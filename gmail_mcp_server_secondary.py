#!/usr/bin/env python3
"""
Gmail MCP Server - A complete Gmail integration for Model Context Protocol
Provides full Gmail API functionality through MCP interface
"""

import os
import sys
import json
import base64
import mimetypes
import asyncio
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# MCP imports
from fastmcp import FastMCP

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Gmail API scope - full access to Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Token storage path - use absolute paths
# Secondary account uses separate token file
TOKEN_PATH = SCRIPT_DIR / 'token_secondary.json'
CREDENTIALS_PATH = SCRIPT_DIR / 'credentials.json'

class GmailMCPServer:
    """Gmail MCP Server implementation"""

    def __init__(self):
        self.service = None
        self.mcp = FastMCP("Gmail MCP Server (Secondary)")
        self._setup_handlers()

    def authenticate(self, manual_auth=False):
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

                if manual_auth:
                    # Manual authentication flow for WSL/headless environments
                    print("\n" + "="*60, file=sys.stderr)
                    print("MANUAL OAUTH AUTHENTICATION REQUIRED", file=sys.stderr)
                    print("="*60, file=sys.stderr)
                    print("Since automatic browser opening failed, please follow these steps:", file=sys.stderr)
                    print("\n1. Copy the URL below and paste it into a web browser:", file=sys.stderr)

                    # Set redirect URI for manual flow
                    flow.redirect_uri = 'http://localhost'

                    # Generate authorization URL with proper parameters
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        prompt='consent'
                    )
                    print(f"\n{auth_url}\n", file=sys.stderr)

                    print("2. Complete the authorization in your browser", file=sys.stderr)
                    print("3. After authorizing, you'll be redirected to localhost (page may not load)", file=sys.stderr)
                    print("4. Copy the ENTIRE URL from your browser's address bar", file=sys.stderr)
                    print("5. Paste it below when prompted", file=sys.stderr)
                    print("="*60, file=sys.stderr)

                    # Get authorization response URL from user
                    auth_response = input("\nPaste the entire redirect URL here: ").strip()

                    # Extract the code from the URL
                    if 'code=' in auth_response:
                        auth_code = auth_response.split('code=')[1].split('&')[0]
                    else:
                        auth_code = auth_response  # Assume they just pasted the code

                    # Exchange code for credentials
                    flow.fetch_token(code=auth_code)
                    creds = flow.credentials

                    print("[OK] Authentication successful!", file=sys.stderr)
                else:
                    # Try automatic flow first
                    try:
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        print(f"Automatic authentication failed: {e}", file=sys.stderr)
                        print("Falling back to manual authentication...", file=sys.stderr)
                        return self.authenticate(manual_auth=True)

            # Save the credentials for the next run
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
                print(f"[OK] Credentials saved to {TOKEN_PATH}", file=sys.stderr)

        self.service = build('gmail', 'v1', credentials=creds)
        return True

    def _setup_handlers(self):
        """Setup all MCP handlers"""

        @self.mcp.tool()
        async def send_email(
            to: str,
            subject: str,
            body: str,
            cc: Optional[str] = None,
            bcc: Optional[str] = None,
            html: bool = False,
            attachments: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Send an email

            Args:
                to: Recipient email address(es), comma-separated for multiple
                subject: Email subject
                body: Email body content
                cc: CC recipients, comma-separated (optional)
                bcc: BCC recipients, comma-separated (optional)
                html: Whether body is HTML content (default: False)
                attachments: List of file paths to attach (optional)

            Returns:
                Dict with message ID and thread ID
            """
            try:
                message = MIMEMultipart() if attachments else MIMEText(body, 'html' if html else 'plain')

                if attachments:
                    message.attach(MIMEText(body, 'html' if html else 'plain'))
                    for file_path in attachments:
                        if os.path.isfile(file_path):
                            with open(file_path, 'rb') as f:
                                mime_type, _ = mimetypes.guess_type(file_path)
                                if mime_type:
                                    main_type, sub_type = mime_type.split('/')
                                else:
                                    main_type, sub_type = 'application', 'octet-stream'

                                attachment = MIMEBase(main_type, sub_type)
                                attachment.set_payload(f.read())
                                encoders.encode_base64(attachment)
                                attachment.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename="{os.path.basename(file_path)}"'
                                )
                                message.attach(attachment)

                message['to'] = to
                message['subject'] = subject
                if cc:
                    message['cc'] = cc
                if bcc:
                    message['bcc'] = bcc

                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                sent_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()

                return {
                    'success': True,
                    'messageId': sent_message['id'],
                    'threadId': sent_message.get('threadId')
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def create_draft(
            to: str,
            subject: str,
            body: str,
            cc: Optional[str] = None,
            bcc: Optional[str] = None,
            html: bool = False
        ) -> Dict[str, Any]:
            """
            Create a draft email

            Args:
                to: Recipient email address(es)
                subject: Email subject
                body: Email body content
                cc: CC recipients (optional)
                bcc: BCC recipients (optional)
                html: Whether body is HTML content

            Returns:
                Dict with draft ID and message ID
            """
            try:
                message = MIMEText(body, 'html' if html else 'plain')
                message['to'] = to
                message['subject'] = subject
                if cc:
                    message['cc'] = cc
                if bcc:
                    message['bcc'] = bcc

                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                draft = self.service.users().drafts().create(
                    userId='me',
                    body={'message': {'raw': raw_message}}
                ).execute()

                return {
                    'success': True,
                    'draftId': draft['id'],
                    'messageId': draft['message']['id']
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def search_emails(
            query: str,
            max_results: int = 10,
            include_spam_trash: bool = False
        ) -> Dict[str, Any]:
            """
            Search emails using Gmail query syntax

            Args:
                query: Gmail search query (e.g., "from:sender@example.com subject:important")
                max_results: Maximum number of results to return (default: 10)
                include_spam_trash: Include spam and trash folders (default: False)

            Returns:
                Dict with list of matching emails
            """
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results,
                    includeSpamTrash=include_spam_trash
                ).execute()

                messages = results.get('messages', [])
                email_list = []

                for msg in messages:
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()

                    headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}

                    email_list.append({
                        'id': msg['id'],
                        'threadId': msg_data['threadId'],
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', ''),
                        'date': headers.get('Date', ''),
                        'snippet': msg_data.get('snippet', ''),
                        'labelIds': msg_data.get('labelIds', [])
                    })

                return {
                    'success': True,
                    'count': len(email_list),
                    'emails': email_list
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def read_email(
            message_id: str,
            format: str = 'full'
        ) -> Dict[str, Any]:
            """
            Read a specific email by ID

            Args:
                message_id: The Gmail message ID
                format: Format of response - 'full', 'metadata', or 'minimal'

            Returns:
                Dict with email content and metadata
            """
            try:
                message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format=format
                ).execute()

                # Extract body content if format is 'full'
                body_content = ''
                if format == 'full' and 'payload' in message:
                    body_content = self._extract_body(message['payload'])

                # Extract headers
                headers = {}
                if 'payload' in message and 'headers' in message['payload']:
                    headers = {h['name']: h['value'] for h in message['payload']['headers']}

                return {
                    'success': True,
                    'id': message['id'],
                    'threadId': message['threadId'],
                    'labelIds': message.get('labelIds', []),
                    'snippet': message.get('snippet', ''),
                    'headers': headers,
                    'body': body_content,
                    'sizeEstimate': message.get('sizeEstimate', 0),
                    'internalDate': message.get('internalDate', '')
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def get_thread(
            thread_id: str
        ) -> Dict[str, Any]:
            """
            Get all messages in a thread

            Args:
                thread_id: The Gmail thread ID

            Returns:
                Dict with all messages in the thread
            """
            try:
                thread = self.service.users().threads().get(
                    userId='me',
                    id=thread_id
                ).execute()

                messages = []
                for msg in thread.get('messages', []):
                    headers = {h['name']: h['value']
                              for h in msg['payload'].get('headers', [])}
                    body = self._extract_body(msg['payload'])

                    messages.append({
                        'id': msg['id'],
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', ''),
                        'date': headers.get('Date', ''),
                        'body': body,
                        'snippet': msg.get('snippet', '')
                    })

                return {
                    'success': True,
                    'threadId': thread_id,
                    'messageCount': len(messages),
                    'messages': messages
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def reply_to_email(
            message_id: str,
            body: str,
            html: bool = False
        ) -> Dict[str, Any]:
            """
            Reply to an email (maintains thread)

            Args:
                message_id: The message ID to reply to
                body: Reply body content
                html: Whether body is HTML content

            Returns:
                Dict with sent message details
            """
            try:
                # Get original message
                original = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Message-ID']
                ).execute()

                headers = {h['name']: h['value']
                          for h in original['payload'].get('headers', [])}

                # Create reply
                message = MIMEText(body, 'html' if html else 'plain')
                message['to'] = headers.get('From', '')
                message['subject'] = f"Re: {headers.get('Subject', '').replace('Re: ', '')}"
                message['In-Reply-To'] = headers.get('Message-ID', '')
                message['References'] = headers.get('Message-ID', '')

                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                sent_message = self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message, 'threadId': original['threadId']}
                ).execute()

                return {
                    'success': True,
                    'messageId': sent_message['id'],
                    'threadId': sent_message['threadId']
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def list_labels(self) -> Dict[str, Any]:
            """
            List all Gmail labels

            Returns:
                Dict with list of labels
            """
            try:
                results = self.service.users().labels().list(userId='me').execute()
                labels = results.get('labels', [])

                label_list = []
                for label in labels:
                    label_list.append({
                        'id': label['id'],
                        'name': label['name'],
                        'type': label.get('type', 'user'),
                        'messageListVisibility': label.get('messageListVisibility', ''),
                        'labelListVisibility': label.get('labelListVisibility', '')
                    })

                return {
                    'success': True,
                    'count': len(label_list),
                    'labels': label_list
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def create_label(
            name: str,
            message_list_visibility: str = 'show',
            label_list_visibility: str = 'labelShow'
        ) -> Dict[str, Any]:
            """
            Create a new Gmail label

            Args:
                name: Label name (use '/' for nested labels)
                message_list_visibility: 'show' or 'hide'
                label_list_visibility: 'labelShow' or 'labelHide'

            Returns:
                Dict with created label details
            """
            try:
                label = self.service.users().labels().create(
                    userId='me',
                    body={
                        'name': name,
                        'messageListVisibility': message_list_visibility,
                        'labelListVisibility': label_list_visibility
                    }
                ).execute()

                return {
                    'success': True,
                    'labelId': label['id'],
                    'name': label['name']
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def modify_message_labels(
            message_id: str,
            add_labels: Optional[List[str]] = None,
            remove_labels: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Add or remove labels from a message

            Args:
                message_id: The Gmail message ID
                add_labels: List of label IDs to add
                remove_labels: List of label IDs to remove

            Returns:
                Dict with updated message info
            """
            try:
                body = {}
                if add_labels:
                    body['addLabelIds'] = add_labels
                if remove_labels:
                    body['removeLabelIds'] = remove_labels

                message = self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body=body
                ).execute()

                return {
                    'success': True,
                    'messageId': message['id'],
                    'labelIds': message.get('labelIds', [])
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def delete_message(
            message_id: str
        ) -> Dict[str, Any]:
            """
            Permanently delete a message

            Args:
                message_id: The Gmail message ID to delete

            Returns:
                Dict with deletion status
            """
            try:
                self.service.users().messages().delete(
                    userId='me',
                    id=message_id
                ).execute()

                return {
                    'success': True,
                    'message': f'Message {message_id} deleted successfully'
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def trash_message(
            message_id: str
        ) -> Dict[str, Any]:
            """
            Move a message to trash

            Args:
                message_id: The Gmail message ID to trash

            Returns:
                Dict with trash status
            """
            try:
                message = self.service.users().messages().trash(
                    userId='me',
                    id=message_id
                ).execute()

                return {
                    'success': True,
                    'messageId': message['id'],
                    'message': f'Message {message_id} moved to trash'
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def batch_modify_messages(
            message_ids: List[str],
            add_labels: Optional[List[str]] = None,
            remove_labels: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Modify multiple messages at once

            Args:
                message_ids: List of message IDs to modify
                add_labels: Label IDs to add to all messages
                remove_labels: Label IDs to remove from all messages

            Returns:
                Dict with batch operation status
            """
            try:
                body = {'ids': message_ids}
                if add_labels:
                    body['addLabelIds'] = add_labels
                if remove_labels:
                    body['removeLabelIds'] = remove_labels

                self.service.users().messages().batchModify(
                    userId='me',
                    body=body
                ).execute()

                return {
                    'success': True,
                    'messageCount': len(message_ids),
                    'message': f'Successfully modified {len(message_ids)} messages'
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def create_filter(
            from_address: Optional[str] = None,
            to_address: Optional[str] = None,
            subject: Optional[str] = None,
            query: Optional[str] = None,
            has_attachment: Optional[bool] = None,
            add_labels: Optional[List[str]] = None,
            remove_labels: Optional[List[str]] = None,
            forward_to: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create an email filter

            Args:
                from_address: Filter by sender
                to_address: Filter by recipient
                subject: Filter by subject
                query: Advanced query string
                has_attachment: Filter messages with attachments
                add_labels: Labels to add to matching messages
                remove_labels: Labels to remove from matching messages
                forward_to: Email address to forward matching messages

            Returns:
                Dict with filter creation status
            """
            try:
                criteria = {}
                if from_address:
                    criteria['from'] = from_address
                if to_address:
                    criteria['to'] = to_address
                if subject:
                    criteria['subject'] = subject
                if query:
                    criteria['query'] = query
                if has_attachment is not None:
                    criteria['hasAttachment'] = has_attachment

                action = {}
                if add_labels:
                    action['addLabelIds'] = add_labels
                if remove_labels:
                    action['removeLabelIds'] = remove_labels
                if forward_to:
                    action['forward'] = forward_to

                filter_obj = self.service.users().settings().filters().create(
                    userId='me',
                    body={'criteria': criteria, 'action': action}
                ).execute()

                return {
                    'success': True,
                    'filterId': filter_obj['id'],
                    'criteria': filter_obj.get('criteria', {}),
                    'action': filter_obj.get('action', {})
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def download_attachment(
            message_id: str,
            attachment_id: str,
            save_path: str
        ) -> Dict[str, Any]:
            """
            Download an attachment from an email

            Args:
                message_id: The Gmail message ID
                attachment_id: The attachment ID
                save_path: Path where to save the attachment

            Returns:
                Dict with download status
            """
            try:
                attachment = self.service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment_id
                ).execute()

                file_data = base64.urlsafe_b64decode(attachment['data'])

                with open(save_path, 'wb') as f:
                    f.write(file_data)

                return {
                    'success': True,
                    'message': f'Attachment saved to {save_path}',
                    'size': len(file_data)
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        @self.mcp.tool()
        async def get_profile(self) -> Dict[str, Any]:
            """
            Get Gmail profile information

            Returns:
                Dict with profile details
            """
            try:
                profile = self.service.users().getProfile(userId='me').execute()

                return {
                    'success': True,
                    'emailAddress': profile['emailAddress'],
                    'messagesTotal': profile.get('messagesTotal', 0),
                    'threadsTotal': profile.get('threadsTotal', 0),
                    'historyId': profile.get('historyId', '')
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def _extract_body(self, payload):
        """Extract body from email payload"""
        body = ''

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return body

    def run(self):
        """Run the MCP server"""
        print("Starting Gmail MCP Server (Secondary)...", file=sys.stderr)
        print("Authenticating with Gmail API...", file=sys.stderr)

        try:
            manual_auth = getattr(self, '_manual_auth', False)
            self.authenticate(manual_auth=manual_auth)
            print("Authentication successful!", file=sys.stderr)

            # Get profile to verify connection
            try:
                profile = self.service.users().getProfile(userId='me').execute()
                print(f"Connected to: {profile.get('emailAddress')}", file=sys.stderr)
                print(f"Total messages: {profile.get('messagesTotal')}", file=sys.stderr)
                print(f"Total threads: {profile.get('threadsTotal')}", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch profile: {e}", file=sys.stderr)

            print("\nGmail MCP Server (Secondary) is ready!", file=sys.stderr)
            print("Available tools: send_email, search_emails, read_email, create_draft, and more...", file=sys.stderr)
            print("\nServer is running. Press Ctrl+C to stop.", file=sys.stderr)

            # Run the MCP server (this already handles async internally)
            self.mcp.run()

        except Exception as e:
            print(f"Error starting server: {e}", file=sys.stderr)
            raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Gmail MCP Server (Secondary)")
    parser.add_argument(
        "--manual-auth",
        action="store_true",
        help="Use manual OAuth authentication (for WSL/headless environments)"
    )
    parser.add_argument(
        "--test-auth",
        action="store_true",
        help="Test authentication and exit"
    )
    args = parser.parse_args()

    server = GmailMCPServer()

    if args.test_auth:
        print("Testing Gmail authentication (Secondary)...", file=sys.stderr)
        try:
            server.authenticate(manual_auth=args.manual_auth)
            # Get profile directly from service
            profile = server.service.users().getProfile(userId='me').execute()
            print(f"[OK] Authentication successful!", file=sys.stderr)
            print(f"[OK] Connected to: {profile['emailAddress']}", file=sys.stderr)
            print(f"[OK] Total messages: {profile.get('messagesTotal', 0)}", file=sys.stderr)
            print(f"[OK] Total threads: {profile.get('threadsTotal', 0)}", file=sys.stderr)
            print("\nGmail MCP Server is ready to use!", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Set manual auth flag for the server
        server._manual_auth = args.manual_auth
        server.run()

if __name__ == "__main__":
    main()