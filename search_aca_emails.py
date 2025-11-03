#!/usr/bin/env python3
"""
Search and extract ACA email details
"""

import os
import sys
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
TOKEN_PATH = SCRIPT_DIR / 'token.json'
CREDENTIALS_PATH = SCRIPT_DIR / 'credentials.json'


def authenticate():
    """Authenticate with Gmail API"""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...", file=sys.stderr)
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_PATH}. Please download OAuth credentials from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Authentication failed: {e}", file=sys.stderr)
                sys.exit(1)

        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            print(f"[OK] Credentials saved to {TOKEN_PATH}", file=sys.stderr)

    service = build('gmail', 'v1', credentials=creds)
    return service


def extract_body(payload):
    """Extract body from email payload"""
    body = ''

    if 'parts' in payload:
        for part in payload['parts']:
            # Try to get text/plain first
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            # Handle nested parts (multipart)
            elif 'parts' in part:
                body = extract_body(part)
                if body:
                    break
    elif payload['body'].get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    return body


def extract_field(text: str, patterns: List[str], default: str = '') -> str:
    """Extract field using multiple regex patterns"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            # Clean up any extra whitespace or newlines
            value = ' '.join(value.split())
            return value
    return default


def proper_case_name(name: str) -> str:
    """Convert name to proper case"""
    if not name:
        return ''

    # Handle common patterns
    name = name.strip()

    # Split by spaces and capitalize each word
    words = name.split()
    proper_words = []

    for word in words:
        # Handle special cases like O'Brien, McDonald
        if "'" in word:
            parts = word.split("'")
            proper_words.append("'".join([p.capitalize() for p in parts]))
        elif word.lower().startswith('mc') and len(word) > 2:
            proper_words.append('Mc' + word[2:].capitalize())
        else:
            proper_words.append(word.capitalize())

    return ' '.join(proper_words)


def extract_client_data(body: str, headers: dict, internal_date: str) -> Dict[str, Any]:
    """Extract client data from email body"""

    # Convert internal date to readable format
    date_received = ''
    if internal_date:
        try:
            timestamp = int(internal_date) / 1000
            date_received = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except:
            date_received = internal_date

    # The format appears to be:
    # NAME (all caps on one line)
    # Policy number (next line)
    # Monthly Premium: $XXX.XX
    # Application: MM/DD/YYYY
    # Paid to Date: MM/DD/YYYY
    # Primary Information
    # Gender
    # DOB (Age)
    # Phone
    # Email (all caps)
    # Address line 1
    # Address line 2

    # Extract name - look for all caps name before policy number
    name = ''
    name_match = re.search(r'(?:>>|>)?\s*([A-Z][A-Z\s]+[A-Z])\s*\n\s*(?:>>|>)?\s*([A-Z0-9]+)\s*\n\s*(?:>>|>)?\s*Monthly Premium:', body)
    if name_match:
        name = proper_case_name(name_match.group(1).strip())

    # Policy number - follows the name
    policy_number = ''
    policy_match = re.search(r'(?:>>|>)?\s*([A-Z0-9]{8,})\s*\n\s*(?:>>|>)?\s*Monthly Premium:', body)
    if policy_match:
        policy_number = policy_match.group(1).strip()

    # Monthly Premium
    monthly_premium = ''
    premium_match = re.search(r'Monthly Premium:\s*\$?([0-9,.]+)', body, re.IGNORECASE)
    if premium_match:
        monthly_premium = premium_match.group(1).strip()

    # Application Date
    app_date = ''
    app_match = re.search(r'Application:\s*(\d{1,2}/\d{1,2}/\d{4})', body, re.IGNORECASE)
    if app_match:
        app_date = app_match.group(1).strip()

    # Paid to Date
    paid_to_date = ''
    paid_match = re.search(r'Paid to Date:\s*([^\n]+)', body, re.IGNORECASE)
    if paid_match:
        paid_to_date = paid_match.group(1).strip()

    # Gender - look for Male/Female after "Primary Information"
    gender = ''
    gender_match = re.search(r'Primary Information\s*\n\s*(?:>>|>)?\s*(Male|Female)', body, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).strip()

    # DOB and Age - format: MM/DD/YYYY (Age)
    dob = ''
    age = ''
    dob_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s*\((\d+)\)', body)
    if dob_match:
        dob = dob_match.group(1).strip()
        age = dob_match.group(2).strip()

    # Phone - format: (XXX) XXX-XXXX
    phone = ''
    phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', body)
    if phone_match:
        phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

    # Email - all caps email address
    email = ''
    email_match = re.search(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', body, re.IGNORECASE)
    if email_match:
        email = email_match.group(1).strip().lower()

    # Address - two lines after email
    address = ''
    # Look for street address pattern (numbers followed by street name)
    address_match = re.search(r'([0-9]+\s+[A-Z\s]+(?:ST|AVE|RD|DR|BLVD|LN|CT|WAY|PL)[^\n]*)\s*\n\s*(?:>>|>)?\s*([A-Z\s]+,\s*[A-Z]{2}\s+\d{5})', body, re.IGNORECASE)
    if address_match:
        address = f"{address_match.group(1).strip()}, {address_match.group(2).strip()}"

    # SSN - not typically in these emails, but check
    ssn = ''
    ssn_match = re.search(r'SSN[:\s]+([0-9-]+)', body, re.IGNORECASE)
    if ssn_match:
        ssn = ssn_match.group(1).strip()

    return {
        'Name': name,
        'Policy Number': policy_number,
        'Phone': phone,
        'Email': email,
        'Monthly Premium': monthly_premium,
        'Application Date': app_date,
        'Paid to Date': paid_to_date,
        'Gender': gender,
        'DOB': dob,
        'Age': age,
        'Address': address,
        'SSN': ssn,
        'Date Received': date_received,
        'Notes': ''
    }


def search_and_extract(service, max_results=15):
    """Search for emails and extract client data"""

    # Search query
    query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'

    print(f"Searching for emails with query: {query}", file=sys.stderr)

    try:
        # Search for emails
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results,
            includeSpamTrash=False
        ).execute()

        messages = results.get('messages', [])
        print(f"Found {len(messages)} emails", file=sys.stderr)

        if not messages:
            print("No emails found matching the criteria", file=sys.stderr)
            return []

        # Extract data from each email
        client_data = []

        for i, msg in enumerate(messages, 1):
            print(f"Processing email {i}/{len(messages)} (ID: {msg['id']})", file=sys.stderr)

            try:
                # Get full message content
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                # Extract headers
                headers = {h['name']: h['value']
                          for h in msg_data['payload'].get('headers', [])}

                # Extract body
                body = extract_body(msg_data['payload'])

                if not body:
                    print(f"  Warning: No body content found for email {msg['id']}", file=sys.stderr)
                    continue

                # Extract client data
                internal_date = msg_data.get('internalDate', '')
                client_info = extract_client_data(body, headers, internal_date)

                # Add message ID for reference
                client_info['Message ID'] = msg['id']

                client_data.append(client_info)

                print(f"  Extracted: {client_info.get('Name', 'N/A')}", file=sys.stderr)

            except HttpError as e:
                print(f"  Error processing email {msg['id']}: {e}", file=sys.stderr)
                continue

        print(f"\nSuccessfully extracted data from {len(client_data)} emails", file=sys.stderr)
        return client_data

    except HttpError as e:
        print(f"Error searching emails: {e}", file=sys.stderr)
        return []


def main():
    """Main function"""
    print("Gmail ACA Email Extractor", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Authenticate
    print("Authenticating with Gmail...", file=sys.stderr)
    service = authenticate()
    print("Authentication successful!", file=sys.stderr)
    print()

    # Search and extract
    client_data = search_and_extract(service, max_results=15)

    # Output as JSON
    print(json.dumps(client_data, indent=2))


if __name__ == "__main__":
    main()
