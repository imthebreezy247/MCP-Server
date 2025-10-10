# Claude Desktop MCP Server Setup Guide

This guide will help you configure the Gmail MCP Server to work with Claude Desktop.

## Prerequisites

1. **Authentication Setup**: You must complete OAuth authentication first
   - If you haven't already authenticated, run: `python gmail_mcp_server.py --test-auth`
   - This will create the necessary `token.json` file
   - Make sure both `credentials.json` and `token.json` exist in `C:\Coding-projects\MCP-Server\`

2. **Required Files**:
   - `credentials.json` - OAuth credentials from Google Cloud Console
   - `token.json` - Generated after successful authentication
   - `gmail_mcp_server.py` - The MCP server script

## Installation Steps

### Step 1: Locate Claude Desktop Config Directory

The Claude Desktop configuration file should be placed in one of these locations:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Typically: `C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\claude_desktop_config.json`

### Step 2: Copy the Configuration

A pre-configured file has been created at:
```
C:\Coding-projects\MCP-Server\claude_desktop_config.json
```

**Option A - Manual Copy:**
1. Open File Explorer
2. Navigate to `%APPDATA%\Claude\` (paste this in the address bar)
3. If the `Claude` folder doesn't exist, create it
4. Copy `claude_desktop_config.json` from this project to that folder

**Option B - Using Command Line:**
```bash
# Create the Claude config directory if it doesn't exist
mkdir -p "$APPDATA/Claude"

# Copy the config file
cp C:/Coding-projects/MCP-Server/claude_desktop_config.json "$APPDATA/Claude/claude_desktop_config.json"
```

### Step 3: Verify Configuration

The configuration file should contain:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "C:\\Users\\shann\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "C:\\Coding-projects\\MCP-Server\\gmail_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Coding-projects\\MCP-Server",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop

1. Completely quit Claude Desktop (not just close the window)
2. Restart Claude Desktop
3. The Gmail MCP Server should now be available

## Verifying It Works

Once Claude Desktop restarts, you should be able to use Gmail commands like:

- "Check my latest emails"
- "Send an email to someone@example.com"
- "Search for emails from john@example.com"
- "Create a draft email"

## Troubleshooting

### Server Not Starting

1. **Check Authentication**:
   ```bash
   cd C:/Coding-projects/MCP-Server
   python gmail_mcp_server.py --test-auth
   ```

2. **Verify Python Path**:
   ```bash
   where python
   ```
   Make sure the path in the config matches your Python installation

3. **Check Logs**:
   - Claude Desktop logs are usually in `%APPDATA%\Claude\logs\`
   - Look for error messages related to the MCP server

### Permission Issues

If you see permission errors:
- Make sure `token.json` and `credentials.json` are readable
- Ensure the Python executable has proper permissions
- Try running Claude Desktop as administrator (not recommended long-term)

### Python Not Found

If Claude Desktop can't find Python:
1. Get the full path: `where python`
2. Update the `command` field in the config with the full path
3. Make sure you're using Python 3.11 or 3.12

### Missing Dependencies

If you see import errors:
```bash
cd C:/Coding-projects/MCP-Server
pip install fastmcp google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Configuration Options

### Using Manual Authentication

If you need manual OAuth (for WSL or headless environments), modify the config:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "C:\\Users\\shann\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "C:\\Coding-projects\\MCP-Server\\gmail_mcp_server.py",
        "--manual-auth"
      ],
      "env": {
        "PYTHONPATH": "C:\\Coding-projects\\MCP-Server",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Available Gmail Tools

Once configured, Claude can use these Gmail functions:

- `send_email` - Send emails with optional attachments
- `create_draft` - Create draft emails
- `search_emails` - Search using Gmail query syntax
- `read_email` - Read specific emails
- `get_thread` - Get entire email threads
- `reply_to_email` - Reply to emails
- `list_labels` - List all Gmail labels
- `create_label` - Create new labels
- `modify_message_labels` - Add/remove labels
- `delete_message` - Permanently delete
- `trash_message` - Move to trash
- `batch_modify_messages` - Bulk operations
- `create_filter` - Create email filters
- `download_attachment` - Download attachments
- `get_profile` - Get account info

## Security Notes

- The `token.json` file contains your OAuth credentials
- Keep this file secure and don't share it
- The server runs locally and communicates only with Gmail API
- No data is sent to third parties

## Support

For issues:
1. Check the authentication guide: `AUTHENTICATION_GUIDE.md`
2. Review troubleshooting: `OAUTH_TROUBLESHOOTING.md`
3. Test the server standalone: `python gmail_mcp_server.py --test-auth`
