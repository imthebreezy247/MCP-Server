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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_mcp_server import GmailMCPServer


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

    # Extract Name (look for patterns like "FIRST LAST" or "First Last")
    name_patterns = [
        r'(?:Name|MEMBER|Member|CLIENT|Client)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'^([A-Z][A-Z\s]+)(?:\s+ACA|\s+52Z)',  # All caps name at start
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+ACA',  # Name before ACA
    ]

    for pattern in name_patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Convert to proper case
            client_info["Name"] = ' '.join(word.capitalize() for word in name.split())
            break

    # If no name found, try extracting from subject
    if not client_info["Name"]:
        subject_match = re.search(r'([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)(?:\s+ACA)?', subject)
        if subject_match:
            name = subject_match.group(1).strip()
            client_info["Name"] = ' '.join(word.capitalize() for word in name.split())

    # Extract Policy Number (format: 52Z followed by digits)
    policy_match = re.search(r'(52Z\d{7})', content)
    if policy_match:
        client_info["Policy Number"] = policy_match.group(1)

    # Extract Phone (10 digits, various formats)
    phone_patterns = [
        r'(?:Phone|Tel|Mobile|Cell)[:\s]*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
        r'(?:Phone|Tel|Mobile|Cell)[:\s]*\((\d{3})\)\s*(\d{3})[-.\s]?(\d{4})',
        r'\b(\d{10})\b',  # 10 digits together
        r'\((\d{3})\)\s*(\d{3})-(\d{4})',
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, content)
        if match:
            # Extract all digits
            phone_digits = ''.join(re.findall(r'\d', match.group(0)))
            if len(phone_digits) == 10:
                client_info["Phone"] = phone_digits
                break

    # Extract Email address
    email_match = re.search(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', content)
    if email_match:
        email_addr = email_match.group(1)
        # Exclude the sender's email
        if 'danielberman' not in email_addr.lower():
            client_info["Email"] = email_addr

    # Extract Monthly Premium
    premium_patterns = [
        r'(?:Monthly Premium|Premium|Monthly Payment)[:\s]*\$?([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.\d{2})\s*(?:/month|monthly|per month)',
    ]

    for pattern in premium_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            premium = match.group(1).replace(',', '')
            client_info["Monthly Premium"] = f"${premium}"
            break

    # Extract Application Date
    app_date_patterns = [
        r'(?:Application Date|App Date|Date of Application)[:\s]*(\\d{1,2}/\\d{1,2}/\\d{4})',
        r'(?:Applied|Application)[:\s]*(\\d{1,2}/\\d{1,2}/\\d{2,4})',
    ]

    for pattern in app_date_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["Application Date"] = match.group(1)
            break

    # Extract Paid to Date
    paid_patterns = [
        r'(?:Paid to Date|Paid Through|Paid Until)[:\s]*(\\d{1,2}/\\d{1,2}/\\d{4})',
    ]

    for pattern in paid_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["Paid to Date"] = match.group(1)
            break

    # Extract Gender
    gender_match = re.search(r'(?:Gender|Sex)[:\s]*(Male|Female|M|F)', content, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).upper()
        if gender in ['M', 'MALE']:
            client_info["Gender"] = "Male"
        elif gender in ['F', 'FEMALE']:
            client_info["Gender"] = "Female"

    # Extract Date of Birth
    dob_patterns = [
        r'(?:DOB|Date of Birth|Birth Date)[:\s]*(\\d{1,2}/\\d{1,2}/\\d{4})',
        r'(?:Born|Birthday)[:\s]*(\\d{1,2}/\\d{1,2}/\\d{2,4})',
    ]

    for pattern in dob_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["DOB"] = match.group(1)
            break

    # Extract Age
    age_match = re.search(r'(?:Age)[:\s]*(\d{1,3})', content, re.IGNORECASE)
    if age_match:
        client_info["Age"] = age_match.group(1)

    # Extract Address
    address_patterns = [
        r'(?:Address|Residence)[:\s]*([^\\n]+(?:Street|St|Ave|Avenue|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct)[^\\n]*,\s*[A-Z]{2}\s+\d{5})',
        r'(\d+\s+[A-Z\s]+(?:Street|St|Ave|Avenue|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|STREET|ST|AVE|AVENUE|ROAD|RD|DRIVE|DR|LANE|LN|BOULEVARD|BLVD|WAY|COURT|CT)[^\\n]*,\s*[A-Z]{2}\s+\d{5})',
    ]

    for pattern in address_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            client_info["Address"] = match.group(1).strip()
            break

    # Extract SSN if present
    ssn_match = re.search(r'(?:SSN|Social Security)[:\s]*(\\d{3}-\\d{2}-\\d{4})', content, re.IGNORECASE)
    if ssn_match:
        client_info["SSN"] = ssn_match.group(1)

    return client_info


async def main():
    """Main function to fetch and process emails"""

    print("Fetching ACA emails batch 4 (emails 46-60)...")
    print("=" * 60)

    # Initialize server
    server = GmailMCPServer()

    # Authenticate
    try:
        server.authenticate()
        print("Authentication successful")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Search for emails
    print("\nSearching for emails...")
    search_result = await server.search_emails(
        query='from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01',
        max_results=60  # Get first 60 emails
    )

    if not search_result['success']:
        print(f"Search failed: {search_result.get('error', 'Unknown error')}")
        return

    total_emails = search_result['count']
    print(f"Found {total_emails} emails total")

    if total_emails < 46:
        print(f"Not enough emails. Only {total_emails} found, need at least 46.")
        return

    # Get emails 46-60 (index 45-59 in zero-based)
    emails_to_process = search_result['emails'][45:60]
    print(f"\nProcessing emails 46-60 ({len(emails_to_process)} emails)...")

    # Process each email
    all_client_data = []

    for idx, email in enumerate(emails_to_process, start=46):
        print(f"\nProcessing email {idx}/{60}...")
        print(f"  Subject: {email['subject']}")
        print(f"  Date: {email['date']}")

        # Get full email content
        email_id = email['id']
        full_email = await server.get_email(email_id)

        if full_email['success']:
            # Extract client information
            client_info = extract_client_info(full_email)
            all_client_data.append(client_info)

            print(f"  Extracted: {client_info['Name']} - {client_info['Policy Number']}")
        else:
            print(f"  Failed to get full email content")

    # Save to JSON file
    output_file = Path(__file__).parent / 'aca_batch_4.json'
    with open(output_file, 'w') as f:
        json.dump(all_client_data, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Processed {len(all_client_data)} emails")
    print(f"Data saved to: {output_file.absolute()}")
    print("\nSample of extracted data:")
    if all_client_data:
        print(json.dumps(all_client_data[0], indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
