#!/usr/bin/env python3
"""
Update credentials.json with proper redirect URIs for OAuth flow
This fixes common OAuth 400 errors
"""

import json
import sys
import shutil
from datetime import datetime

def update_redirect_uris():
    """Update redirect URIs in credentials.json to fix OAuth issues"""

    print("Updating credentials.json with proper redirect URIs...")

    try:
        # Backup original file
        backup_name = f"credentials.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2('credentials.json', backup_name)
        print(f"✅ Created backup: {backup_name}")

        # Load credentials
        with open('credentials.json', 'r') as f:
            creds = json.load(f)

        # Determine client type and update redirect URIs
        if 'installed' in creds:
            print("Desktop application client detected")

            # Update redirect URIs for desktop app
            creds['installed']['redirect_uris'] = [
                "http://localhost",
                "http://localhost:8080",
                "http://localhost:8080/",
                "http://127.0.0.1",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8080/",
                "urn:ietf:wg:oauth:2.0:oob",
                "urn:ietf:wg:oauth:2.0:oob:auto"
            ]

            print("✅ Updated redirect URIs for desktop application")

        elif 'web' in creds:
            print("Web application client detected")

            # For web app, we need different URIs
            if 'redirect_uris' not in creds['web']:
                creds['web']['redirect_uris'] = []

            creds['web']['redirect_uris'] = [
                "http://localhost:8080",
                "http://localhost:8080/",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8080/"
            ]

            print("✅ Updated redirect URIs for web application")
        else:
            print("❌ Unknown client type in credentials.json")
            return False

        # Save updated credentials
        with open('credentials.json', 'w') as f:
            json.dump(creds, f, indent=2)

        print("✅ Successfully updated credentials.json")
        print("\nUpdated redirect URIs:")

        if 'installed' in creds:
            for uri in creds['installed']['redirect_uris']:
                print(f"  - {uri}")
        elif 'web' in creds:
            for uri in creds['web']['redirect_uris']:
                print(f"  - {uri}")

        print("\n⚠️  IMPORTANT: You must also update these URIs in Google Cloud Console!")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Navigate to: APIs & Services → Credentials")
        print("3. Click on your OAuth 2.0 Client ID")
        print("4. Add all the URIs listed above to 'Authorized redirect URIs'")
        print("5. Click 'SAVE'")

        return True

    except FileNotFoundError:
        print("❌ credentials.json not found!")
        print("Please download it from Google Cloud Console first")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error updating credentials: {e}")
        return False

def main():
    print("Gmail MCP Server - Credentials Update Tool")
    print("=" * 60)

    if update_redirect_uris():
        print("\n✅ Credentials updated successfully!")
        print("\nNext steps:")
        print("1. Update the redirect URIs in Google Cloud Console (see above)")
        print("2. Delete token.json if it exists: rm -f token.json")
        print("3. Run the authentication test: python3 fix_oauth_auth.py")
    else:
        print("\n❌ Failed to update credentials")
        sys.exit(1)

if __name__ == "__main__":
    main()