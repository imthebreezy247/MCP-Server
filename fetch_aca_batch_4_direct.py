#!/usr/bin/env python3
"""
Fetch ACA emails batch 4 (emails 46-60) - Direct Gmail API access
Extract client information from Gmail emails
"""

import json
import re
import base64
from datetime import datetime
from pathlib import Path
import sys
import os

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Token storage path
TOKEN_PATH = SCRIPT_DIR / 'token.json'
CREDENTIALS_PATH = SCRIPT_DIR / 'credentials.json'


def proper_case_name(name):
    """Convert name to proper case"""
    if not name:
        return ""
    words = name.split()
    return ' '.join(word.capitalize() for word in words)


def extract_body(payload):
    """Extract email body from message payload"""
    body = ''

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html':
                if 'data' in part['body']:
                    body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                # Recursively extract from nested parts
                body += extract_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    return body


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
    subject_name_match = re.search(r'^([A-Za-z\s]+?)\s+ACA', subject, re.IGNORECASE)
    if subject_name_match:
        name = subject_name_match.group(1).strip()
        client_info["Name"] = proper_case_name(name)

    # Extract Policy Number
    policy_match = re.search(r'52Z\d{7}', content)
    if policy_match:
        client_info["Policy Number"] = policy_match.group(0)

    # Extract Phone
    phone_patterns = [
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*(\d{10})',
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*(\d{3})[-.\s](\d{3})[-.\s](\d{4})',
        r'(?:Phone|Tel|Mobile|Cell|Ph)[:\s]*\((\d{3})\)\s*(\d{3})[-.\s](\d{4})',
        r'\b(\d{10})\b',
    ]

    for pattern in phone_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            phone_digits = re.sub(r'\D', '', match.group(0))
            if len(phone_digits) == 10:
                client_info["Phone"] = phone_digits
                break
        if client_info["Phone"]:
            break

    # Extract Email address
    email_matches = re.findall(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', content)
    for email_addr in email_matches:
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
            if '.' not in premium:
                premium = premium + '.00'
            client_info["Monthly Premium"] = f"${premium}"
            break

    # Extract Application Date
    app_date_patterns = [
        r'(?:Application\s+Date|App\s+Date|Applied)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
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

    # Extract Date of Birth
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

    # Extract Address
    address_patterns = [
        r'(\d+\s+[NSEW]?\s*[A-Z][A-Za-z\s.]+(?:Street|St|Ave|Avenue|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl|STREET|ST|AVE|AVENUE|ROAD|RD|DRIVE|DR|LANE|LN|BOULEVARD|BLVD|WAY|COURT|CT|CIRCLE|CIR|PLACE|PL)\.?\s*,\s*[A-Z][A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5})',
        r'(?:Address|Residence)[:\s]*([^\n]+,\s*[A-Z]{2}\s+\d{5})',
    ]

    for pattern in address_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            address = re.sub(r'\s+', ' ', address)
            client_info["Address"] = address.upper()
            break

    # Extract SSN
    ssn_match = re.search(r'(?:SSN|Social\s+Security)[:\s]*(\d{3}-\d{2}-\d{4})', content, re.IGNORECASE)
    if ssn_match:
        client_info["SSN"] = ssn_match.group(1)

    return client_info


def authenticate():
    """Authenticate with Gmail API"""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_PATH}. Please download OAuth credentials from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def main():
    """Main function to fetch and process emails"""

    print("=" * 70)
    print("Fetching ACA emails batch 4 (emails 46-60)")
    print("=" * 70)

    # Authenticate
    print("\nAuthenticating...")
    try:
        service = authenticate()
        print("[OK] Authentication successful")
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return

    # Search for emails
    print("\nSearching for emails...")
    query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'
    print(f"Query: {query}")

    try:
        # Get first 60 emails
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=60
        ).execute()

        messages = results.get('messages', [])
        total_emails = len(messages)

        print(f"[OK] Found {total_emails} emails total")

        if total_emails < 46:
            print(f"[ERROR] Not enough emails. Only {total_emails} found, need at least 46.")
            return

        # Get emails 46-60 (index 45-59 in zero-based)
        emails_to_process = messages[45:60]
        actual_count = len(emails_to_process)
        print(f"[OK] Processing emails 46-{45+actual_count} ({actual_count} emails)\n")

        # Process each email
        all_client_data = []

        for idx, msg in enumerate(emails_to_process, start=46):
            print(f"Processing email {idx}...")

            # Get full email content
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}

            # Extract body
            body = extract_body(msg_data['payload'])

            email_data = {
                'id': msg['id'],
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': msg_data.get('snippet', ''),
                'body': body
            }

            print(f"  Subject: {email_data['subject'][:60]}")
            print(f"  Date: {email_data['date']}")

            # Extract client information
            client_info = extract_client_info(email_data)
            all_client_data.append(client_info)

            print(f"  [OK] {client_info['Name']} | {client_info['Policy Number']} | {client_info['Phone']}")

        # Save to JSON file
        output_file = SCRIPT_DIR / 'aca_batch_4.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_client_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print(f"[OK] Processing complete!")
        print(f"[OK] Processed {len(all_client_data)} emails")
        print(f"[OK] Data saved to: {output_file.absolute()}")
        print("\nFirst record sample:")
        print(json.dumps(all_client_data[0], indent=2))

    except HttpError as error:
        print(f"[ERROR] Gmail API error: {error}")
    except Exception as e:
        print(f"[ERROR] Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Fatal error: {e}")
        sys.exit(1)
