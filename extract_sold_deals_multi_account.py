#!/usr/bin/env python3
"""
Extract all sold deal emails from multiple Gmail accounts
Includes: processed-sold-deals and sold-deal-paid labels
Excludes: dead deal labels

This version supports multi-account authentication with better error handling
"""

import json
import re
import base64
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Required Google API packages not installed.")
    print("Please install them with:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Paths
SCRIPT_DIR = Path(__file__).parent.absolute()

# Email accounts to process
EMAIL_ACCOUNTS = [
    "danielhera.ushealth@gmail.com",
    "jordang.ushealth@gmail.com",
    "danielberman.ushealth@gmail.com",
    "richardodle.ushealth@gmail.com"
]

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


def find_credentials_file():
    """Find any available credentials file"""
    possible_names = [
        "credentials.json",
        "credentials_secondary.json",
        "client_secret.json",
        "client_secrets.json",
        "oauth2_credentials.json"
    ]

    for name in possible_names:
        path = SCRIPT_DIR / name
        if path.exists():
            print(f"  Found credentials file: {path}")
            return path

    return None


def get_token_path_for_account(email_account):
    """Get the token file path for a specific email account"""
    # Create a safe filename from the email
    account_name = email_account.split('@')[0].replace('.', '_')
    return SCRIPT_DIR / f"token_{account_name}.json"


def create_oauth_flow(credentials_path):
    """Create OAuth flow with manual authentication support"""
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # For manual copy-paste flow
    )
    return flow


def manual_authentication(flow):
    """Handle manual OAuth authentication for WSL/headless environments"""
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("\n" + "="*80)
    print("MANUAL OAUTH AUTHENTICATION REQUIRED")
    print("="*80)
    print("\nPlease follow these steps:")
    print("\n1. Copy and open this URL in your browser:\n")
    print(auth_url)
    print("\n2. Sign in with the Google account you want to use")
    print("3. Accept the permissions")
    print("4. Copy the authorization code from the browser")
    print("="*80)

    code = input("\nPaste the authorization code here: ").strip()

    try:
        flow.fetch_token(code=code)
        return flow.credentials
    except Exception as e:
        print(f"  Error during authentication: {e}")
        return None


def authenticate_gmail(email_account):
    """Authenticate with Gmail API for a specific account"""
    creds = None
    token_path = get_token_path_for_account(email_account)

    # Load existing token
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            print(f"  Found existing token for {email_account}")
        except Exception as e:
            print(f"  Error loading token: {e}")

    # If there are no (valid) credentials available, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"  Refreshing expired credentials for {email_account}...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  Error refreshing credentials: {e}")
                creds = None

        if not creds:
            # Find credentials file
            credentials_path = find_credentials_file()

            if not credentials_path:
                print(f"  ERROR: No OAuth credentials file found!")
                print(f"  Please obtain credentials from Google Cloud Console:")
                print(f"  1. Go to https://console.cloud.google.com/")
                print(f"  2. Create or select a project")
                print(f"  3. Enable Gmail API")
                print(f"  4. Create OAuth 2.0 credentials (Desktop application)")
                print(f"  5. Download and save as 'credentials.json' in {SCRIPT_DIR}")
                return None

            print(f"  Starting OAuth flow for {email_account}...")
            print(f"  IMPORTANT: When prompted in browser, sign in with {email_account}!")

            flow = create_oauth_flow(credentials_path)

            # Try automatic browser flow first
            try:
                creds = flow.run_local_server(port=0)
                print(f"  [OK] Authentication successful!")
            except Exception as e:
                print(f"  Browser authentication failed: {e}")
                print(f"  Switching to manual authentication...")

                # Fall back to manual authentication
                flow = create_oauth_flow(credentials_path)
                creds = manual_authentication(flow)

                if not creds:
                    print(f"  [ERROR] Manual authentication also failed")
                    return None

        # Save the credentials for the next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                print(f"  [OK] Credentials saved to {token_path}")
        except Exception as e:
            print(f"  Warning: Could not save token: {e}")

    try:
        service = build('gmail', 'v1', credentials=creds)
        # Test the connection
        profile = service.users().getProfile(userId='me').execute()
        print(f"  [OK] Connected to: {profile['emailAddress']}")
        return service
    except Exception as e:
        print(f"  [ERROR] Failed to build Gmail service: {e}")
        return None


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
                for match in matches:
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
            # Skip US Health related emails and common service emails
            skip_domains = ['ushealth', 'gmail', 'google', 'outlook', 'yahoo', 'hotmail']
            if not any(domain in email_lower for domain in skip_domains):
                client_email = email
                break

        # Extract name - try multiple patterns
        first_name = None
        last_name = None
        full_name = None

        # Pattern 1: Look for specific labels followed by a name
        name_patterns = [
            r'(?:Name|Client|Customer|Applicant|Member):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'(?:First Name|First):\s*([A-Z][a-z]+)',
            r'(?:Last Name|Last):\s*([A-Z][a-z]+)',
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                if 'First' in pattern:
                    first_name = matches[0] if matches else first_name
                elif 'Last' in pattern:
                    last_name = matches[0] if matches else last_name
                else:
                    for match in matches:
                        match = match.strip()
                        skip_words = ['United States', 'Health Insurance', 'Customer Service',
                                     'Email Address', 'Phone Number', 'Social Security']
                        if not any(skip in match for skip in skip_words):
                            full_name = match
                            name_parts = full_name.split()
                            if len(name_parts) >= 2:
                                first_name = first_name or name_parts[0]
                                last_name = last_name or ' '.join(name_parts[1:])
                                break

        # Extract premium
        premium_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:premium|monthly premium|total premium)[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:amount|monthly amount)[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        premium = None
        for pattern in premium_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1)
                try:
                    amount = float(amount_str.replace(',', ''))
                    if 10 <= amount <= 10000:  # Reasonable range for health insurance premium
                        premium = f"${amount_str}"
                        break
                except:
                    continue
            if premium:
                break

        # Extract agent name from sender
        agent_name = from_email
        if '<' in from_email:
            agent_name = from_email.split('<')[0].strip()

        # Get labels
        label_ids = message.get('labelIds', [])

        return {
            'First Name': first_name,
            'Last Name': last_name,
            'Full Name': full_name or (f"{first_name} {last_name}" if first_name and last_name else None),
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


def search_messages_with_label(service, label_query, max_results=1000):
    """Search for messages with specific label"""
    try:
        all_messages = []
        page_token = None

        while len(all_messages) < max_results:
            results = service.users().messages().list(
                userId='me',
                q=label_query,
                maxResults=min(500, max_results - len(all_messages)),
                pageToken=page_token
            ).execute()

            messages = results.get('messages', [])
            all_messages.extend(messages)

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return all_messages
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
            print(f"  Skipping this account...")
            return []

        # Collect all message IDs from INCLUDE labels
        all_message_ids = set()

        for label in INCLUDE_LABELS:
            print(f"\n  Searching for label: {label}")
            query = f'label:{label}'
            messages = search_messages_with_label(service, query, max_results=1000)
            print(f"  Found {len(messages)} messages with label: {label}")

            for msg in messages:
                all_message_ids.add(msg['id'])

        print(f"\n  Total unique messages to process: {len(all_message_ids)}")

        # Process each message
        processed_count = 0
        skipped_count = 0
        extracted_count = 0

        for idx, msg_id in enumerate(all_message_ids, 1):
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
                        # Only add if we have at least some identifying information
                        if client_info['First Name'] or client_info['Last Name'] or client_info['Email'] or client_info['Phone']:
                            all_clients.append(client_info)
                            extracted_count += 1

                    processed_count += 1

                    # Progress update
                    if processed_count % 10 == 0 or idx == len(all_message_ids):
                        print(f"  Progress: {idx}/{len(all_message_ids)} - Extracted: {extracted_count}, Skipped: {skipped_count}")

            except Exception as e:
                print(f"  Error processing message {msg_id}: {e}")
                continue

        print(f"\n  Completed processing {email_account}")
        print(f"  Total messages processed: {processed_count}")
        print(f"  Total extracted: {extracted_count} client records")
        print(f"  Skipped (excluded labels): {skipped_count}")

    except Exception as e:
        print(f"  [ERROR] Error processing account {email_account}: {e}")

    return all_clients


def main():
    """Main function to process all email accounts"""
    print("="*80)
    print("SOLD DEALS EXTRACTION - MULTIPLE GMAIL ACCOUNTS")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nAccounts to process: {len(EMAIL_ACCOUNTS)}")
    for account in EMAIL_ACCOUNTS:
        print(f"  - {account}")
    print(f"\nInclude labels:")
    for label in INCLUDE_LABELS:
        print(f"  + {label}")
    print(f"\nExclude labels:")
    for label in EXCLUDE_LABELS:
        print(f"  - {label}")

    all_results = {}
    total_clients = 0

    # Process each email account
    for email_account in EMAIL_ACCOUNTS:
        clients = process_email_account(email_account)

        account_key = email_account.split('@')[0].replace('.', '_')
        all_results[account_key] = clients
        total_clients += len(clients)

        # Save individual account results
        if clients:
            filename = SCRIPT_DIR / f"{account_key}_sold_deals.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(clients, f, indent=2, ensure_ascii=False)
            print(f"\n  [OK] Saved {len(clients)} records to {filename}")

    # Save consolidated results (organized by account)
    consolidated_file = SCRIPT_DIR / "all_sold_deals_consolidated.json"
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Save flat list of all clients
    all_clients_flat = []
    for clients in all_results.values():
        all_clients_flat.extend(clients)

    flat_file = SCRIPT_DIR / "all_sold_deals_flat.json"
    with open(flat_file, 'w', encoding='utf-8') as f:
        json.dump(all_clients_flat, f, indent=2, ensure_ascii=False)

    # Print final summary
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"\nTotal clients extracted: {total_clients}")

    print(f"\nBreakdown by account:")
    for account, clients in all_results.items():
        print(f"  {account}: {len(clients)} clients")

    print(f"\nFiles saved:")
    print(f"  - {consolidated_file.absolute()} (organized by account)")
    print(f"  - {flat_file.absolute()} (flat list)")
    for account in all_results.keys():
        filename = SCRIPT_DIR / f"{account}_sold_deals.json"
        if filename.exists():
            print(f"  - {filename.absolute()}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Return summary for programmatic use
    return {
        'total_clients': total_clients,
        'accounts_processed': len(all_results),
        'breakdown': {account: len(clients) for account, clients in all_results.items()},
        'files_created': {
            'consolidated': str(consolidated_file.absolute()),
            'flat': str(flat_file.absolute()),
            'individual': [str((SCRIPT_DIR / f"{account}_sold_deals.json").absolute())
                          for account in all_results.keys()
                          if (SCRIPT_DIR / f"{account}_sold_deals.json").exists()]
        }
    }


if __name__ == "__main__":
    try:
        summary = main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)