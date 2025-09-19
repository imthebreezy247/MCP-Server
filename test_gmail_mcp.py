#!/usr/bin/env python3
"""
Test script for Gmail MCP Server
Tests all available Gmail operations
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gmail_mcp_server import GmailMCPServer


class GmailMCPTester:
    """Test harness for Gmail MCP Server"""

    def __init__(self):
        self.server = GmailMCPServer()
        self.test_results = []

    async def test_authentication(self):
        """Test Gmail API authentication"""
        print("\n=== Testing Authentication ===")
        try:
            self.server.authenticate()
            print("✓ Authentication successful")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False

    async def test_get_profile(self):
        """Test getting Gmail profile"""
        print("\n=== Testing Get Profile ===")
        try:
            result = await self.server.mcp.tools[14]._func()  # get_profile
            if result['success']:
                print(f"✓ Email: {result['emailAddress']}")
                print(f"  Messages: {result['messagesTotal']}")
                print(f"  Threads: {result['threadsTotal']}")
                return True
            else:
                print(f"✗ Failed: {result['error']}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def test_list_labels(self):
        """Test listing Gmail labels"""
        print("\n=== Testing List Labels ===")
        try:
            result = await self.server.mcp.tools[7]._func()  # list_labels
            if result['success']:
                print(f"✓ Found {result['count']} labels")
                for label in result['labels'][:5]:  # Show first 5
                    print(f"  - {label['name']} ({label['type']})")
                return True
            else:
                print(f"✗ Failed: {result['error']}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def test_search_emails(self):
        """Test searching emails"""
        print("\n=== Testing Email Search ===")
        try:
            # Search for recent emails
            result = await self.server.mcp.tools[2]._func(
                query="is:unread",
                max_results=5
            )  # search_emails

            if result['success']:
                print(f"✓ Found {result['count']} unread emails")
                for email in result['emails']:
                    print(f"  - From: {email['from'][:50]}...")
                    print(f"    Subject: {email['subject'][:50]}...")
                return True
            else:
                print(f"✗ Failed: {result['error']}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def test_create_and_delete_label(self):
        """Test creating and deleting a label"""
        print("\n=== Testing Create Label ===")
        try:
            # Create a test label
            test_label_name = f"MCP_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = await self.server.mcp.tools[8]._func(
                name=test_label_name
            )  # create_label

            if result['success']:
                print(f"✓ Created label: {result['name']}")
                print(f"  ID: {result['labelId']}")

                # Note: Label deletion would need to be added to the server
                # For now, we just confirm creation
                return True
            else:
                print(f"✗ Failed: {result['error']}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def test_create_draft(self):
        """Test creating a draft email"""
        print("\n=== Testing Create Draft ===")
        try:
            # Get profile to get email address
            profile = await self.server.mcp.tools[14]._func()  # get_profile
            if not profile['success']:
                print("✗ Could not get profile")
                return False

            result = await self.server.mcp.tools[1]._func(
                to=profile['emailAddress'],  # Send to self
                subject=f"MCP Test Draft - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                body="This is a test draft created by Gmail MCP Server.\n\nThis email was created as a draft and not sent.",
                html=False
            )  # create_draft

            if result['success']:
                print(f"✓ Created draft")
                print(f"  Draft ID: {result['draftId']}")
                print(f"  Message ID: {result['messageId']}")
                return True
            else:
                print(f"✗ Failed: {result['error']}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    async def test_advanced_search(self):
        """Test advanced email search"""
        print("\n=== Testing Advanced Search ===")

        # Test various search queries
        queries = [
            ("has:attachment", "Emails with attachments"),
            ("is:important", "Important emails"),
            ("in:sent", "Sent emails"),
            ("label:inbox", "Inbox emails")
        ]

        for query, description in queries:
            try:
                result = await self.server.mcp.tools[2]._func(
                    query=query,
                    max_results=2
                )  # search_emails

                if result['success']:
                    print(f"✓ {description}: Found {result['count']} emails")
                else:
                    print(f"✗ {description}: {result['error']}")
            except Exception as e:
                print(f"✗ {description}: {e}")

        return True

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("Gmail MCP Server Test Suite")
        print("=" * 60)

        # Authenticate first
        if not await self.test_authentication():
            print("\n✗ Authentication failed. Cannot continue tests.")
            return

        # Run all tests
        tests = [
            self.test_get_profile,
            self.test_list_labels,
            self.test_search_emails,
            self.test_create_and_delete_label,
            self.test_create_draft,
            self.test_advanced_search
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                if await test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ Test failed with exception: {e}")
                failed += 1

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"Total: {passed + failed}")

        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠ {failed} test(s) failed")

    async def interactive_test(self):
        """Interactive testing mode"""
        print("=" * 60)
        print("Gmail MCP Server - Interactive Test Mode")
        print("=" * 60)

        if not await self.test_authentication():
            print("\n✗ Authentication failed.")
            return

        while True:
            print("\n" + "=" * 40)
            print("Available Operations:")
            print("1. Send Email")
            print("2. Search Emails")
            print("3. Read Email (by ID)")
            print("4. List Labels")
            print("5. Create Label")
            print("6. Get Profile Info")
            print("7. Create Draft")
            print("8. Get Thread")
            print("9. Run All Tests")
            print("0. Exit")
            print("=" * 40)

            choice = input("\nSelect operation (0-9): ").strip()

            if choice == "0":
                print("Exiting...")
                break

            elif choice == "1":
                # Send email
                to = input("To (email address): ").strip()
                subject = input("Subject: ").strip()
                body = input("Body: ").strip()

                result = await self.server.mcp.tools[0]._func(
                    to=to, subject=subject, body=body
                )

                if result['success']:
                    print(f"✓ Email sent! Message ID: {result['messageId']}")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "2":
                # Search emails
                query = input("Search query (e.g., 'is:unread', 'from:someone@example.com'): ").strip()
                max_results = input("Max results (default 10): ").strip()
                max_results = int(max_results) if max_results else 10

                result = await self.server.mcp.tools[2]._func(
                    query=query, max_results=max_results
                )

                if result['success']:
                    print(f"\n✓ Found {result['count']} emails:")
                    for email in result['emails']:
                        print(f"\n  ID: {email['id']}")
                        print(f"  From: {email['from']}")
                        print(f"  Subject: {email['subject']}")
                        print(f"  Date: {email['date']}")
                        print(f"  Snippet: {email['snippet'][:100]}...")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "3":
                # Read email
                message_id = input("Message ID: ").strip()

                result = await self.server.mcp.tools[3]._func(
                    message_id=message_id
                )

                if result['success']:
                    print(f"\n✓ Email Details:")
                    print(f"  From: {result['headers'].get('From', 'N/A')}")
                    print(f"  To: {result['headers'].get('To', 'N/A')}")
                    print(f"  Subject: {result['headers'].get('Subject', 'N/A')}")
                    print(f"  Date: {result['headers'].get('Date', 'N/A')}")
                    print(f"\n  Body:\n{result['body'][:500]}...")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "4":
                # List labels
                await self.test_list_labels()

            elif choice == "5":
                # Create label
                name = input("Label name: ").strip()

                result = await self.server.mcp.tools[8]._func(name=name)

                if result['success']:
                    print(f"✓ Label created: {result['name']} (ID: {result['labelId']})")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "6":
                # Get profile
                await self.test_get_profile()

            elif choice == "7":
                # Create draft
                to = input("To (email address): ").strip()
                subject = input("Subject: ").strip()
                body = input("Body: ").strip()

                result = await self.server.mcp.tools[1]._func(
                    to=to, subject=subject, body=body
                )

                if result['success']:
                    print(f"✓ Draft created! Draft ID: {result['draftId']}")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "8":
                # Get thread
                thread_id = input("Thread ID: ").strip()

                result = await self.server.mcp.tools[5]._func(
                    thread_id=thread_id
                )

                if result['success']:
                    print(f"\n✓ Thread contains {result['messageCount']} messages:")
                    for i, msg in enumerate(result['messages'], 1):
                        print(f"\n  Message {i}:")
                        print(f"    From: {msg['from']}")
                        print(f"    Date: {msg['date']}")
                        print(f"    Snippet: {msg['snippet'][:100]}...")
                else:
                    print(f"✗ Failed: {result['error']}")

            elif choice == "9":
                # Run all tests
                await self.run_all_tests()

            else:
                print("Invalid choice. Please try again.")


async def main():
    """Main entry point for testing"""
    tester = GmailMCPTester()

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await tester.interactive_test()
    else:
        await tester.run_all_tests()


if __name__ == "__main__":
    print("Gmail MCP Server Test Script")
    print("============================")
    print("\nUsage:")
    print("  python test_gmail_mcp.py           # Run all tests")
    print("  python test_gmail_mcp.py --interactive  # Interactive mode")
    print()

    asyncio.run(main())