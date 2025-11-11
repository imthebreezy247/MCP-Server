#!/usr/bin/env python3
"""
OAuth Credentials Setup Helper for Gmail API
Helps you set up OAuth 2.0 credentials for accessing Gmail accounts
"""

import json
import os
import sys
from pathlib import Path
import webbrowser

SCRIPT_DIR = Path(__file__).parent.absolute()
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80)


def create_sample_credentials():
    """Create a sample credentials.json structure for manual editing"""
    sample = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-name",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    return sample


def main():
    print_section("GMAIL OAUTH CREDENTIALS SETUP")

    print("\nThis helper will guide you through setting up OAuth credentials for Gmail API access.")

    # Check if credentials already exist
    if CREDENTIALS_FILE.exists():
        print(f"\n✓ Found existing credentials file: {CREDENTIALS_FILE}")
        response = input("\nDo you want to replace it? (y/n): ").strip().lower()
        if response != 'y':
            print("Keeping existing credentials. Setup complete!")
            return

    print("\n" + "-"*80)
    print("\nSTEP-BY-STEP INSTRUCTIONS TO GET OAUTH CREDENTIALS")
    print("-"*80)

    print("\n1. OPEN GOOGLE CLOUD CONSOLE")
    print("   Go to: https://console.cloud.google.com/")
    input("\n   Press Enter when you have opened the console...")

    print("\n2. CREATE OR SELECT A PROJECT")
    print("   - Click on the project dropdown at the top")
    print("   - Select an existing project OR click 'New Project'")
    print("   - If creating new: Give it a name like 'Gmail-MCP-Server'")
    input("\n   Press Enter when you have a project selected...")

    print("\n3. ENABLE GMAIL API")
    print("   - In the left menu, go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Gmail API'")
    print("   - Click on 'Gmail API'")
    print("   - Click the 'ENABLE' button")
    input("\n   Press Enter when Gmail API is enabled...")

    print("\n4. CREATE OAUTH 2.0 CREDENTIALS")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click '+ CREATE CREDENTIALS' at the top")
    print("   - Select 'OAuth client ID'")
    input("\n   Press Enter to continue...")

    print("\n5. CONFIGURE OAUTH CONSENT SCREEN (if prompted)")
    print("   - Choose 'External' user type")
    print("   - Fill in required fields:")
    print("     * App name: 'Gmail MCP Server'")
    print("     * User support email: Your email")
    print("     * Developer contact: Your email")
    print("   - Add scopes: gmail.modify and gmail.readonly")
    print("   - Add your email addresses as test users")
    input("\n   Press Enter when consent screen is configured...")

    print("\n6. CREATE OAUTH CLIENT")
    print("   - Application type: Select 'Desktop app'")
    print("   - Name: 'Gmail MCP Client' (or any name you prefer)")
    print("   - Click 'CREATE'")
    input("\n   Press Enter when the client is created...")

    print("\n7. DOWNLOAD CREDENTIALS")
    print("   - You should see a dialog with your client ID and secret")
    print("   - Click 'DOWNLOAD JSON' button")
    print("   - Save the file to your computer")
    print("\n" + "-"*80)

    print("\nNow, let's add your credentials to this project:")
    print("\nChoose an option:")
    print("1. Paste the entire JSON content here")
    print("2. Enter client_id and client_secret manually")
    print("3. I'll copy the file myself")

    choice = input("\nYour choice (1-3): ").strip()

    if choice == "1":
        print("\nPaste the entire JSON content (press Ctrl+D or Ctrl+Z when done):")
        try:
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break

            json_content = '\n'.join(lines)
            credentials = json.loads(json_content)

            with open(CREDENTIALS_FILE, 'w') as f:
                json.dump(credentials, f, indent=2)

            print(f"\n✓ Credentials saved to: {CREDENTIALS_FILE}")

        except json.JSONDecodeError as e:
            print(f"\nError: Invalid JSON format - {e}")
            print("Please try again or use option 2 or 3.")
            return
        except Exception as e:
            print(f"\nError saving credentials: {e}")
            return

    elif choice == "2":
        print("\nEnter your OAuth credentials:")
        client_id = input("Client ID (ends with .apps.googleusercontent.com): ").strip()
        client_secret = input("Client Secret: ").strip()
        project_id = input("Project ID (optional, press Enter to skip): ").strip()

        if not client_id or not client_secret:
            print("\nError: Client ID and Client Secret are required!")
            return

        credentials = {
            "installed": {
                "client_id": client_id,
                "project_id": project_id or "gmail-mcp-server",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }

        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)

        print(f"\n✓ Credentials saved to: {CREDENTIALS_FILE}")

    elif choice == "3":
        # Create a sample file for manual editing
        sample = create_sample_credentials()
        sample_file = SCRIPT_DIR / "credentials_sample.json"

        with open(sample_file, 'w') as f:
            json.dump(sample, f, indent=2)

        print(f"\n✓ Created sample file: {sample_file}")
        print(f"\nPlease:")
        print(f"1. Copy your downloaded JSON file to: {CREDENTIALS_FILE}")
        print(f"   OR")
        print(f"2. Edit {sample_file} with your credentials and rename it to 'credentials.json'")
        return

    else:
        print("\nInvalid choice. Please run the script again.")
        return

    print_section("SETUP COMPLETE!")

    print("\n✓ OAuth credentials are now configured!")
    print("\nYou can now run the extraction script:")
    print(f"  python3 extract_sold_deals_multi_account.py")
    print("\nNote: You'll need to authenticate each Gmail account on first use.")
    print("The script will guide you through the authentication process for each account.")

    # Try to open the direct link for creating credentials
    print("\n" + "-"*80)
    print("\nHelpful direct link (Ctrl+Click to open):")
    print("https://console.cloud.google.com/apis/credentials")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)