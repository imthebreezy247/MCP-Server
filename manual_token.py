#!/usr/bin/env python3
"""
Manual token creation from authorization code
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

def create_token_from_code():
    print("Manual Token Creation")
    print("-" * 30)

    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        ['https://www.googleapis.com/auth/gmail.modify']
    )

    # Set redirect URI
    flow.redirect_uri = 'http://localhost:8080/'

    print("\n1. Open this URL in your browser:")
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    print(f"\n{auth_url}\n")

    print("2. After authorizing, copy the authorization code from the URL")
    print("   (the part after 'code=' in the redirect URL)")

    # Get authorization code from user
    auth_code = input("\nEnter the authorization code: ").strip()

    # Exchange code for token
    try:
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Save token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

        print("✅ Token created successfully!")
        print("You can now run: python3 gmail_mcp_server.py")

    except Exception as e:
        print(f"❌ Error creating token: {e}")

if __name__ == "__main__":
    create_token_from_code()