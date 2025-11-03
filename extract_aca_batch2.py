#!/usr/bin/env python3
"""
Extract ACA emails batch 2 (emails 16-30)
Search for emails from danielberman.ushealth@gmail.com with subject containing "ACA"
Exclude label:dead, after 2025/06/01
"""

import os
import sys
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Token storage path
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

    # If there are no (valid) credentials available, exit
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
            # Save the refreshed credentials
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        else:
            print("ERROR: No valid credentials found. Please run the MCP server first to authenticate.")
            sys.exit(1)

    service = build('gmail', 'v1', credentials=creds)
    return service

def extract_body(payload):
    """Extract body from email payload - handles nested parts"""
    body = ''

    def decode_part(part_data):
        """Decode base64 data"""
        if part_data:
            try:
                return base64.urlsafe_b64decode(part_data).decode('utf-8', errors='ignore')
            except:
                return ''
        return ''

    def extract_from_parts(parts):
        """Recursively extract text from parts"""
        text = ''
        html = ''

        for part in parts:
            mime_type = part.get('mimeType', '')

            # Handle nested parts (multipart/alternative, multipart/mixed, etc.)
            if 'parts' in part:
                nested_text, nested_html = extract_from_parts(part['parts'])
                if nested_text and not text:
                    text = nested_text
                if nested_html and not html:
                    html = nested_html

            # Extract text/plain
            elif mime_type == 'text/plain':
                if 'data' in part.get('body', {}):
                    text = decode_part(part['body']['data'])

            # Extract text/html
            elif mime_type == 'text/html':
                if 'data' in part.get('body', {}):
                    html = decode_part(part['body']['data'])

        return text, html

    # Handle multipart messages
    if 'parts' in payload:
        text_body, html_body = extract_from_parts(payload['parts'])
        # Prefer plain text, fall back to HTML
        body = text_body if text_body else html_body

    # Handle simple messages
    elif payload.get('body', {}).get('data'):
        body = decode_part(payload['body']['data'])

    return body

def proper_case(name):
    """Convert name to proper case"""
    if not name:
        return ""
    # Handle all caps names
    if name.isupper():
        return name.title()
    return name

def extract_email_data(body, headers, internal_date):
    """Extract structured data from email body"""
    data = {
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
        "Date Received": "",
        "Notes": ""
    }

    # Convert internal date to readable format
    if internal_date:
        timestamp_ms = int(internal_date)
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
        data["Date Received"] = dt.strftime("%Y-%m-%d %H:%M:%S")

    # Try to extract name from subject line (fallback for reply emails)
    subject = headers.get('Subject', '')
    subject_name = ''
    if subject:
        # Remove "Re: " prefix if present
        clean_subject = re.sub(r'^Re:\s*', '', subject, flags=re.IGNORECASE)
        # Remove " ACA" suffix and anything after it
        clean_subject = re.sub(r'\s*ACA.*$', '', clean_subject, flags=re.IGNORECASE)
        subject_name = proper_case(clean_subject.strip())

    # Split body into lines for easier parsing
    lines = body.split('\n')

    # Extract Name - usually in all caps on its own line before policy number
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for all caps name (2-3 words)
        if re.match(r'^[A-Z][A-Z\s]+[A-Z]$', line) and len(line.split()) >= 2 and len(line.split()) <= 4:
            # Check if next line might be policy number
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^[A-Z0-9]+$', next_line) or 'Monthly Premium' in next_line:
                    data["Name"] = proper_case(line)
                    break

    # If no name found in body, use subject name
    if not data["Name"] and subject_name:
        data["Name"] = subject_name

    # Policy Number - alphanumeric line after name
    for i, line in enumerate(lines):
        line = line.strip()
        if data["Name"] and i > 0:
            prev_line = lines[i-1].strip()
            if proper_case(prev_line) == data["Name"]:
                # This line should be policy number
                if re.match(r'^[A-Z0-9]+$', line):
                    data["Policy Number"] = line
                    break

    # Monthly Premium
    match = re.search(r'Monthly Premium:\s*\$?([\d,]+\.?\d*)', body)
    if match:
        data["Monthly Premium"] = f"${match.group(1)}"

    # Application Date - format: "Application: MM/DD/YYYY"
    match = re.search(r'Application:\s*(\d{2}/\d{2}/\d{4})', body)
    if match:
        data["Application Date"] = match.group(1)

    # Paid to Date
    match = re.search(r'Paid to Date:\s*([^\n]+)', body)
    if match:
        data["Paid to Date"] = match.group(1).strip()

    # Look for "Primary Information" section
    primary_section = False
    for i, line in enumerate(lines):
        line = line.strip()

        if 'Primary Information' in line:
            primary_section = True
            continue

        if primary_section and i < len(lines) - 1:
            # Gender is usually right after "Primary Information"
            if line in ['Male', 'Female'] and not data["Gender"]:
                data["Gender"] = line

            # DOB with age - format: "MM/DD/YYYY (age)"
            dob_match = re.match(r'(\d{2}/\d{2}/\d{4})\s*\((\d+)\)', line)
            if dob_match and not data["DOB"]:
                data["DOB"] = dob_match.group(1)
                data["Age"] = dob_match.group(2)

            # Phone number - format: (XXX) XXX-XXXX
            phone_match = re.match(r'\((\d{3})\)\s*(\d{3})-(\d{4})', line)
            if phone_match and not data["Phone"]:
                data["Phone"] = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"

            # Email address
            if '@' in line and '.' in line and not data["Email"]:
                email = line.strip()
                # Clean up email: remove ">" prefixes from reply quotes
                email = re.sub(r'^[>\s]+', '', email).strip()
                if 'danielberman' not in email.lower() and 'cjsinsurancesolutions' not in email.lower():
                    data["Email"] = email

            # Address - numeric start with street name
            if re.match(r'\d+\s+[A-Z]', line) and not data["Address"]:
                address_parts = [line]
                # Get next line for city, state, zip
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.search(r'[A-Z]{2}\s+\d{5}', next_line):
                        address_parts.append(next_line)
                data["Address"] = ', '.join(address_parts)

            # Stop at "Dependents" section
            if 'Dependents' in line or 'Dependent' in line:
                primary_section = False

    # SSN pattern anywhere in body
    ssn_match = re.search(r'SSN[:\s]+(\d{3}[-\s]?\d{2}[-\s]?\d{4})', body)
    if ssn_match:
        data["SSN"] = ssn_match.group(1)

    # Fallback: search entire body for phone if not found
    if not data["Phone"]:
        phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', body)
        if phone_match:
            data["Phone"] = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"

    # Fallback: search entire body for email if not found
    if not data["Email"]:
        # Look for email patterns
        email_match = re.search(r'\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b', body, re.IGNORECASE)
        if email_match:
            email = email_match.group(1)
            if 'danielberman' not in email.lower() and 'cjsinsurancesolutions' not in email.lower():
                data["Email"] = email

    return data

def main():
    print("Authenticating with Gmail API...")
    service = authenticate()

    # Search query
    query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'
    print(f"Search query: {query}")

    try:
        # Get all matching emails (we need to get more than 15 to skip to 16-30)
        print("\nSearching for emails...")
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=30  # Get first 30 emails
        ).execute()

        messages = results.get('messages', [])
        total_found = len(messages)
        print(f"Found {total_found} emails total")

        if total_found < 16:
            print(f"ERROR: Only {total_found} emails found. Need at least 16 to skip first 15.")
            sys.exit(1)

        # Skip first 15, process 16-30 (indices 15-29)
        messages_to_process = messages[15:30]  # This gets emails 16-30
        print(f"Processing emails 16-30 ({len(messages_to_process)} emails)...")

        extracted_data = []

        for idx, msg in enumerate(messages_to_process, start=16):
            print(f"\nProcessing email {idx}/{min(30, total_found)}...")

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

            # Get internal date
            internal_date = msg_data.get('internalDate', '')

            print(f"  Subject: {headers.get('Subject', 'N/A')[:60]}...")
            print(f"  From: {headers.get('From', 'N/A')}")
            print(f"  Body length: {len(body)} chars")

            # Extract structured data
            data = extract_email_data(body, headers, internal_date)

            # Add email subject to notes if needed
            if headers.get('Subject'):
                data['Notes'] = f"Subject: {headers.get('Subject')}"

            extracted_data.append(data)

            print(f"  Extracted - Name: {data['Name']}, Policy: {data['Policy Number']}")

        # Save to JSON file
        output_file = SCRIPT_DIR / 'aca_batch_2.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"SUCCESS! Processed {len(extracted_data)} emails")
        print(f"Data saved to: {output_file}")
        print(f"{'='*60}")

        # Print summary
        print("\nSummary of extracted data:")
        for idx, data in enumerate(extracted_data, start=16):
            print(f"\nEmail {idx}:")
            print(f"  Name: {data['Name']}")
            print(f"  Policy: {data['Policy Number']}")
            print(f"  Phone: {data['Phone']}")
            print(f"  Email: {data['Email']}")
            print(f"  Premium: {data['Monthly Premium']}")

    except HttpError as error:
        print(f"An error occurred: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
