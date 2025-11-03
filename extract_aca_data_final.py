#!/usr/bin/env python3
"""
Final version: Search and extract ACA email details with improved parsing
"""

import os
import sys
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from html import unescape

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
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

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

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

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            print(f"[OK] Credentials saved to {TOKEN_PATH}", file=sys.stderr)

    service = build('gmail', 'v1', credentials=creds)
    return service


def extract_body(payload):
    """Extract body from email payload - both text and HTML"""
    text_body = ''
    html_body = ''

    def extract_parts(parts):
        nonlocal text_body, html_body
        for part in parts:
            mime_type = part.get('mimeType', '')

            if mime_type == 'text/plain':
                if 'data' in part.get('body', {}):
                    data = part['body']['data']
                    text_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            elif mime_type == 'text/html':
                if 'data' in part.get('body', {}):
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            elif 'parts' in part:
                extract_parts(part['parts'])

    if 'parts' in payload:
        extract_parts(payload['parts'])
    elif payload.get('body', {}).get('data'):
        # Single part message
        data = payload['body']['data']
        mime_type = payload.get('mimeType', 'text/plain')
        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        if 'text/html' in mime_type:
            html_body = decoded
        else:
            text_body = decoded

    # Return text body if available, otherwise convert HTML to text
    if text_body:
        return text_body
    elif html_body:
        # Basic HTML to text conversion
        text = re.sub(r'<br\s*/?>', '\n', html_body, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)  # Remove all HTML tags
        text = unescape(text)  # Convert HTML entities
        return text
    else:
        return ''


def proper_case_name(name: str) -> str:
    """Convert name to proper case"""
    if not name:
        return ''

    name = name.strip()
    words = name.split()
    proper_words = []

    for word in words:
        if "'" in word:
            parts = word.split("'")
            proper_words.append("'".join([p.capitalize() for p in parts]))
        elif word.lower().startswith('mc') and len(word) > 2:
            proper_words.append('Mc' + word[2:].capitalize())
        else:
            proper_words.append(word.capitalize())

    return ' '.join(proper_words)


def clean_paid_to_date(paid_to: str) -> str:
    """Clean up paid to date field - remove HTML fragments"""
    if not paid_to:
        return ''

    # If it contains HTML tags, extract just the date portion
    if '<' in paid_to or '>' in paid_to:
        # Try to extract a date pattern
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', paid_to)
        if date_match:
            return date_match.group(1)
        # Check for "Pending"
        if 'Pending' in paid_to or 'pending' in paid_to.lower():
            return 'Pending'
        return ''

    return paid_to.strip()


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

    # Extract name - look for all caps name before policy number
    name = ''
    name_match = re.search(r'(?:>>|>)?\s*([A-Z][A-Z\s]+[A-Z])\s*\n\s*(?:>>|>)?\s*([A-Z0-9]{8,})\s*\n\s*(?:>>|>)?\s*Monthly Premium:', body)
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
        paid_to_date = clean_paid_to_date(paid_match.group(1))

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

    # Email - look for email addresses, prioritize client emails (not danielberman or chris)
    email = ''
    email_matches = re.findall(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', body, re.IGNORECASE)
    for em in email_matches:
        em_lower = em.lower()
        if 'danielberman' not in em_lower and 'chris@' not in em_lower and 'ushealth' not in em_lower:
            email = em_lower
            break

    # If no client email found, use the first one that's not a sender
    if not email and email_matches:
        for em in email_matches:
            em_lower = em.lower()
            if 'danielberman' not in em_lower:
                email = em_lower
                break

    # Address - two lines (street + city/state/zip)
    address = ''
    address_match = re.search(r'([0-9]+\s+[A-Z\s]+(?:ST|AVE|RD|DR|BLVD|LN|CT|WAY|PL|WALK)[^\n]*)\s*\n\s*(?:>>|>)?\s*([A-Z\s]+,\s*[A-Z]{2}\s+\d{5})', body, re.IGNORECASE)
    if address_match:
        address = f"{address_match.group(1).strip()}, {address_match.group(2).strip()}"

    # SSN
    ssn = ''
    ssn_match = re.search(r'SSN[:\s]+([0-9-]+)', body, re.IGNORECASE)
    if ssn_match:
        ssn = ssn_match.group(1).strip()

    # Alternative SSN format: "social ——> XXXXXXXXX"
    if not ssn:
        ssn_match = re.search(r'social\s+[—\-]+>\s*([0-9]+)', body, re.IGNORECASE)
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

    query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'

    print(f"Searching for emails with query: {query}", file=sys.stderr)

    try:
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

        client_data = []

        for i, msg in enumerate(messages, 1):
            print(f"Processing email {i}/{len(messages)} (ID: {msg['id']})", file=sys.stderr)

            try:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = {h['name']: h['value']
                          for h in msg_data['payload'].get('headers', [])}

                body = extract_body(msg_data['payload'])

                if not body:
                    print(f"  Warning: No body content found for email {msg['id']}", file=sys.stderr)
                    continue

                internal_date = msg_data.get('internalDate', '')
                client_info = extract_client_data(body, headers, internal_date)

                # Only include emails that have at least a name or policy number
                if client_info['Name'] or client_info['Policy Number']:
                    client_data.append(client_info)
                    print(f"  Extracted: {client_info.get('Name', 'N/A')} - Policy: {client_info.get('Policy Number', 'N/A')}", file=sys.stderr)
                else:
                    print(f"  Skipped: No client data found in this email", file=sys.stderr)

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
    print("Gmail ACA Email Extractor - Final Version", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Authenticate
    print("Authenticating with Gmail...", file=sys.stderr)
    service = authenticate()
    print("Authentication successful!", file=sys.stderr)
    print()

    # Search and extract
    client_data = search_and_extract(service, max_results=15)

    # Save to file
    output_file = SCRIPT_DIR / 'aca_client_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(client_data, f, indent=2)

    print(f"\nData saved to: {output_file}", file=sys.stderr)

    # Output as JSON to stdout
    print(json.dumps(client_data, indent=2))


if __name__ == "__main__":
    main()
