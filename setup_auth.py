#!/usr/bin/env python3
"""
Interactive OAuth Setup for Gmail MCP Server
This script handles the initial OAuth authentication in WSL/headless environments
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'

def setup_authentication():
    """Set up Gmail OAuth authentication"""
    print("=" * 70)
    print("GMAIL MCP SERVER - OAUTH AUTHENTICATION SETUP")
    print("=" * 70)

    # Check for existing token
    if os.path.exists(TOKEN_PATH):
        print(f"✓ Found existing token file: {TOKEN_PATH}")

        # Verify the token works
        try:
            with open(TOKEN_PATH, 'r') as token:
                creds_data = json.load(token)
                creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

            if creds.valid:
                print("✓ Existing credentials are valid!")
                service = build('gmail', 'v1', credentials=creds)
                profile = service.users().getProfile(userId='me').execute()
                print(f"✓ Connected to: {profile['emailAddress']}")
                print(f"✓ Total messages: {profile.get('messagesTotal', 0)}")
                print("\n✅ Authentication already set up! No action needed.")
                return True
            else:
                print("⚠ Existing credentials are expired or invalid")
                print("Starting fresh authentication process...")
        except Exception as e:
            print(f"⚠ Error reading existing token: {e}")
            print("Starting fresh authentication process...")

    # Check for credentials file
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\n❌ Error: Missing {CREDENTIALS_PATH}")
        print("\nPlease:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com)")
        print("2. Enable the Gmail API")
        print("3. Create OAuth 2.0 credentials (Desktop Application)")
        print("4. Download the credentials as 'credentials.json'")
        print("5. Place credentials.json in this directory")
        return False

    print(f"✓ Found credentials file: {CREDENTIALS_PATH}")

    # Start manual OAuth flow
    try:
        print("\n🔐 Starting OAuth authentication process...")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)

        # Generate authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')

        print("\n" + "=" * 70)
        print("STEP 1: AUTHORIZE IN BROWSER")
        print("=" * 70)
        print("Please follow these steps:")
        print("\n1. Copy this URL and open it in your web browser:")
        print(f"\n{auth_url}")
        print("\n2. Sign in to your Google account")
        print("3. Review and accept the permissions")
        print("4. Copy the authorization code shown on the success page")
        print("=" * 70)

        # Get authorization code from user
        print("\nSTEP 2: ENTER AUTHORIZATION CODE")
        while True:
            auth_code = input("\nPaste the authorization code here: ").strip()
            if auth_code:
                break
            print("Please enter a valid authorization code.")

        print("\n🔄 Exchanging authorization code for access token...")

        # Exchange code for credentials
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Save credentials
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

        print(f"✅ Credentials saved to {TOKEN_PATH}")

        # Test the connection
        print("\n🔍 Testing Gmail API connection...")
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()

        print("\n" + "=" * 70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("=" * 70)
        print(f"Connected to: {profile['emailAddress']}")
        print(f"Total messages: {profile.get('messagesTotal', 0)}")
        print(f"Total threads: {profile.get('threadsTotal', 0)}")
        print("\nYour Gmail MCP Server is now ready to use!")
        print("\nNext steps:")
        print("• Run: python3 gmail_mcp_server.py --test-auth")
        print("• Or: python3 gmail_mcp_server.py (to start the MCP server)")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")

        # Clean up invalid token if created
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
            print(f"Removed invalid token file: {TOKEN_PATH}")

        print("\n🔧 Troubleshooting tips:")
        print("• Make sure you copied the complete authorization code")
        print("• Check your internet connection")
        print("• Verify the OAuth client is configured as 'Desktop Application'")
        print("• Ensure the Gmail API is enabled in Google Cloud Console")
        print("• Try running the setup again")

        return False

def main():
    """Main entry point"""
    try:
        success = setup_authentication()
        if not success:
            print("\n❌ Setup failed. Please check the instructions above.")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹ Setup cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()