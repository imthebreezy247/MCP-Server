#!/usr/bin/env python3
"""
Debug script to view multiple email bodies
"""

import os
import sys
import json
import base64
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
SCRIPT_DIR = Path(__file__).parent.absolute()
TOKEN_PATH = SCRIPT_DIR / 'token.json'

def authenticate():
    """Authenticate with Gmail API"""
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('gmail', 'v1', credentials=creds)
    return service


def extract_body(payload):
    """Extract body from email payload"""
    body = ''

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    return body
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                body = extract_body(part)
                if body:
                    return body
    elif payload['body'].get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    return body


def main():
    service = authenticate()

    # Get the first 5 emails
    query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=15
    ).execute()

    messages = results.get('messages', [])

    # Analyze each message
    for idx, msg in enumerate(messages):
        msg_id = msg['id']

        msg_data = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
        body = extract_body(msg_data['payload'])

        # Save to file
        output_file = SCRIPT_DIR / f'debug_email_{idx+1}_{msg_id}.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Message ID: {msg_id}\n")
            f.write(f"Subject: {headers.get('Subject', 'N/A')}\n")
            f.write(f"From: {headers.get('From', 'N/A')}\n")
            f.write(f"Date: {headers.get('Date', 'N/A')}\n")
            f.write("=" * 80 + "\n")
            f.write(body)

        print(f"Saved email {idx+1} to {output_file}")


if __name__ == "__main__":
    main()
