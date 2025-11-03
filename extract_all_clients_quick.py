#!/usr/bin/env python3
"""
Quick extraction of ALL unique clients from search results only (no full email reads)
Uses Gmail search API with high max_results to get all emails at once
Extracts client names from subject lines and any available data from snippets
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

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


def proper_case_name(name: str) -> str:
    """Convert name to proper case"""
    if not name:
        return ''

    name = name.strip()

    # Remove common prefixes/suffixes
    name = re.sub(r'\s+(ACA|aca)$', '', name)

    # Split by spaces and capitalize each word
    words = name.split()
    proper_words = []

    for word in words:
        # Skip empty words
        if not word:
            continue

        # Handle special cases like O'Brien, McDonald
        if "'" in word:
            parts = word.split("'")
            proper_words.append("'".join([p.capitalize() for p in parts]))
        elif word.lower().startswith('mc') and len(word) > 2:
            proper_words.append('Mc' + word[2:].capitalize())
        else:
            proper_words.append(word.capitalize())

    return ' '.join(proper_words)


def extract_name_from_subject(subject: str) -> str:
    """Extract client name from subject line"""
    if not subject:
        return ''

    # Common patterns:
    # "Kayla Harris ACA"
    # "Janet Allen"
    # "John Doe - ACA"

    # Remove common prefixes
    subject = re.sub(r'^(Re:|Fwd:|RE:|FW:)\s*', '', subject, flags=re.IGNORECASE)

    # Try to extract name before ACA
    match = re.search(r'^([A-Za-z\s\'-]+?)(?:\s+ACA|\s+aca|\s+-\s+ACA|\s+-\s+aca|$)', subject)
    if match:
        name = match.group(1).strip()
        return proper_case_name(name)

    return ''


def extract_data_from_snippet(snippet: str) -> Dict[str, str]:
    """Extract any visible data from email snippet"""
    data = {}

    if not snippet:
        return data

    # Policy number pattern (8+ alphanumeric chars)
    policy_match = re.search(r'\b([A-Z0-9]{8,})\b', snippet)
    if policy_match:
        data['Policy Number'] = policy_match.group(1)

    # Phone number pattern
    phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', snippet)
    if phone_match:
        data['Phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

    # Email pattern
    email_match = re.search(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', snippet)
    if email_match:
        data['Email'] = email_match.group(1).lower()

    # Premium pattern
    premium_match = re.search(r'\$\s*([0-9,.]+)', snippet)
    if premium_match:
        data['Premium'] = premium_match.group(1)

    # Date pattern (MM/DD/YYYY)
    date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', snippet)
    if date_match:
        data['Date'] = date_match.group(1)

    return data


def search_all_clients(service, max_results=500):
    """Search for all non-dead emails and extract unique clients from search results"""

    # Search query - all emails from danielberman that DON'T have DEAD label
    query = 'from:danielberman.ushealth@gmail.com -label:DEAD'

    print(f"Searching for emails with query: {query}", file=sys.stderr)
    print(f"Max results: {max_results}", file=sys.stderr)

    all_messages = []
    page_token = None

    try:
        # Paginate through all results
        while True:
            print(f"Fetching batch... (current count: {len(all_messages)})", file=sys.stderr)

            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(500, max_results - len(all_messages)),  # Gmail API max per page is 500
                includeSpamTrash=False,
                pageToken=page_token
            ).execute()

            messages = results.get('messages', [])
            all_messages.extend(messages)

            print(f"  Got {len(messages)} messages in this batch", file=sys.stderr)

            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token or len(all_messages) >= max_results:
                break

        print(f"\nTotal emails found: {len(all_messages)}", file=sys.stderr)

        if not all_messages:
            print("No emails found matching the criteria", file=sys.stderr)
            return []

        # Now get minimal metadata for each message (subject and snippet only)
        # We'll use batch requests for efficiency
        print("\nFetching message metadata (subject & snippet)...", file=sys.stderr)

        clients_dict = {}  # Use dict to track unique clients by name

        for i, msg in enumerate(all_messages, 1):
            if i % 50 == 0:
                print(f"Processing {i}/{len(all_messages)}...", file=sys.stderr)

            try:
                # Get message metadata with minimal format (just headers and snippet)
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()

                # Extract subject
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                subject = headers.get('Subject', '')
                snippet = msg_data.get('snippet', '')

                # Extract client name from subject
                client_name = extract_name_from_subject(subject)

                if not client_name:
                    # Try to extract from snippet as fallback
                    continue

                # Extract any data visible in snippet
                snippet_data = extract_data_from_snippet(snippet)

                # If we already have this client, merge data (keep non-empty values)
                if client_name in clients_dict:
                    existing = clients_dict[client_name]
                    for key, value in snippet_data.items():
                        if value and not existing.get(key):
                            existing[key] = value
                else:
                    # New client
                    client_info = {
                        'Name': client_name,
                        'Policy Number': snippet_data.get('Policy Number', ''),
                        'Phone': snippet_data.get('Phone', ''),
                        'Email': snippet_data.get('Email', ''),
                        'Premium': snippet_data.get('Premium', ''),
                        'Date': snippet_data.get('Date', ''),
                        'Message ID': msg['id'],
                        'Subject': subject,
                        'Snippet': snippet[:100]  # First 100 chars for reference
                    }
                    clients_dict[client_name] = client_info

            except HttpError as e:
                print(f"  Error processing message {msg['id']}: {e}", file=sys.stderr)
                continue

        print(f"\nExtracted {len(clients_dict)} unique clients", file=sys.stderr)

        # Convert dict to sorted list
        clients_list = sorted(clients_dict.values(), key=lambda x: x['Name'])

        return clients_list

    except HttpError as e:
        print(f"Error searching emails: {e}", file=sys.stderr)
        return []


def main():
    """Main function"""
    print("="*80, file=sys.stderr)
    print("Gmail Quick Client Extractor - Search Results Only", file=sys.stderr)
    print("="*80, file=sys.stderr)

    # Authenticate
    print("\nAuthenticating with Gmail...", file=sys.stderr)
    service = authenticate()
    print("Authentication successful!", file=sys.stderr)

    # Search and extract from results only
    clients = search_all_clients(service, max_results=500)

    # Save to file
    output_path = Path(r'C:\Coding-projects\MCP-Server\all_clients_quick.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clients, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"SUCCESS! Saved {len(clients)} unique clients to:", file=sys.stderr)
    print(f"{output_path}", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)

    # Also print to stdout for immediate viewing
    print(json.dumps(clients, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
