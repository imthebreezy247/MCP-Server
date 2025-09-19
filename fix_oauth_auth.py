#!/usr/bin/env python3
"""
OAuth Authentication Fixer for Gmail MCP Server
This script helps diagnose and fix OAuth authentication issues
"""

import os
import json
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def check_credentials_file():
    """Check and validate credentials.json file"""
    print("\n=== Checking credentials.json ===")

    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("   Please download it from Google Cloud Console")
        return False

    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)

        # Check structure
        if 'installed' in creds:
            print("✅ Desktop application OAuth client detected")
            client_info = creds['installed']
        elif 'web' in creds:
            print("✅ Web application OAuth client detected")
            client_info = creds['web']
        else:
            print("❌ Unknown OAuth client type")
            return False

        # Validate required fields
        required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
        missing = [f for f in required_fields if f not in client_info]

        if missing:
            print(f"❌ Missing required fields: {', '.join(missing)}")
            return False

        print(f"✅ Client ID: {client_info['client_id'][:30]}...")
        print(f"✅ Project ID: {client_info.get('project_id', 'Not specified')}")

        # Check redirect URIs
        redirect_uris = client_info.get('redirect_uris', [])
        if not redirect_uris:
            print("⚠️  No redirect URIs found - this might cause issues")
        else:
            print(f"✅ Redirect URIs configured: {len(redirect_uris)}")
            for uri in redirect_uris[:3]:  # Show first 3
                print(f"   - {uri}")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials.json: {e}")
        return False

def test_authentication_flow():
    """Test the OAuth authentication flow"""
    print("\n=== Testing Authentication Flow ===")

    try:
        # Try to load existing token
        if os.path.exists('token.json'):
            print("Found existing token.json, checking validity...")
            with open('token.json', 'r') as token:
                creds_data = json.load(token)
                creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

            if creds and creds.valid:
                print("✅ Existing token is valid!")
                return test_gmail_connection(creds)
            elif creds and creds.expired and creds.refresh_token:
                print("Token expired, attempting refresh...")
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully!")
                    save_token(creds)
                    return test_gmail_connection(creds)
                except Exception as e:
                    print(f"❌ Failed to refresh token: {e}")
                    print("Will need to re-authenticate...")

        # Need new authentication
        print("\n Starting new authentication flow...")
        print("=" * 60)

        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)

        # Try different authentication methods
        print("\nAttempting automatic browser authentication...")
        print("(If a browser doesn't open, we'll fall back to manual mode)")

        try:
            # Try automatic flow with port 0 (random available port)
            creds = flow.run_local_server(
                port=0,
                authorization_prompt_message='Please visit this URL to authorize: {url}',
                success_message='Authentication successful! You can close this window.',
                open_browser=True
            )
            print("✅ Authentication successful via browser!")

        except Exception as e:
            print(f"\n⚠️  Automatic authentication failed: {e}")
            print("\nFalling back to manual authentication...")
            print("=" * 60)

            # Manual flow
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='consent'
            )

            print("\n📋 MANUAL AUTHENTICATION REQUIRED")
            print("=" * 60)
            print("1. Open this URL in your browser:\n")
            print(auth_url)
            print("\n2. Sign in with your Google account")
            print("3. Grant permissions to Gmail MCP Server")
            print("4. Copy the authorization code shown")
            print("5. Paste it below")
            print("=" * 60)

            auth_code = input("\nEnter authorization code: ").strip()

            if not auth_code:
                print("❌ No authorization code provided")
                return False

            try:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                print("✅ Manual authentication successful!")
            except Exception as e:
                print(f"❌ Failed to exchange authorization code: {e}")
                return False

        # Save credentials
        save_token(creds)
        return test_gmail_connection(creds)

    except FileNotFoundError:
        print("❌ credentials.json not found!")
        return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("\nPossible causes:")
        print("- Invalid credentials.json file")
        print("- OAuth client misconfiguration in Google Cloud Console")
        print("- Network connectivity issues")
        return False

def save_token(creds):
    """Save credentials to token.json"""
    try:
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved to token.json")
    except Exception as e:
        print(f"⚠️  Failed to save token: {e}")

def test_gmail_connection(creds):
    """Test the Gmail API connection"""
    print("\n=== Testing Gmail API Connection ===")

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Get user profile
        profile = service.users().getProfile(userId='me').execute()

        print("✅ Successfully connected to Gmail!")
        print(f"   Email: {profile['emailAddress']}")
        print(f"   Total messages: {profile.get('messagesTotal', 0)}")
        print(f"   Total threads: {profile.get('threadsTotal', 0)}")

        # Try to list some labels as additional test
        labels = service.users().labels().list(userId='me').execute()
        print(f"   Available labels: {len(labels.get('labels', []))}")

        return True

    except HttpError as e:
        print(f"❌ Gmail API error: {e}")
        if e.resp.status == 403:
            print("   Possible cause: Gmail API not enabled or insufficient permissions")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("Gmail MCP Server - OAuth Authentication Diagnostic Tool")
    print("=" * 60)

    # Check credentials file
    if not check_credentials_file():
        print("\n❌ Please fix credentials.json issues first")
        sys.exit(1)

    # Test authentication
    if test_authentication_flow():
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Gmail authentication is working!")
        print("=" * 60)
        print("\nYou can now run the Gmail MCP Server:")
        print("  python3 gmail_mcp_server.py")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Authentication failed!")
        print("=" * 60)
        print("\nTroubleshooting steps:")
        print("1. Check the OAuth consent screen configuration in Google Cloud Console")
        print("2. Verify redirect URIs are properly configured")
        print("3. Ensure Gmail API is enabled")
        print("4. Try creating a new OAuth client")
        print("\nRefer to fix_oauth_guide.md for detailed instructions")
        sys.exit(1)

if __name__ == "__main__":
    main()