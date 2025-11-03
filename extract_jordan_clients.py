#!/usr/bin/env python3
"""
Extract client information from Jordan's ACA Signup emails
This script searches Gmail for emails from jordang.ushealth@gmail.com with subject containing "ACA Signup"
and extracts client information from the search results only (no individual email reading)
"""

import os
import sys
import json
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"Missing {CREDENTIALS_PATH}")

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def extract_phone(text):
    """Extract phone number from text"""
    # Match various phone formats: (555) 555-5555, 555-555-5555, 5555555555, etc.
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10,11}'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            # Clean up phone number
            phone = re.sub(r'[^\d]', '', phone)
            if len(phone) == 10:
                return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
            elif len(phone) == 11 and phone[0] == '1':
                return f"({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
            return phone
    return None

def extract_email(text):
    """Extract email address from text"""
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group(0) if match else None

def extract_premium(text):
    """Extract monthly premium from text"""
    # Match $XX.XX or $XXX.XX
    match = re.search(r'\$\d+(?:\.\d{2})?', text)
    return match.group(0) if match else None

def extract_date(text):
    """Extract application date from text"""
    # Match dates like MM/DD/YYYY or MM-DD-YYYY
    match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)
    return match.group(0) if match else None

def extract_name_from_subject(subject):
    """Extract client name from subject line"""
    # Subject format variations:
    # "ACA Signup - Client Name - other info"
    # "aca signup- Bowdy Floyd, 435-828-6900"
    # "Aca signup Edrice Nelson - (404) 542-0302"

    # Remove "Re:" prefix
    subject = re.sub(r'^Re:\s*', '', subject, flags=re.IGNORECASE)

    # Try to find name after "signup" keyword
    if 'signup' in subject.lower():
        # Pattern 1: "aca signup- Name, Phone"
        match = re.search(r'signup[-\s]+([A-Za-z]+\s+[A-Za-z]+)', subject, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()

        # Pattern 2: "ACA Signup - Name - other"
        parts = subject.split('-')
        if len(parts) >= 2:
            # Skip the "ACA Signup" part
            name = parts[1].strip()
            # Remove any trailing info in parentheses or brackets or phone numbers
            name = re.sub(r'\s*[\(\[].*?[\)\]]', '', name)
            name = re.sub(r'\d{3}[-\s]?\d{3}[-\s]?\d{4}', '', name)
            name = name.strip()
            if len(name) > 0 and not name.isdigit():
                return name.title()
    return None

def extract_name_from_snippet(snippet):
    """Extract client name from email snippet"""
    # Look for common patterns in snippets:
    # "Hi, I have someone needing a signup, Rachel King (337) 831-0012"
    # "Hi, I have someone needing a signup: John Doe, (123) 456-7890"
    # "Name: John Doe"

    # Pattern 1: "needing a signup[,:] Name"
    match = re.search(r'needing (?:an? )?signup[,:]?\s+([A-Z][a-z]+(?:\s+(?:and|&amp;|&)\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)+)', snippet, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # Clean up HTML entities
        name = name.replace('&amp;', '&')
        # Remove trailing numbers
        name = re.sub(r'\s+\d{3,}$', '', name)
        # Remove income information
        name = re.sub(r'\s+\d+[kK]$', '', name)
        return name

    # Pattern 2: "Name: John Doe" or "Client: John Doe"
    match = re.search(r'(?:Name|Client):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', snippet)
    if match:
        return match.group(1).strip()

    # Pattern 3: Name at the beginning before phone/email
    match = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-,]?\s*[\(\d]', snippet)
    if match:
        return match.group(1).strip()

    # Pattern 4: Name before "Phone:" or "Email:"
    match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:Phone|Email|Tel):', snippet, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None

def get_label_name(service, label_id):
    """Get label name from label ID"""
    try:
        label = service.users().labels().get(userId='me', id=label_id).execute()
        return label.get('name', label_id)
    except:
        return label_id

def search_and_extract(service, output_file):
    """Search for emails and extract client information"""

    # First, get all labels
    print("Fetching Gmail labels...")
    labels_result = service.users().labels().list(userId='me').execute()
    all_labels = labels_result.get('labels', [])
    label_map = {label['id']: label['name'] for label in all_labels}
    print(f"Found {len(label_map)} labels")

    # Search query
    query = 'from:jordang.ushealth@gmail.com subject:"ACA Signup" -label:dead'
    print(f"\nSearching with query: {query}")

    # Get all messages (paginate if needed)
    all_messages = []
    page_token = None

    while True:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=500,
            pageToken=page_token
        ).execute()

        messages = results.get('messages', [])
        all_messages.extend(messages)

        page_token = results.get('nextPageToken')
        if not page_token:
            break

        print(f"Fetched {len(all_messages)} messages so far...")

    print(f"\nTotal messages found: {len(all_messages)}")

    if not all_messages:
        print("No messages found!")
        return

    # Extract client information from metadata
    clients = {}

    print("\nProcessing messages...")
    for i, msg in enumerate(all_messages, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(all_messages)} messages...")

        try:
            # Get message metadata
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
            subject = headers.get('Subject', '')
            date_received = headers.get('Date', '')

            # Get snippet
            snippet = msg_data.get('snippet', '')

            # Get labels
            label_ids = msg_data.get('labelIds', [])
            labels = [label_map.get(lid, lid) for lid in label_ids if lid not in ['INBOX', 'SENT', 'UNREAD', 'IMPORTANT', 'CATEGORY_PERSONAL']]

            # Extract client name from subject first, then try snippet
            client_name = extract_name_from_subject(subject)

            if not client_name:
                client_name = extract_name_from_snippet(snippet)

            if not client_name:
                # Use message ID as fallback for debugging
                print(f"  Skipping - no name found. Subject: {subject[:60]}... Snippet: {snippet[:60]}...")
                continue

            # If we've seen this client before, update info if we have more details
            if client_name in clients:
                # Update with more complete information
                existing = clients[client_name]

                # Extract additional info from snippet
                phone = extract_phone(snippet) or existing.get('Phone')
                email = extract_email(snippet) or existing.get('Email')
                premium = extract_premium(snippet) or existing.get('Premium')
                app_date = extract_date(snippet) or existing.get('Application Date')

                # Merge labels (keep unique)
                merged_labels = list(set(existing.get('Labels', []) + labels))

                clients[client_name] = {
                    'Name': client_name,
                    'Phone': phone,
                    'Email': email,
                    'Premium': premium,
                    'Application Date': app_date,
                    'Labels': merged_labels,
                    'Date Received': date_received,
                    'Subject': subject,
                    'Snippet': snippet
                }
            else:
                # New client
                phone = extract_phone(snippet)
                email = extract_email(snippet)
                premium = extract_premium(snippet)
                app_date = extract_date(snippet)

                clients[client_name] = {
                    'Name': client_name,
                    'Phone': phone,
                    'Email': email,
                    'Premium': premium,
                    'Application Date': app_date,
                    'Labels': labels,
                    'Date Received': date_received,
                    'Subject': subject,
                    'Snippet': snippet
                }

        except Exception as e:
            print(f"Error processing message {msg['id']}: {e}")
            continue

    # Convert to list and sort by name
    client_list = sorted(clients.values(), key=lambda x: x['Name'])

    print(f"\nFound {len(client_list)} unique clients")

    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(client_list, f, indent=2, ensure_ascii=False)

    print(f"\nSaved client data to: {output_file}")

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total unique clients: {len(client_list)}")
    print(f"\nSample clients:")
    for client in client_list[:5]:
        print(f"\n  Name: {client['Name']}")
        print(f"  Phone: {client.get('Phone', 'N/A')}")
        print(f"  Email: {client.get('Email', 'N/A')}")
        print(f"  Premium: {client.get('Premium', 'N/A')}")
        print(f"  Labels: {', '.join(client.get('Labels', []))}")

    if len(client_list) > 5:
        print(f"\n  ... and {len(client_list) - 5} more clients")

    return client_list

def main():
    output_file = r'c:\Coding-projects\MCP-Server\jordan_clients_all.json'

    print("Authenticating with Gmail...")
    service = authenticate()

    print("Authentication successful!")

    # Search and extract
    search_and_extract(service, output_file)

if __name__ == "__main__":
    main()
