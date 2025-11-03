#!/usr/bin/env python3
"""
Fetch ACA emails batch 4 (emails 46-60)
Extract client information from Gmail emails
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set the working directory
os.chdir(Path(__file__).parent)

from gmail_mcp_server import GmailMCPServer


def proper_case_name(name):
    """Convert name to proper case"""
    if not name:
        return ""
    # Split and capitalize each word
    words = name.split()
    return ' '.join(word.capitalize() for word in words)


def extract_client_info(email_data):
    """Extract client information from email content"""

    # Get the full body content
    body = email_data.get('body', '')
    snippet = email_data.get('snippet', '')
    subject = email_data.get('subject', '')

    # Combine body and snippet for searching
    content = body + '\n' + snippet

    # Initialize data structure
    client_info = {
        "Name": "",
        "Policy Number": "",
        "Phone": "",
        "Email": "",
        "Monthly Premium": "",
        "Application Date": "",
        "Paid to Date": "",
        "Gender": "",
        "DOB": "",
        "Age": "",
        "Address": "",
        "SSN": "",
        "Date Received": email_data.get('date', ''),
        "Notes": f"Subject: {subject}"
    }

    # Extract Name from subject first (most reliable)
    # Subject format: "FIRST LAST ACA" or "First Last ACA"
    subject_name_match = re.search(r'^([A-Za-z\s]+?)\s+ACA', subject, re.IGNORECASE)
    if subject_name_match:
        name = subject_name_match.group(1).strip()
        client_info["Name"] = proper_case_name(name)

    # If no name from subject, try from content
    if not client_info["Name"]:
        name_patterns = [
            r'(?:Name|Member Name|Client Name)[:\s]+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'^([A-Z][A-Z\s]+)$',  # All caps line
        ]

        for pattern in name_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                client_info["Name"] = proper_case_name(name)
                break

    # Extract Policy Number (format: 52Z followed by 7 digits)
    policy_match = re.search(r'52Z\d{7}', content)
    if policy_match:
        client_info["Policy Number"] = policy_match.group(0)

    # Extract Phone - look for 10-digit phone numbers
    # Remove common separators and find 10 consecutive digits
    phone_patterns = [
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*(\d{10})',
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*(\d{3})[-.\s](\d{3})[-.\s](\d{4})',
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*\((\d{3})\)\s*(\d{3})[-.\s](\d{4})',
        r'\b(\d{10})\b',  # Just 10 digits
    ]

    for pattern in phone_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Extract all digits from the match
            phone_digits = re.sub(r'\D', '', match.group(0))
            if len(phone_digits) == 10:
                client_info["Phone"] = phone_digits
                break
        if client_info["Phone"]:
            break

    # Extract Email address (but not sender's email)
    email_matches = re.findall(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', content)
    for email_addr in email_matches:
        # Skip sender's email and common system emails
        if 'danielberman' not in email_addr.lower() and 'noreply' not in email_addr.lower():
            client_info["Email"] = email_addr
            break

    # Extract Monthly Premium
    premium_patterns = [
        r'(?:Monthly\s+Premium|Premium|Payment)[:\s]*\$\s*([\d,]+\.?\d{0,2})',
        r'\$\s*([\d,]+\.\d{2})\s*(?:/month|monthly|per month|month)',
    ]

    for pattern in premium_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            premium = match.group(1).replace(',', '')
            # Format to include cents if not present
            if '.' not in premium:
                premium = premium + '.00'
            elif len(premium.split('.')[1]) == 1:
                premium = premium + '0'
            client_info["Monthly Premium"] = f"${premium}"
            break

    # Extract Application Date (MM/DD/YYYY format)
    app_date_patterns = [
        r'(?:Application\s+Date|App\s+Date|Applied)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
        r'(?:Date\s+of\s+Application)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
    ]

    for pattern in app_date_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["Application Date"] = match.group(1)
            break

    # Extract Paid to Date
    paid_patterns = [
        r'(?:Paid\s+to\s+Date|Paid\s+Through|Paid\s+Until)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
    ]

    for pattern in paid_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["Paid to Date"] = match.group(1)
            break

    # Extract Gender
    gender_match = re.search(r'(?:Gender|Sex)[:\s]*(Male|Female|M|F)\b', content, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).upper()
        if gender in ['M', 'MALE']:
            client_info["Gender"] = "Male"
        elif gender in ['F', 'FEMALE']:
            client_info["Gender"] = "Female"

    # Extract Date of Birth (MM/DD/YYYY format)
    dob_patterns = [
        r'(?:DOB|Date\s+of\s+Birth|Birth\s+Date|Born)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
    ]

    for pattern in dob_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["DOB"] = match.group(1)
            break

    # Extract Age
    age_match = re.search(r'(?:Age)[:\s]*(\d{1,3})\b', content, re.IGNORECASE)
    if age_match:
        client_info["Age"] = age_match.group(1)

    # Extract Address - look for street address with city, state, zip
    address_patterns = [
        r'(\d+\s+[NSEW]?\s*[A-Z][A-Za-z\s.]+(?:Street|St|Ave|Avenue|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl|STREET|ST|AVE|AVENUE|ROAD|RD|DRIVE|DR|LANE|LN|BOULEVARD|BLVD|WAY|COURT|CT|CIRCLE|CIR|PLACE|PL)\.?\s*,\s*[A-Z][A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5})',
        r'(?:Address|Residence)[:\s]*([^\n]+,\s*[A-Z]{2}\s+\d{5})',
    ]

    for pattern in address_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            # Clean up the address
            address = re.sub(r'\s+', ' ', address)
            client_info["Address"] = address.upper()
            break

    # Extract SSN if present
    ssn_match = re.search(r'(?:SSN|Social\s+Security)[:\s]*(\d{3}-\d{2}-\d{4})', content, re.IGNORECASE)
    if ssn_match:
        client_info["SSN"] = ssn_match.group(1)

    return client_info


async def main():
    """Main function to fetch and process emails"""

    print("=" * 70)
    print("Fetching ACA emails batch 4 (emails 46-60)")
    print("=" * 70)

    # Initialize server
    server = GmailMCPServer()

    # Authenticate
    print("\nAuthenticating...")
    try:
        server.authenticate()
        print("[OK] Authentication successful")
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return

    # Search for emails using the server's tool
    print("\nSearching for emails...")
    print("Query: from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01")

    try:
        # Call the search_emails tool directly
        search_result = await server.mcp.tools[2]._func(
            query='from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01',
            max_results=60  # Get first 60 emails
        )

        if not search_result['success']:
            print(f"[ERROR] Search failed: {search_result.get('error', 'Unknown error')}")
            return

        total_emails = search_result['count']
        print(f"[OK] Found {total_emails} emails total")

        if total_emails < 46:
            print(f"[ERROR] Not enough emails. Only {total_emails} found, need at least 46.")
            return

        # Get emails 46-60 (index 45-59 in zero-based)
        emails_to_process = search_result['emails'][45:60]
        actual_count = len(emails_to_process)
        print(f"[OK] Processing emails 46-{45+actual_count} ({actual_count} emails)\n")

        # Process each email
        all_client_data = []

        for idx, email in enumerate(emails_to_process, start=46):
            print(f"Processing email {idx}...")
            print(f"  Subject: {email['subject'][:60]}")
            print(f"  Date: {email['date']}")

            # Get full email content using get_email tool
            email_id = email['id']

            # Call the get_email tool directly
            full_email = await server.mcp.tools[3]._func(message_id=email_id)

            if full_email['success']:
                # Extract client information
                client_info = extract_client_info(full_email)
                all_client_data.append(client_info)

                print(f"  [OK] {client_info['Name']} | {client_info['Policy Number']} | {client_info['Phone']}")
            else:
                print(f"  [ERROR] Failed to get full email content")
                # Add empty record
                all_client_data.append({
                    "Name": "",
                    "Policy Number": "",
                    "Phone": "",
                    "Email": "",
                    "Monthly Premium": "",
                    "Application Date": "",
                    "Paid to Date": "",
                    "Gender": "",
                    "DOB": "",
                    "Age": "",
                    "Address": "",
                    "SSN": "",
                    "Date Received": email.get('date', ''),
                    "Notes": f"Subject: {email.get('subject', '')} [FAILED TO FETCH]"
                })

        # Save to JSON file
        output_file = Path(__file__).parent / 'aca_batch_4.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_client_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print(f"[OK] Processing complete!")
        print(f"[OK] Processed {len(all_client_data)} emails")
        print(f"[OK] Data saved to: {output_file.absolute()}")
        print("\nFirst record sample:")
        print(json.dumps(all_client_data[0], indent=2))

    except Exception as e:
        print(f"\n[ERROR] Error during processing: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Fatal error: {e}")
        sys.exit(1)
