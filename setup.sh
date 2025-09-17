#!/bin/bash

# Gmail MCP Server Setup Script
# This script helps you set up the Gmail MCP Server quickly

set -e

echo "🚀 Gmail MCP Server Setup"
echo "========================="

# Check Node.js version
echo "Checking Node.js version..."
node_version=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$node_version" ] || [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18+ is required. Please install Node.js 18 or later."
    exit 1
fi
echo "✅ Node.js version: $(node --version)"

# Install dependencies
echo ""
echo "Installing dependencies..."
npm install

# Build the project
echo ""
echo "Building the project..."
npm run build

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: You need to configure your Google OAuth2 credentials in .env"
    echo "   1. Edit .env file with your Google OAuth2 credentials"
    echo "   2. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI"
else
    echo "✅ .env file already exists"
fi

# Create credentials directory
mkdir -p "$(dirname "${CREDENTIALS_PATH:-./credentials.json}")"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with Google OAuth2 credentials"
echo "2. Run 'npm start' to start the MCP server"
echo "3. Use the gmail_auth_url tool to begin authentication"
echo ""
echo "For detailed instructions, see README.md"