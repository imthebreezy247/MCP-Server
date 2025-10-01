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