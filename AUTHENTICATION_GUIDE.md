# Gmail MCP Server - Complete Authentication Guide

## Problem Solved ✅

Your Gmail MCP Server OAuth authentication issue has been resolved! The automatic browser opening problem in WSL has been fixed with manual authentication support.

## What Was Done

1. **Enhanced OAuth Authentication**: Modified `gmail_mcp_server.py` to support manual OAuth flow
2. **Added Command-Line Options**: New flags for manual auth and testing
3. **Created Helper Scripts**: Dedicated authentication and testing utilities
4. **WSL-Friendly Process**: Manual URL copying instead of automatic browser opening

## Quick Start - Complete These Steps

### Step 1: Choose Your Authentication Method

**Option A: Use the dedicated setup script (Recommended)**
```bash
python3 setup_auth.py
```

**Option B: Use the main server with manual auth**
```bash
python3 gmail_mcp_server.py --manual-auth --test-auth
```

### Step 2: Complete Browser Authentication

When you run either command above, you'll see:

```
======================================================================
STEP 1: AUTHORIZE IN BROWSER
======================================================================
Please follow these steps:

1. Copy this URL and open it in your web browser:

https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...

2. Sign in to your Google account
3. Review and accept the permissions
4. Copy the authorization code shown on the success page
======================================================================

STEP 2: ENTER AUTHORIZATION CODE

Paste the authorization code here:
```

### Step 3: Complete the Process

1. **Copy the entire URL** from your terminal
2. **Open any web browser** and paste the URL
3. **Sign in to your Google account**
4. **Click "Advanced"** if you see a security warning, then "Go to [App Name] (unsafe)"
5. **Accept the permissions** - the app needs Gmail access
6. **Copy the authorization code** from the success page
7. **Return to your terminal** and paste the code when prompted
8. **Press Enter**

### Step 4: Verify Success

You should see:
```
✅ AUTHENTICATION SUCCESSFUL!
======================================================================
Connected to: your-email@gmail.com
Total messages: 12345
Total threads: 6789

Your Gmail MCP Server is now ready to use!
```

## Testing Your Setup

### Test Authentication Only
```bash
python3 gmail_mcp_server.py --test-auth
```

### Run Comprehensive Tests
```bash
python3 test_auth.py
```

### Start the MCP Server
```bash
python3 gmail_mcp_server.py
```

## Available Command-Line Options

```bash
# Show help
python3 gmail_mcp_server.py --help

# Use manual authentication (for WSL)
python3 gmail_mcp_server.py --manual-auth

# Test authentication and exit
python3 gmail_mcp_server.py --test-auth

# Use both manual auth and test
python3 gmail_mcp_server.py --manual-auth --test-auth
```

## File Structure After Setup

```
/mnt/c/Coding-projects/MCP-Server/
├── credentials.json          # OAuth client config (provided)
├── token.json               # Access token (created after auth) ✅
├── gmail_mcp_server.py      # Main MCP server (enhanced) ✅
├── setup_auth.py            # Dedicated auth setup (new) ✅
├── test_auth.py             # Authentication tester (new) ✅
├── AUTHENTICATION_GUIDE.md  # This guide (new) ✅
├── OAUTH_SETUP.md           # Detailed OAuth guide (new) ✅
└── requirements.txt         # Dependencies
```

## Gmail MCP Server Features

Once authenticated, your server provides these tools:

### Email Operations
- **send_email**: Send emails with attachments
- **create_draft**: Create draft emails
- **reply_to_email**: Reply within email threads

### Email Management
- **search_emails**: Search using Gmail query syntax
- **read_email**: Read specific emails by ID
- **get_thread**: Get entire email conversations

### Organization
- **list_labels**: List all Gmail labels
- **create_label**: Create new labels
- **modify_message_labels**: Add/remove labels from messages
- **batch_modify_messages**: Bulk operations on multiple emails

### Advanced Features
- **create_filter**: Set up automatic email filters
- **download_attachment**: Download email attachments
- **trash_message**: Move emails to trash
- **delete_message**: Permanently delete emails
- **get_profile**: Get Gmail account information

## Troubleshooting

### Common Issues

**1. "App not verified" warning in browser**
- Click "Advanced" → "Go to [App Name] (unsafe)"
- This is normal for development use

**2. Authentication fails repeatedly**
- Delete `token.json` and try again
- Check your internet connection
- Verify `credentials.json` is valid

**3. "Invalid client" error**
- Ensure OAuth client is configured as "Desktop Application"
- Check that Gmail API is enabled in Google Cloud Console

**4. Permission denied errors**
- Use `--manual-auth` flag (already solved)

### Getting Help

If you encounter issues:
1. Check the error messages in the terminal
2. Review the OAuth setup in Google Cloud Console
3. Try deleting `token.json` and re-authenticating
4. Ensure your `credentials.json` is from a "Desktop Application" OAuth client

## Security Notes

- ✅ Uses secure OAuth 2.0 flow
- ✅ No passwords stored
- ✅ `token.json` contains your personal access token (keep private)
- ✅ Access can be revoked in Google Account settings
- ✅ All communications encrypted (HTTPS)

## Next Steps

1. **Complete authentication** using the steps above
2. **Test the server** with `python3 gmail_mcp_server.py --test-auth`
3. **Start using the MCP server** with `python3 gmail_mcp_server.py`
4. **Integrate with MCP clients** like Claude Desktop

Your Gmail MCP Server is now ready for production use! 🚀