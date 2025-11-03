#!/usr/bin/env python3
"""Debug script to see email format"""

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
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def extract_body(payload):
    """Extract body from email payload - handles nested parts"""
    body = ''

    def decode_part(part_data):
        if part_data:
            try:
                return base64.urlsafe_b64decode(part_data).decode('utf-8', errors='ignore')
            except:
                return ''
        return ''

    def extract_from_parts(parts):
        text = ''
        html = ''
        for part in parts:
            mime_type = part.get('mimeType', '')
            if 'parts' in part:
                nested_text, nested_html = extract_from_parts(part['parts'])
                if nested_text and not text:
                    text = nested_text
                if nested_html and not html:
                    html = nested_html
            elif mime_type == 'text/plain':
                if 'data' in part.get('body', {}):
                    text = decode_part(part['body']['data'])
            elif mime_type == 'text/html':
                if 'data' in part.get('body', {}):
                    html = decode_part(part['body']['data'])
        return text, html

    if 'parts' in payload:
        text_body, html_body = extract_from_parts(payload['parts'])
        body = text_body if text_body else html_body
    elif payload.get('body', {}).get('data'):
        body = decode_part(payload['body']['data'])

    return body

service = authenticate()
query = 'from:danielberman.ushealth@gmail.com subject:ACA -label:dead after:2025/06/01'
results = service.users().messages().list(userId='me', q=query, maxResults=30).execute()
messages = results.get('messages', [])

# Get email 16 (index 15)
msg = messages[15]
msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
body = extract_body(msg_data['payload'])

print("="*80)
print(f"Subject: {headers.get('Subject')}")
print("="*80)
print("\nEMAIL BODY:")
print("="*80)
print(body)
print("="*80)
