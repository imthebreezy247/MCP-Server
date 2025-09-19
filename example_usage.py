#!/usr/bin/env python3
"""
Example usage of Gmail MCP Server
Demonstrates common Gmail operations
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_mcp_server import GmailMCPServer


async def demonstrate_gmail_operations():
    """Demonstrate common Gmail operations"""

    # Initialize the server
    server = GmailMCPServer()

    print("🚀 Gmail MCP Server Example")
    print("=" * 50)

    # Authenticate
    try:
        server.authenticate()
        print("✓ Authentication successful")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Get profile information
    print("\n📊 Getting profile information...")
    profile = await server.get_profile()
    if profile['success']:
        print(f"✓ Email: {profile['emailAddress']}")
        print(f"✓ Total messages: {profile['messagesTotal']}")
        print(f"✓ Total threads: {profile['threadsTotal']}")

    # List existing labels
    print("\n🏷️  Listing Gmail labels...")
    labels_result = await server.list_labels()
    if labels_result['success']:
        print(f"✓ Found {labels_result['count']} labels:")
        for label in labels_result['labels'][:5]:  # Show first 5
            print(f"   - {label['name']} ({label['type']})")

    # Search for unread emails
    print("\n🔍 Searching for unread emails...")
    search_result = await server.search_emails(
        query="is:unread",
        max_results=5
    )
    if search_result['success']:
        print(f"✓ Found {search_result['count']} unread emails:")
        for email in search_result['emails']:
            print(f"   From: {email['from'][:50]}...")
            print(f"   Subject: {email['subject'][:50]}...")
            print(f"   Date: {email['date']}")
            print()

    # Search for emails with attachments
    print("\n📎 Searching for emails with attachments...")
    attachment_search = await server.search_emails(
        query="has:attachment",
        max_results=3
    )
    if attachment_search['success']:
        print(f"✓ Found {attachment_search['count']} emails with attachments")

    # Search in sent folder
    print("\n📤 Checking sent emails...")
    sent_search = await server.search_emails(
        query="in:sent",
        max_results=3
    )
    if sent_search['success']:
        print(f"✓ Found {sent_search['count']} sent emails")

    # Create a test label (optional - uncomment to test)
    # print("\n🆕 Creating test label...")
    # from datetime import datetime
    # test_label = f"MCP_Example_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # label_result = await server.create_label(name=test_label)
    # if label_result['success']:
    #     print(f"✓ Created label: {label_result['name']}")

    # Create a draft email (optional - uncomment to test)
    # print("\n✉️  Creating test draft...")
    # if profile['success']:
    #     draft_result = await server.create_draft(
    #         to=profile['emailAddress'],  # Send to self
    #         subject="Gmail MCP Server Test Draft",
    #         body="This is a test draft created by the Gmail MCP Server example script.\n\nYou can safely delete this draft.",
    #         html=False
    #     )
    #     if draft_result['success']:
    #         print(f"✓ Draft created with ID: {draft_result['draftId']}")

    # Advanced search examples
    print("\n🎯 Advanced search examples...")

    # Search for important emails
    important_search = await server.search_emails(
        query="is:important",
        max_results=2
    )
    if important_search['success']:
        print(f"✓ Found {important_search['count']} important emails")

    # Search for recent emails from a specific domain
    recent_search = await server.search_emails(
        query="newer_than:7d from:gmail.com",
        max_results=2
    )
    if recent_search['success']:
        print(f"✓ Found {recent_search['count']} recent emails from gmail.com")

    print("\n" + "=" * 50)
    print("🎉 Example completed successfully!")
    print("\nNext steps:")
    print("1. Review the code in example_usage.py")
    print("2. Uncomment optional sections to test draft creation")
    print("3. Run test_gmail_mcp.py for interactive testing")
    print("4. Read SETUP_GUIDE.md for advanced configuration")


async def interactive_example():
    """Interactive example with user prompts"""
    server = GmailMCPServer()

    print("🤖 Interactive Gmail MCP Server Example")
    print("=" * 50)

    # Authenticate
    try:
        server.authenticate()
        print("✓ Authentication successful")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Get user's email
    profile = await server.get_profile()
    if not profile['success']:
        print("✗ Could not get profile")
        return

    user_email = profile['emailAddress']
    print(f"✓ Authenticated as: {user_email}")

    # Ask what they want to do
    print("\nWhat would you like to do?")
    print("1. Search emails")
    print("2. Create a draft")
    print("3. List labels")
    print("4. Create a label")
    print("5. Show profile info")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        query = input("Enter search query (e.g., 'is:unread', 'from:someone@example.com'): ").strip()
        if query:
            result = await server.search_emails(query=query, max_results=10)
            if result['success']:
                print(f"\n✓ Found {result['count']} emails:")
                for email in result['emails']:
                    print(f"\n  From: {email['from']}")
                    print(f"  Subject: {email['subject']}")
                    print(f"  Date: {email['date']}")
                    print(f"  Snippet: {email['snippet'][:100]}...")
            else:
                print(f"✗ Search failed: {result['error']}")

    elif choice == "2":
        to = input("To (leave empty to send to yourself): ").strip()
        if not to:
            to = user_email

        subject = input("Subject: ").strip()
        body = input("Message body: ").strip()

        if subject and body:
            result = await server.create_draft(to=to, subject=subject, body=body)
            if result['success']:
                print(f"✓ Draft created successfully!")
                print(f"  Draft ID: {result['draftId']}")
            else:
                print(f"✗ Failed to create draft: {result['error']}")
        else:
            print("✗ Subject and body are required")

    elif choice == "3":
        result = await server.list_labels()
        if result['success']:
            print(f"\n✓ Found {result['count']} labels:")
            for label in result['labels']:
                print(f"  - {label['name']} ({label['type']})")
        else:
            print(f"✗ Failed to list labels: {result['error']}")

    elif choice == "4":
        name = input("Label name (use '/' for nested labels): ").strip()
        if name:
            result = await server.create_label(name=name)
            if result['success']:
                print(f"✓ Label '{result['name']}' created successfully!")
                print(f"  Label ID: {result['labelId']}")
            else:
                print(f"✗ Failed to create label: {result['error']}")
        else:
            print("✗ Label name is required")

    elif choice == "5":
        print(f"\n📊 Profile Information:")
        print(f"  Email: {profile['emailAddress']}")
        print(f"  Total Messages: {profile['messagesTotal']}")
        print(f"  Total Threads: {profile['threadsTotal']}")
        print(f"  History ID: {profile['historyId']}")

    else:
        print("Invalid choice")


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_example()
    else:
        await demonstrate_gmail_operations()


if __name__ == "__main__":
    print("Gmail MCP Server - Example Usage")
    print("===============================")
    print("\nUsage:")
    print("  python example_usage.py              # Run demonstration")
    print("  python example_usage.py --interactive # Interactive mode")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed: {e}")
        sys.exit(1)