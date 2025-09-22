#!/usr/bin/env python3
"""
Simple Gmail OAuth Authentication Script
Handles the OAuth flow properly for Desktop clients
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'

def authenticate():
    """Simple authentication with proper redirect URI"""
    creds = None

    # Check for existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
            print("✓ Using existing token")

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Starting OAuth flow...")

            # Create flow from credentials file
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)

            # Try local server method first (works in most environments)
            try:
                print("Attempting automatic authentication...")
                print("A browser window should open. If it doesn't, use the URL shown.")
                creds = flow.run_local_server(
                    port=8080,
                    success_message='Authentication successful! You can close this window.',
                    open_browser=True
                )
                print("✓ Authentication successful!")
            except Exception as e:
                print(f"\nAutomatic authentication failed: {e}")
                print("\n" + "="*60)
                print("MANUAL AUTHENTICATION REQUIRED")
                print("="*60)

                # Manual flow with proper redirect URI
                flow.redirect_uri = 'http://localhost:8080'

                # Generate authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    prompt='consent'
                )

                print("\n1. Open this URL in your browser:")
                print(f"\n{auth_url}\n")
                print("2. Sign in and authorize the application")
                print("3. You'll see an error page (localhost refused to connect)")
                print("4. Look at the URL bar - it will contain: http://localhost:8080/?code=...")
                print("5. Copy the ENTIRE URL from your browser")
                print("="*60)

                # Get the redirect URL
                redirect_url = input("\nPaste the entire URL here: ").strip()

                # Parse the authorization code
                if 'code=' in redirect_url:
                    # Extract code from URL
                    import urllib.parse
                    parsed = urllib.parse.urlparse(redirect_url)
                    params = urllib.parse.parse_qs(parsed.query)
                    auth_code = params.get('code', [None])[0]

                    if not auth_code:
                        print("Error: Could not extract authorization code from URL")
                        return None
                else:
                    # Assume they just pasted the code directly
                    auth_code = redirect_url

                print(f"Using authorization code: {auth_code[:20]}...")

                # Exchange code for token
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                print("✓ Authentication successful!")

    # Save credentials
    if creds:
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            print(f"✓ Token saved to {TOKEN_PATH}")

    return creds

if __name__ == "__main__":
    print("Gmail OAuth Authentication Setup")
    print("-" * 40)

    # Check for credentials file
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERROR: {CREDENTIALS_PATH} not found!")
        print("Please download your OAuth client credentials from Google Cloud Console")
        exit(1)

    # Load and check credentials format
    with open(CREDENTIALS_PATH, 'r') as f:
        cred_data = json.load(f)
        if 'installed' not in cred_data:
            print("ERROR: credentials.json must be a Desktop (installed) client!")
            print("Current format:", list(cred_data.keys()))
            print("Please use a Desktop OAuth client from Google Cloud Console")
            exit(1)

    # Perform authentication
    creds = authenticate()

    if creds:
        print("\n✅ Authentication complete!")
        print("You can now run: python3 gmail_mcp_server.py")
    else:
        print("\n❌ Authentication failed!")
        print("Please check your credentials and try again")