# Gmail MCP Server Setup Guide

This guide will help you set up and configure the Gmail MCP Server for complete Gmail integration through the Model Context Protocol.

## Features

### Email Operations
- **Send Email**: Send emails with attachments, HTML content, CC/BCC
- **Create Drafts**: Create draft emails for later editing
- **Reply to Email**: Reply to emails maintaining thread context
- **Read Email**: Get full email content and metadata
- **Search Emails**: Use Gmail's powerful search syntax

### Thread Management
- **Get Thread**: Retrieve all messages in a conversation
- **Reply in Thread**: Maintain conversation context

### Label Management
- **List Labels**: Get all Gmail labels
- **Create Labels**: Create new labels (including nested)
- **Apply Labels**: Add/remove labels from messages
- **Batch Operations**: Modify multiple messages at once

### Filter Management
- **Create Filters**: Auto-organize incoming emails
- **Advanced Criteria**: Filter by sender, subject, attachments, etc.

### Attachment Handling
- **Send Attachments**: Attach files to outgoing emails
- **Download Attachments**: Save attachments from received emails

### Advanced Features
- **Batch Operations**: Modify multiple messages efficiently
- **Trash/Delete**: Move to trash or permanently delete
- **Profile Info**: Get account statistics and information

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select Project**
   - Create a new project or select an existing one
   - Note the project ID

3. **Enable Gmail API**
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client Ids
   - Choose "Desktop application"
   - Name it "Gmail MCP Server"
   - Download the JSON file

5. **Save Credentials**
   - Rename the downloaded file to `credentials.json`
   - Place it in the same directory as `gmail_mcp_server.py`

### Step 3: First Run Authentication

1. **Run the server for the first time:**
   ```bash
   python gmail_mcp_server.py
   ```

2. **Complete OAuth Flow:**
   - A browser window will open
   - Sign in to your Google account
   - Grant permissions to the application
   - You'll see "The authentication flow has completed"

3. **Verify Setup:**
   - The server will create a `token.json` file
   - You should see your email address and message counts

### Step 4: Test the Installation

Run the test script to verify everything works:

```bash
# Run all tests
python test_gmail_mcp.py

# Interactive testing mode
python test_gmail_mcp.py --interactive
```

## Configuration

### OAuth Scopes

The server uses `https://www.googleapis.com/auth/gmail.modify` which provides:
- Read all Gmail messages
- Send and create emails
- Modify labels and filters
- Manage drafts
- Access attachments

### File Structure

```
MCP-Server/
├── gmail_mcp_server.py     # Main server implementation
├── test_gmail_mcp.py       # Test script
├── requirements.txt        # Dependencies
├── credentials.json        # OAuth credentials (you create this)
├── token.json             # Auth token (auto-generated)
└── SETUP_GUIDE.md         # This file
```

## Usage Examples

### Basic Email Operations

```python
# Send an email
await send_email(
    to="recipient@example.com",
    subject="Hello from MCP!",
    body="This email was sent via Gmail MCP Server",
    html=False
)

# Search for emails
await search_emails(
    query="from:important@company.com is:unread",
    max_results=10
)

# Read specific email
await read_email(message_id="abc123")
```

### Advanced Search Queries

```python
# Find emails with attachments from last week
await search_emails(query="has:attachment after:2024-01-01")

# Find important unread emails
await search_emails(query="is:important is:unread")

# Find emails in specific label
await search_emails(query="label:work")

# Complex query
await search_emails(query="from:boss@company.com has:attachment subject:urgent")
```

### Label Management

```python
# Create nested labels
await create_label(name="Work/Projects")
await create_label(name="Work/Projects/Client-A")

# Apply labels to messages
await modify_message_labels(
    message_id="abc123",
    add_labels=["Label_123", "Label_456"]
)

# Batch modify multiple messages
await batch_modify_messages(
    message_ids=["msg1", "msg2", "msg3"],
    add_labels=["Important"]
)
```

### Email Filters

```python
# Auto-label emails from specific sender
await create_filter(
    from_address="notifications@github.com",
    add_labels=["GitHub"]
)

# Forward important emails
await create_filter(
    subject="URGENT",
    forward_to="mobile@example.com"
)
```

## Gmail Search Syntax Reference

| Operator | Description | Example |
|----------|-------------|---------|
| `from:` | Sender email | `from:john@example.com` |
| `to:` | Recipient email | `to:me@example.com` |
| `subject:` | Subject contains | `subject:meeting` |
| `has:attachment` | Has attachments | `has:attachment` |
| `is:unread` | Unread messages | `is:unread` |
| `is:important` | Important messages | `is:important` |
| `label:` | Has specific label | `label:work` |
| `after:` | Date range (after) | `after:2024/01/01` |
| `before:` | Date range (before) | `before:2024/12/31` |
| `older_than:` | Relative date | `older_than:7d` |
| `newer_than:` | Relative date | `newer_than:2d` |

## Troubleshooting

### Common Issues

1. **"credentials.json not found"**
   - Download OAuth credentials from Google Cloud Console
   - Rename to `credentials.json` and place in project directory

2. **"Invalid scope" error**
   - Delete `token.json` and re-authenticate
   - Ensure Gmail API is enabled in Google Cloud Console

3. **"Rate limit exceeded"**
   - Gmail API has quotas (1 billion quota units per day)
   - Implement delays between requests if needed

4. **"Permission denied"**
   - Check OAuth scopes in Google Cloud Console
   - Re-authenticate with correct permissions

### Debug Mode

For detailed error information, modify the server to enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Token Refresh

If authentication expires:
1. Delete `token.json`
2. Run the server again
3. Complete OAuth flow

## Security Best Practices

1. **Protect Credentials**
   - Never commit `credentials.json` or `token.json` to version control
   - Use environment variables in production

2. **Scope Limitation**
   - Only request necessary Gmail scopes
   - Consider read-only scope for monitoring applications

3. **Token Storage**
   - Store tokens securely in production
   - Implement token encryption if needed

## Production Deployment

For production use:

1. **Environment Variables**
   ```bash
   export GOOGLE_CREDENTIALS=/path/to/credentials.json
   export GMAIL_TOKEN_PATH=/secure/path/to/token.json
   ```

2. **Service Account** (for server applications)
   - Use service account instead of OAuth for unattended operation
   - Configure domain-wide delegation if needed

3. **Error Handling**
   - Implement retry logic for transient failures
   - Log operations for audit trail

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test script to identify specific problems
3. Enable debug logging for detailed error information
4. Verify Google Cloud Console configuration

## API Limits

Gmail API quotas (per project):
- 1,000,000,000 quota units per day
- 250 quota units per user per second

Typical operation costs:
- Send email: 100 units
- Read email: 5 units
- Search: 5 units
- List: 5 units