#!/usr/bin/env python3
"""
WSL-friendly Gmail OAuth Authentication
Handles authentication without trying to open browser
"""

import os
import json
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def main():
    creds = None

    # Check for existing token
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
            print("✓ Found existing token")

    # Check if token needs refresh
    if creds and creds.valid:
        print("✅ Token is valid! You're already authenticated.")
        return

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired token...")
        creds.refresh(Request())
    else:
        print("Starting new OAuth flow...")

        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

        # Use a fixed port for consistency
        PORT = 8080

        print("\n" + "="*60)
        print("OAUTH AUTHENTICATION REQUIRED")
        print("="*60)
        print(f"\n1. Open this URL in your browser:\n")

        # Set redirect URI
        flow.redirect_uri = f'http://localhost:{PORT}/'

        # Generate auth URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        print(auth_url)
        print(f"\n2. Authorize the application")
        print(f"3. You'll see 'Authentication successful!' message")
        print(f"4. Return here - authentication will complete automatically")
        print("="*60)

        # Start local server to receive the authorization code
        # This will wait for the redirect
        try:
            creds = flow.run_local_server(
                port=PORT,
                success_message='Authentication successful! You can close this window and return to the terminal.',
                open_browser=False  # Don't try to open browser
            )
            print("\n✓ Received authorization code!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    # Save the token
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("✅ Authentication complete! Token saved to token.json")
    print("You can now run: python3 gmail_mcp_server.py")

if __name__ == "__main__":
    main()