# Gmail MCP Server

A comprehensive Model Context Protocol (MCP) server for Gmail that provides full email management capabilities. Perfect for automating Gmail operations through N8N or other MCP-compatible systems.

## Features

- **Read Emails**: List, search, and get detailed email information
- **Send Emails**: Compose and send new emails with full formatting support
- **Reply to Emails**: Reply to existing emails with thread continuity
- **Email Management**: Mark as read/unread, archive, delete emails
- **Label Management**: Create, modify, and manage Gmail labels
- **Advanced Search**: Search emails with multiple criteria (sender, date, attachments, etc.)
- **Attachment Support**: Access and manage email attachments
- **Bulk Operations**: Perform operations on multiple emails at once

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with Gmail API enabled
2. **OAuth2 Credentials**: Download OAuth2 client credentials from Google Cloud Console
3. **Node.js**: Version 18 or higher

## Setup Instructions

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application" as the application type
   - Download the credentials file

### 2. Project Setup

```bash
# Clone and install dependencies
git clone <repository-url>
cd MCP-Server
npm install

# Place your downloaded credentials file as 'credentials.json' in the project root
cp /path/to/your/downloaded/credentials.json ./credentials.json

# Build the project
npm run build

# Run the authentication setup
node dist/setup.js
```

### 3. Authentication

The setup script will:
1. Generate an authentication URL
2. Open your browser for Google OAuth consent
3. Save the authentication token for future use

Follow the prompts to complete authentication.

## Usage

### Starting the MCP Server

```bash
npm start
```

The server runs on stdio and communicates via the MCP protocol.

### Available Tools

#### Email Reading Tools

- **`list_emails`**: List emails with optional filters
  ```json
  {
    "query": "from:example@gmail.com is:unread",
    "maxResults": 20,
    "labelIds": ["INBOX"]
  }
  ```

- **`get_email`**: Get detailed email information
  ```json
  {
    "messageId": "message-id-here",
    "format": "full"
  }
  ```

- **`search_emails`**: Advanced email search
  ```json
  {
    "from": "sender@example.com",
    "subject": "important",
    "hasAttachment": true,
    "isUnread": true,
    "dateAfter": "2024/01/01",
    "maxResults": 50
  }
  ```

#### Email Sending Tools

- **`send_email`**: Send a new email
  ```json
  {
    "to": "recipient@example.com",
    "cc": "cc@example.com",
    "subject": "Hello from MCP",
    "body": "This is the email body",
    "isHtml": false
  }
  ```

- **`reply_to_email`**: Reply to an existing email
  ```json
  {
    "messageId": "original-message-id",
    "body": "This is my reply",
    "replyAll": false
  }
  ```

#### Email Management Tools

- **`modify_email`**: Add/remove labels from emails
  ```json
  {
    "messageId": "message-id",
    "addLabelIds": ["STARRED"],
    "removeLabelIds": ["UNREAD"]
  }
  ```

- **`mark_as_read`** / **`mark_as_unread`**: Bulk read status changes
  ```json
  {
    "messageIds": ["id1", "id2", "id3"]
  }
  ```

- **`archive_emails`** / **`delete_emails`**: Bulk archive or delete
  ```json
  {
    "messageIds": ["id1", "id2", "id3"]
  }
  ```

#### Label Management Tools

- **`get_labels`**: List all available labels
- **`create_label`**: Create a new label
  ```json
  {
    "name": "My Custom Label",
    "messageListVisibility": "show",
    "labelListVisibility": "labelShow"
  }
  ```

#### Attachment Tools

- **`get_attachments`**: List attachments in an email
  ```json
  {
    "messageId": "message-id-with-attachments"
  }
  ```

## Integration with N8N

To use this MCP server with N8N:

1. Start the MCP server: `npm start`
2. In N8N, use HTTP Request nodes to communicate with the MCP server
3. Send MCP-formatted requests to the stdio interface
4. Parse JSON responses for email data

### Example N8N Workflow

1. **Trigger**: Schedule or webhook
2. **MCP Request**: Use the `list_emails` tool to get unread emails
3. **Process**: Parse email data and apply business logic
4. **Action**: Use `send_email` or `modify_email` tools to respond

## Gmail Search Query Syntax

The `query` parameter in `list_emails` supports Gmail's full search syntax:

- `from:sender@example.com` - Emails from specific sender
- `to:recipient@example.com` - Emails to specific recipient
- `subject:keyword` - Emails with keyword in subject
- `has:attachment` - Emails with attachments
- `is:unread` - Unread emails
- `is:starred` - Starred emails
- `label:labelname` - Emails with specific label
- `after:2024/01/01` - Emails after date
- `before:2024/12/31` - Emails before date
- `older_than:2d` - Emails older than 2 days
- `newer_than:1m` - Emails newer than 1 month

## Common Label IDs

- `INBOX` - Inbox
- `SENT` - Sent mail
- `DRAFT` - Drafts
- `SPAM` - Spam
- `TRASH` - Trash
- `STARRED` - Starred
- `IMPORTANT` - Important
- `UNREAD` - Unread

## Error Handling

The server provides detailed error messages for:
- Authentication failures
- API quota exceeded
- Invalid message IDs
- Permission issues
- Network connectivity problems

## Security Considerations

- Store `credentials.json` and `token.json` securely
- Use environment variables for sensitive configuration
- Regularly rotate OAuth tokens
- Monitor API usage and quotas
- Implement proper logging for audit trails

## Development

### Building
```bash
npm run build
```

### Development Mode
```bash
npm run dev
```

### Debugging
```bash
npm run inspect
```

## License

MIT License - see LICENSE file for details.
