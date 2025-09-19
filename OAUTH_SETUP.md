# Gmail MCP Server - OAuth Authentication Setup

This guide will help you complete the OAuth authentication process for the Gmail MCP Server in WSL/Linux environments where automatic browser opening doesn't work.

## Quick Authentication Steps

### 1. Run the Authentication Test

```bash
python3 gmail_mcp_server.py --manual-auth --test-auth
```

### 2. Follow the Manual Authentication Process

When you run the command above, you'll see output like this:

```
============================================================
MANUAL OAUTH AUTHENTICATION REQUIRED
============================================================
Since automatic browser opening failed, please follow these steps:

1. Copy the URL below and paste it into a web browser:

https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...

2. Complete the authorization in your browser
3. Copy the authorization code from the browser
4. Paste it below when prompted
============================================================

Enter the authorization code:
```

### 3. Complete Browser Authorization

1. **Copy the entire URL** that appears in your terminal
2. **Open a web browser** (Chrome, Firefox, Edge, etc.) and paste the URL
3. **Sign in to your Google account** if prompted
4. **Review and accept the permissions** - the app will request access to:
   - View, compose, send, and permanently delete all your email from Gmail
   - Manage drafts and send emails
5. **Copy the authorization code** - After accepting, you'll see a page that shows an authorization code
6. **Return to your terminal** and paste the authorization code when prompted

### 4. Verify Successful Authentication

If authentication succeeds, you'll see:

```
✓ Authentication successful!
✓ Connected to: your-email@gmail.com
✓ Total messages: 12345
✓ Total threads: 6789

Gmail MCP Server is ready to use!
```

## Alternative Testing Methods

### Use the Custom Test Script

```bash
python3 test_auth.py
```

This runs a comprehensive test that verifies:
- Authentication
- Gmail API connection
- Basic email search
- Label listing

### Test Individual Functions

After authentication succeeds, you can test individual MCP functions:

```bash
# Run the full MCP server
python3 gmail_mcp_server.py --manual-auth

# Or test without manual auth (if token.json exists)
python3 gmail_mcp_server.py --test-auth
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Missing credentials.json" Error
**Problem**: The OAuth client configuration file is missing.
**Solution**:
- Download `credentials.json` from Google Cloud Console
- Place it in the same directory as `gmail_mcp_server.py`

#### 2. "Invalid client" Error in Browser
**Problem**: The OAuth client isn't configured correctly.
**Solution**:
- Verify the OAuth client is set up as "Desktop Application"
- Check that the Gmail API is enabled in Google Cloud Console
- Ensure the OAuth consent screen is configured

#### 3. "Access blocked" or "App not verified" Warning
**Problem**: Google shows a security warning for unverified apps.
**Solution**:
- Click "Advanced" on the warning page
- Click "Go to [Your App Name] (unsafe)"
- This is normal for development/personal use

#### 4. "Permission denied" Browser Errors
**Problem**: This was the original issue - browser can't open automatically in WSL.
**Solution**: ✅ **SOLVED** - Use `--manual-auth` flag

#### 5. Token Refresh Issues
**Problem**: Authentication works once but fails later.
**Solution**:
- Delete `token.json` and re-authenticate
- Check that your system clock is correct
- Verify internet connectivity

### File Structure Verification

Ensure your directory contains:
```
/mnt/c/Coding-projects/MCP-Server/
├── credentials.json          # OAuth client config (required)
├── gmail_mcp_server.py      # Main MCP server
├── test_auth.py             # Authentication test script
├── token.json               # Generated after first auth (auto-created)
└── requirements.txt         # Python dependencies
```

### Authentication Flow Details

1. **First Time**: No `token.json` exists
   - OAuth flow generates authorization URL
   - User completes browser authorization
   - Authorization code exchanged for access token
   - `token.json` saved for future use

2. **Subsequent Runs**: `token.json` exists
   - Loads existing credentials
   - Automatically refreshes if expired
   - Only re-authenticates if refresh fails

## Testing After Authentication

Once authentication is complete, you can verify the Gmail MCP Server functionality:

### 1. List Available Tools
```bash
python3 gmail_mcp_server.py
```

### 2. Test Email Operations
The server provides these main functions:
- `send_email` - Send emails with attachments
- `search_emails` - Search using Gmail query syntax
- `read_email` - Read specific emails by ID
- `create_draft` - Create draft emails
- `reply_to_email` - Reply to emails in threads
- `list_labels` - List all Gmail labels
- `create_label` - Create new labels
- `modify_message_labels` - Add/remove labels
- `batch_modify_messages` - Bulk operations
- `create_filter` - Set up email filters
- `download_attachment` - Download email attachments
- `get_profile` - Get Gmail account info

### 3. Integration with MCP Clients
Once running, the server can be used with MCP-compatible clients like Claude Desktop.

## Security Notes

- `credentials.json` contains your OAuth client configuration (safe to share in teams)
- `token.json` contains your personal access token (keep private, never commit to version control)
- The server uses Gmail's secure OAuth 2.0 flow
- No passwords are stored locally
- Access can be revoked at any time in Google Account settings

## Need Help?

If you encounter issues not covered here:
1. Check the terminal output for specific error messages
2. Verify your Google Cloud Console OAuth setup
3. Ensure the Gmail API quota isn't exceeded
4. Test with a simple Gmail API Python script to isolate issues

The manual authentication process should resolve the browser-opening issues in WSL environments!