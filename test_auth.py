#!/usr/bin/env python3
"""
Simple authentication test script for Gmail MCP Server
This script helps verify that authentication is working correctly
"""

import asyncio
import sys
from gmail_mcp_server import GmailMCPServer

async def test_authentication():
    """Test Gmail authentication and basic functionality"""
    print("=" * 60)
    print("GMAIL MCP SERVER AUTHENTICATION TEST")
    print("=" * 60)

    # Create server instance
    server = GmailMCPServer()

    try:
        print("1. Testing authentication...")
        # Use manual auth by default for WSL environments
        server.authenticate(manual_auth=True)
        print("✓ Authentication successful!")

        print("\n2. Testing Gmail API connection...")
        profile = await server.get_profile()

        if profile['success']:
            print("✓ Gmail API connection successful!")
            print(f"   Email: {profile['emailAddress']}")
            print(f"   Messages: {profile['messagesTotal']}")
            print(f"   Threads: {profile['threadsTotal']}")
        else:
            print(f"✗ Failed to get profile: {profile.get('error')}")
            return False

        print("\n3. Testing basic email search...")
        search_result = await server.search_emails("in:inbox", max_results=5)

        if search_result['success']:
            print(f"✓ Email search successful! Found {search_result['count']} messages")
            for i, email in enumerate(search_result['emails'][:3], 1):
                print(f"   {i}. From: {email['from'][:50]}...")
                print(f"      Subject: {email['subject'][:50]}...")
        else:
            print(f"✗ Email search failed: {search_result.get('error')}")
            return False

        print("\n4. Testing label listing...")
        labels_result = await server.list_labels()

        if labels_result['success']:
            print(f"✓ Label listing successful! Found {labels_result['count']} labels")
            system_labels = [l for l in labels_result['labels'] if l['type'] == 'system'][:5]
            for label in system_labels:
                print(f"   - {label['name']} (ID: {label['id']})")
        else:
            print(f"✗ Label listing failed: {labels_result.get('error')}")
            return False

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("Gmail MCP Server is ready for use!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Authentication test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure credentials.json is in the current directory")
        print("2. Check that the OAuth client is configured correctly")
        print("3. Make sure you have internet connectivity")
        print("4. Verify the Gmail API is enabled in Google Cloud Console")
        return False

def main():
    """Main entry point"""
    success = asyncio.run(test_authentication())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()