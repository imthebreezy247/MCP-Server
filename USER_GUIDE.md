# Gmail MCP Server - User Guide

## What is This?

This is a **Gmail MCP Server** that lets AI assistants (like Claude) interact with your Gmail account. Once set up, you can ask Claude to:
- Read your emails
- Send emails
- Search your inbox
- Manage labels
- Archive/delete messages
- And more!

## Prerequisites

- Python 3.12 (you already have this installed)
- Gmail account
- Google Cloud project with Gmail API enabled (for OAuth credentials)

## Setup (One-Time)

### Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable the **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download the credentials
5. Save the downloaded file as `credentials.json` in this folder:
   ```
   C:\Coding-projects\MCP-Server\credentials.json
   ```

### Step 2: Install Dependencies

```bash
# Make sure you're using Python 3.12
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe -m pip install -r requirements.txt
```

### Step 3: Authenticate

```bash
# Test authentication
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py --test-auth
```

This will:
- Open your browser
- Ask you to log in to Gmail
- Request permissions
- Save a `token.json` file (used for future authentication)

**You've already completed this step!** ✓

## How to Use

### Method 1: With Claude Desktop (Recommended)

This is the most common way to use MCP servers.

1. **Find your Claude Desktop config file:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Edit the config file** to add your Gmail MCP server:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "C:\\Users\\shann\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "C:\\Coding-projects\\MCP-Server\\gmail_mcp_server.py"
      ]
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Use it!** Ask Claude things like:
   - "Show me my latest emails"
   - "Search for emails from john@example.com"
   - "Send an email to jane@example.com saying hello"
   - "What are my unread messages?"

### Method 2: Direct Testing (For Development)

Run the server directly to test functionality:

```bash
# Test authentication
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py --test-auth

# Run the server (it will listen for MCP commands)
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py
```

### Method 3: Using MCP Inspector (For Debugging)

The MCP Inspector lets you test the server interactively:

```bash
# Install the inspector
npm install -g @modelcontextprotocol/inspector

# Run with your server
mcp-inspector /c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py
```

This opens a web interface where you can test all available tools.

## Available Features

Once connected, Claude can use these Gmail functions:

| Function | Description |
|----------|-------------|
| `list_messages` | Get list of emails (with filters) |
| `get_message` | Read a specific email |
| `send_message` | Send a new email |
| `search_messages` | Search your inbox |
| `modify_message` | Add/remove labels |
| `delete_message` | Delete an email |
| `trash_message` | Move email to trash |
| `list_labels` | Get all your labels |
| `create_label` | Create a new label |
| `get_profile` | Get your Gmail profile info |

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastmcp'"

**Solution:** You're using the wrong Python version. Use Python 3.12:
```bash
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py
```

### Issue: "credentials.json not found"

**Solution:** Download OAuth credentials from Google Cloud Console and save as `credentials.json` in this folder.

### Issue: "Token expired"

**Solution:** Delete `token.json` and run `--test-auth` again:
```bash
rm token.json
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py --test-auth
```

### Issue: "The system cannot find the path specified"

**Solution:** Use the MINGW path format:
```bash
/c/Users/shann/AppData/Local/Programs/Python/Python312/python.exe gmail_mcp_server.py
```

## Pro Tips

1. **Create a shortcut:** Add this to your PATH or create a batch file:
   ```batch
   @echo off
   C:\Users\shann\AppData\Local\Programs\Python\Python312\python.exe C:\Coding-projects\MCP-Server\gmail_mcp_server.py %*
   ```
   Save as `gmail-mcp.bat` somewhere in your PATH.

2. **Security:** Keep `token.json` and `credentials.json` private - they contain your Gmail access credentials!

3. **Monitoring:** Check the server logs if something goes wrong - it prints helpful debug info.

## What's Next?

- Start Claude Desktop with the MCP server configured
- Try asking Claude to check your email
- Use it to automate email tasks
- Build custom workflows with your emails

## Need Help?

- Check the [FastMCP docs](https://github.com/jlowin/fastmcp)
- Read the [Gmail API docs](https://developers.google.com/gmail/api)
- Review the source code: `gmail_mcp_server.py`
