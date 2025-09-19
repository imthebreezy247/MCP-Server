#!/usr/bin/env python3
"""
Gmail MCP Server Installation Helper
Assists with initial setup and configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path


class GmailMCPInstaller:
    """Installation helper for Gmail MCP Server"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.requirements_file = self.project_dir / "requirements.txt"
        self.credentials_file = self.project_dir / "credentials.json"
        self.token_file = self.project_dir / "token.json"

    def print_header(self):
        """Print installation header"""
        print("=" * 60)
        print("📧 Gmail MCP Server Installation Helper")
        print("=" * 60)
        print()

    def check_python_version(self):
        """Check Python version"""
        print("🐍 Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"✗ Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True

    def install_dependencies(self):
        """Install required packages"""
        print("\n📦 Installing dependencies...")

        if not self.requirements_file.exists():
            print("✗ requirements.txt not found")
            return False

        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
            ])
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False

    def check_credentials(self):
        """Check for OAuth credentials"""
        print("\n🔑 Checking OAuth credentials...")

        if self.credentials_file.exists():
            try:
                with open(self.credentials_file) as f:
                    data = json.load(f)
                    if 'installed' in data or 'web' in data:
                        print("✓ Valid credentials.json found")
                        return True
                    else:
                        print("✗ Invalid credentials.json format")
                        return False
            except json.JSONDecodeError:
                print("✗ Invalid JSON in credentials.json")
                return False
        else:
            print("✗ credentials.json not found")
            return False

    def guide_oauth_setup(self):
        """Guide user through OAuth setup"""
        print("\n🔧 OAuth Setup Required")
        print("-" * 30)
        print("To use Gmail MCP Server, you need OAuth 2.0 credentials.")
        print("\nFollow these steps:")
        print("\n1. Go to Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print("\n2. Create or select a project")
        print("\n3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API'")
        print("   - Click 'Enable'")
        print("\n4. Create OAuth 2.0 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("   - Choose 'Desktop application'")
        print("   - Download the JSON file")
        print(f"\n5. Save the file as: {self.credentials_file}")
        print("\nPress Enter after completing these steps...")
        input()

    def test_authentication(self):
        """Test Gmail authentication"""
        print("\n🔐 Testing authentication...")

        try:
            # Import here to ensure dependencies are installed
            from gmail_mcp_server import GmailMCPServer

            server = GmailMCPServer()
            server.authenticate()
            print("✓ Authentication successful!")

            # Test basic operations
            import asyncio

            async def test_basic_ops():
                profile = await server.get_profile()
                if profile['success']:
                    print(f"✓ Connected as: {profile['emailAddress']}")
                    print(f"✓ Messages: {profile['messagesTotal']}")
                    return True
                return False

            result = asyncio.run(test_basic_ops())
            return result

        except ImportError as e:
            print(f"✗ Import error: {e}")
            print("Please ensure all dependencies are installed")
            return False
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False

    def run_tests(self):
        """Run the test suite"""
        print("\n🧪 Running tests...")

        test_file = self.project_dir / "test_gmail_mcp.py"
        if not test_file.exists():
            print("✗ test_gmail_mcp.py not found")
            return False

        try:
            subprocess.check_call([sys.executable, str(test_file)])
            print("✓ All tests passed!")
            return True
        except subprocess.CalledProcessError:
            print("✗ Some tests failed")
            return False

    def show_next_steps(self):
        """Show next steps after installation"""
        print("\n🎉 Installation Complete!")
        print("-" * 30)
        print("Next steps:")
        print("\n1. Run the server:")
        print("   python gmail_mcp_server.py")
        print("\n2. Try the example:")
        print("   python example_usage.py")
        print("\n3. Interactive testing:")
        print("   python test_gmail_mcp.py --interactive")
        print("\n4. Read the documentation:")
        print("   See SETUP_GUIDE.md for detailed information")
        print("\nHappy emailing! 📧")

    def install(self):
        """Run the complete installation process"""
        self.print_header()

        # Check Python version
        if not self.check_python_version():
            return False

        # Install dependencies
        if not self.install_dependencies():
            return False

        # Check/guide OAuth setup
        while not self.check_credentials():
            self.guide_oauth_setup()

        # Test authentication
        if not self.test_authentication():
            print("\n⚠️  Authentication setup incomplete")
            print("Please check your credentials.json and try again")
            return False

        # Optionally run tests
        run_tests = input("\n🧪 Run test suite? (y/N): ").strip().lower()
        if run_tests == 'y':
            self.run_tests()

        # Show next steps
        self.show_next_steps()
        return True


def main():
    """Main entry point"""
    installer = GmailMCPInstaller()

    try:
        success = installer.install()
        if success:
            print("\n✅ Installation completed successfully!")
        else:
            print("\n❌ Installation incomplete")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()