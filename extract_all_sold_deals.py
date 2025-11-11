#!/usr/bin/env python3
"""
Extract all sold deal emails from multiple Gmail accounts
Includes: processed-sold-deals and sold-deal-paid labels
Excludes: dead deal labels
"""

import json
import re
import base64
import os
from datetime import datetime
from pathlib import Path

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Paths
SCRIPT_DIR = Path(__file__).parent.absolute()

# Email accounts to process
# The script will use the same credentials.json but different token files
# This assumes you have a multi-account OAuth setup or will authenticate each account separately
EMAIL_ACCOUNTS = [
    "danielhera.ushealth@gmail.com",
    "jordang.ushealth@gmail.com",
    "danielberman.ushealth@gmail.com",
    "richardodle.ushealth@gmail.com"
]

# Credential paths - use same credentials file for all accounts
CREDENTIALS_PATH = SCRIPT_DIR / "credentials.json"

# Labels to include (SOLD labels)
INCLUDE_LABELS = [
    "processed-sold-deals-using-automation-to-final-label",
    "sold-deal-paid---sold-deals"
]

# Labels to exclude (DEAD labels - exact labels)
EXCLUDE_LABELS = [
    "aca-leads-to-be-worked-dead-deal",
    "aca-leads-to-be-worked-tanya-deals-processed-tanya-sold-deals",
    "aca-leads-to-be-worked-tanya-deals-tanya-sold-deals",
    "aca-leads-to-be-worked-tanya-deals"
]


def get_token_path_for_account(email_account):
    """Get the token file path for a specific email account"""
    # Create a safe filename from the email
    account_name = email_account.split('@')[0].replace('.', '_')
    return SCRIPT_DIR / f"token_{account_name}.json"


def authenticate_gmail(email_account):
    """Authenticate with Gmail API for a specific account"""
    creds = None
    token_path = get_token_path_for_account(email_account)

    # Load existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"  Error loading token: {e}")

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"  Refreshing expired credentials for {email_account}...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  Error refreshing credentials: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"  ERROR: Missing {CREDENTIALS_PATH}")
                print(f"  Please ensure OAuth credentials are available")
                print(f"  Download credentials from Google Cloud Console")
                return None

            print(f"  Starting OAuth flow for {email_account}...")
            print(f"  IMPORTANT: Please log in with {email_account} when prompted!")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES)

            try:
                creds = flow.run_local_server(port=0)
                print(f"  [OK] Authentication successful!")
            except Exception as e:
                print(f"  Error during authentication: {e}")
                return None

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            print(f"  [OK] Credentials saved to {token_path}")

    service = build('gmail', 'v1', credentials=creds)
    return service


def extract_body(payload):
    """Extract email body from message payload"""
    body = ''

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] in ['text/plain', 'text/html']:
                if 'data' in part['body']:
                    body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                body += extract_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    return body


def get_header_value(headers, name):
    """Get header value from list of headers"""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ''


def extract_client_info(message, account_email):
    """Extract client information from email message"""
    try:
        headers = message['payload']['headers']
        subject = get_header_value(headers, 'Subject')
        from_email = get_header_value(headers, 'From')
        date_str = get_header_value(headers, 'Date')

        # Extract body
        body = extract_body(message['payload'])
        snippet = message.get('snippet', '')

        # Combine all text for searching
        full_text = f"{subject}\n{body}\n{snippet}"

        # Extract phone number
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
            r'\b\d{10}\b'
        ]
        phone = None
        for pattern in phone_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # Get the first phone number that looks valid
                for match in matches:
                    # Clean up the phone number
                    cleaned = re.sub(r'[^\d]', '', match)
                    if len(cleaned) == 10:
                        phone = match
                        break
                if phone:
                    break

        # Extract email address (client email, not the account email)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, full_text)
        client_email = None
        for email in emails:
            email_lower = email.lower()
            if 'ushealth' not in email_lower and 'gmail' not in email_lower and 'google' not in email_lower:
                client_email = email
                break

        # Extract name - try multiple patterns
        first_name = None
        last_name = None
        full_name = None

        # Pattern 1: Look for "Name:" or "Client:" followed by a name
        name_patterns = [
            r'(?:Name|Client|Customer|Applicant):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b'
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # Filter out common non-name matches
                for match in matches:
                    match = match.strip()
                    # Skip if it looks like a company or common phrase
                    skip_words = ['United States', 'Health Insurance', 'Customer Service', 'Email Address']
                    if not any(skip in match for skip in skip_words):
                        full_name = match
                        name_parts = full_name.split()
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = ' '.join(name_parts[1:])
                            break
                if full_name:
                    break

        # Extract premium
        premium_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'premium[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'amount[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'monthly[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        premium = None
        for pattern in premium_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                premium = match.group(1)
                # Validate it's a reasonable premium amount
                try:
                    amount = float(premium.replace(',', ''))
                    if 10 <= amount <= 10000:  # Reasonable range for health insurance premium
                        break
                    else:
                        premium = None
                except:
                    premium = None

        # Extract agent name from sender
        agent_name = from_email
        if '<' in from_email:
            agent_name = from_email.split('<')[0].strip()

        # Get labels
        label_ids = message.get('labelIds', [])

        return {
            'First Name': first_name,
            'Last Name': last_name,
            'Full Name': full_name,
            'Agent Name': agent_name,
            'Phone': phone,
            'Email': client_email,
            'Premium': premium,
            'Subject': subject,
            'Date': date_str,
            'Labels': label_ids,
            'Message ID': message['id'],
            'Source Account': account_email
        }
    except Exception as e:
        print(f"  Error extracting info from message: {e}")
        return None


def get_label_name(service, label_id):
    """Get label name from label ID"""
    try:
        label = service.users().labels().get(userId='me', id=label_id).execute()
        return label.get('name', '')
    except:
        return ''


def search_messages_with_label(service, label_query, max_results=500):
    """Search for messages with specific label"""
    try:
        results = service.users().messages().list(
            userId='me',
            q=label_query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        # Handle pagination if there are more results
        while 'nextPageToken' in results and len(messages) < max_results:
            page_token = results['nextPageToken']
            results = service.users().messages().list(
                userId='me',
                q=label_query,
                maxResults=max_results - len(messages),
                pageToken=page_token
            ).execute()
            messages.extend(results.get('messages', []))

        return messages
    except HttpError as error:
        print(f'  Error searching messages: {error}')
        return []


def get_message_full(service, msg_id):
    """Get full message details"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        return message
    except HttpError as error:
        print(f'  Error getting message {msg_id}: {error}')
        return None


def has_exclude_label(label_ids, service):
    """Check if message has any exclude labels"""
    for label_id in label_ids:
        label_name = get_label_name(service, label_id)
        # Check for exact match against exclude labels
        if label_name in EXCLUDE_LABELS:
            return True
    return False


def process_email_account(email_account):
    """Process a single email account"""
    print(f"\n{'='*80}")
    print(f"Processing account: {email_account}")
    print(f"{'='*80}")

    all_clients = []

    try:
        # Authenticate
        print(f"\nAuthenticating {email_account}...")
        service = authenticate_gmail(email_account)

        if not service:
            print(f"  [ERROR] Failed to authenticate {email_account}")
            return []

        print(f"  [OK] Successfully authenticated")

        # Collect all message IDs from INCLUDE labels
        all_message_ids = set()

        for label in INCLUDE_LABELS:
            print(f"\n  Searching for label: {label}")
            query = f'label:{label}'
            messages = search_messages_with_label(service, query, max_results=500)
            print(f"  Found {len(messages)} messages with label: {label}")

            for msg in messages:
                all_message_ids.add(msg['id'])

        print(f"\n  Total unique messages to process: {len(all_message_ids)}")

        # Process each message
        processed_count = 0
        skipped_count = 0

        for msg_id in all_message_ids:
            try:
                message = get_message_full(service, msg_id)

                if message:
                    # Check if message has any EXCLUDE labels
                    label_ids = message.get('labelIds', [])

                    if has_exclude_label(label_ids, service):
                        skipped_count += 1
                        continue

                    # Extract client information
                    client_info = extract_client_info(message, email_account)

                    if client_info:
                        all_clients.append(client_info)
                        processed_count += 1

                        if processed_count % 10 == 0:
                            print(f"  Processed: {processed_count}, Skipped: {skipped_count}, Remaining: {len(all_message_ids) - processed_count - skipped_count}")

            except Exception as e:
                print(f"  Error processing message {msg_id}: {e}")
                continue

        print(f"\n  Completed processing {email_account}")
        print(f"  Total extracted: {len(all_clients)} client records")
        print(f"  Skipped (dead labels): {skipped_count}")

    except Exception as e:
        print(f"  [ERROR] Error processing account {email_account}: {e}")

    return all_clients


def main():
    """Main function to process all email accounts"""
    print("="*80)
    print("SOLD DEALS EXTRACTION - ALL ACCOUNTS")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nAccounts to process: {len(EMAIL_ACCOUNTS)}")
    print(f"Include labels: {', '.join(INCLUDE_LABELS)}")
    print(f"Exclude labels: {len(EXCLUDE_LABELS)} labels (dead/tanya deals)")

    all_results = {}
    total_clients = 0

    # Process each email account
    for email_account in EMAIL_ACCOUNTS:
        clients = process_email_account(email_account)

        account_key = email_account.split('@')[0]
        all_results[account_key] = clients
        total_clients += len(clients)

        # Save individual account results
        filename = f"{account_key}_sold_deals.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(clients, f, indent=2, ensure_ascii=False)
        print(f"\n  [OK] Saved {len(clients)} records to {filename}")

    # Save consolidated results
    consolidated_file = "all_sold_deals_consolidated.json"
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Save flat list of all clients
    all_clients_flat = []
    for clients in all_results.values():
        all_clients_flat.extend(clients)

    flat_file = "all_sold_deals_flat.json"
    with open(flat_file, 'w', encoding='utf-8') as f:
        json.dump(all_clients_flat, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"\nTotal clients extracted: {total_clients}")
    print(f"\nBreakdown by account:")
    for account, clients in all_results.items():
        print(f"  {account}: {len(clients)} clients")
    print(f"\nFiles saved:")
    print(f"  - {consolidated_file} (organized by account)")
    print(f"  - {flat_file} (flat list)")
    for account in all_results.keys():
        print(f"  - {account}_sold_deals.json")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
