# Gmail MCP Server

A complete Model Context Protocol (MCP) Server implementation for Gmail automation, designed to work seamlessly with N8N and other MCP-compatible tools.

## Features

- **Complete Gmail API Integration**: Send, read, search, modify, and delete emails
- **Label Management**: Create and manage Gmail labels/folders
- **OAuth2 Authentication**: Secure authentication with Google APIs
- **MCP Protocol Compliant**: Full compatibility with MCP specification
- **N8N Ready**: Optimized for N8N workflow automation
- **TypeScript**: Full type safety and modern development experience

## Quick Start

### 1. Prerequisites

- Node.js 18+ installed
- Gmail account with API access
- Google Cloud Console project with Gmail API enabled

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth2 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" or "Web application"
   - Add `http://localhost:3000/oauth/callback` to authorized redirect URIs
   - Download the credentials JSON file

### 3. Installation & Setup

```bash
# Clone the repository
git clone https://github.com/imthebreezy247/MCP-Server.git
cd MCP-Server

# Install dependencies
npm install

# Build the project
npm run build

# Copy environment template
cp .env.example .env
```

### 4. Configuration

Edit `.env` file with your Google OAuth2 credentials:

```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth/callback

# Optional: Custom credentials path
CREDENTIALS_PATH=./credentials.json

# Server configuration
MCP_SERVER_NAME=gmail-mcp-server
MCP_SERVER_VERSION=1.0.0
LOG_LEVEL=info
```

### 5. Authentication

Before using the server, you need to authenticate with Gmail:

```bash
# Start the server
npm start

# In another terminal or through your MCP client, call:
# Tool: gmail_auth_url
# This will return an authorization URL

# Visit the URL, authorize the application, and copy the authorization code

# Then call:
# Tool: gmail_auth_token
# Arguments: { "code": "your_authorization_code_here" }
```

## Usage with N8N

### 1. Install N8N (if not already installed)

```bash
npm install -g n8n
```

### 2. Configure N8N for MCP

Create a workflow in N8N and use the "Execute Command" node or "HTTP Request" node to interact with the MCP server.

### 3. Example N8N Workflow Nodes

#### Send Email Node
```json
{
  "tool": "gmail_send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Hello from N8N",
    "body": "This email was sent automatically via N8N and Gmail MCP Server!"
  }
}
```

#### Search Emails Node
```json
{
  "tool": "gmail_search_emails",
  "arguments": {
    "query": "is:unread from:important@example.com",
    "maxResults": 5
  }
}
```

#### Auto-Label Emails Node
```json
{
  "tool": "gmail_modify_email",
  "arguments": {
    "messageId": "{{$json.emails[0].id}}",
    "addLabelIds": ["Label_123"],
    "removeLabelIds": ["INBOX"]
  }
}
```

## Available Tools

### Authentication Tools

#### `gmail_auth_url`
Get OAuth2 authorization URL for initial setup.
- **Arguments**: None
- **Returns**: Authorization URL to visit

#### `gmail_auth_token`
Exchange authorization code for access token.
- **Arguments**: `{ "code": "authorization_code" }`
- **Returns**: Authentication status and credentials

### Email Management Tools

#### `gmail_send_email`
Send an email through Gmail.
- **Arguments**:
  ```json
  {
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Email content",
    "cc": ["cc@example.com"],  // optional
    "bcc": ["bcc@example.com"] // optional
  }
  ```

#### `gmail_search_emails`
Search for emails using Gmail search syntax.
- **Arguments**:
  ```json
  {
    "query": "from:example@gmail.com is:unread",
    "maxResults": 10,
    "labelIds": ["INBOX"],     // optional
    "includeSpamTrash": false  // optional
  }
  ```

#### `gmail_get_email`
Get a specific email by ID.
- **Arguments**:
  ```json
  {
    "messageId": "email_id_here",
    "format": "full"  // minimal, full, raw, metadata
  }
  ```

#### `gmail_modify_email`
Modify email labels (mark as read/unread, add/remove labels).
- **Arguments**:
  ```json
  {
    "messageId": "email_id_here",
    "addLabelIds": ["STARRED"],    // optional
    "removeLabelIds": ["UNREAD"]   // optional
  }
  ```

#### `gmail_delete_email`
Delete an email permanently.
- **Arguments**:
  ```json
  {
    "messageId": "email_id_here"
  }
  ```

### Label Management Tools

#### `gmail_get_labels`
Get all Gmail labels/folders.
- **Arguments**: None
- **Returns**: List of all labels

#### `gmail_create_label`
Create a new Gmail label/folder.
- **Arguments**:
  ```json
  {
    "name": "My New Label",
    "labelListVisibility": "labelShow",    // optional
    "messageListVisibility": "show"        // optional
  }
  ```

### Information Tools

#### `gmail_get_profile`
Get Gmail user profile information.
- **Arguments**: None
- **Returns**: User profile data

## Common Use Cases

### 1. Email Automation Workflow
```
Trigger (Schedule) → Search Unread Emails → Process Each Email → Mark as Read/Archive
```

### 2. Auto-Response System
```
Trigger (Webhook) → Search for Keywords → Send Automated Response → Label Email
```

### 3. Email Backup/Archiving
```
Trigger (Schedule) → Search Old Emails → Export to External Storage → Delete/Archive
```

### 4. Priority Email Alerts
```
Trigger (Schedule) → Search VIP Emails → Send Slack/SMS Notification → Mark as Priority
```

## Gmail Search Query Examples

- `is:unread` - Unread emails
- `from:example@gmail.com` - Emails from specific sender
- `subject:important` - Emails with "important" in subject
- `has:attachment` - Emails with attachments
- `is:starred` - Starred emails
- `label:work` - Emails with "work" label
- `newer_than:2d` - Emails newer than 2 days
- `larger:5M` - Emails larger than 5MB

## Error Handling

The server includes comprehensive error handling:

- **Authentication Errors**: Clear messages for OAuth2 issues
- **API Rate Limits**: Automatic retry with exponential backoff
- **Validation Errors**: Detailed schema validation messages
- **Network Errors**: Graceful handling of connectivity issues

## Development

### Running in Development Mode
```bash
npm run dev
```

### Building
```bash
npm run build
```

### Running Tests
```bash
npm test
```

### Linting
```bash
npm run lint
```

## Security Considerations

1. **Credentials Storage**: Tokens are stored locally in `credentials.json`
2. **Environment Variables**: Sensitive config in `.env` (not committed)
3. **OAuth2 Scopes**: Minimal required permissions requested
4. **Token Refresh**: Automatic token refresh handling

## Troubleshooting

### Common Issues

1. **"Not authenticated" errors**
   - Run `gmail_auth_url` tool to get authorization URL
   - Complete OAuth2 flow with `gmail_auth_token`

2. **"Invalid credentials" errors**
   - Check `.env` configuration
   - Verify Google Cloud Console setup
   - Ensure Gmail API is enabled

3. **Rate limit errors**
   - Reduce request frequency
   - Implement delays between bulk operations

4. **Build errors**
   - Ensure Node.js 18+ is installed
   - Run `npm install` to update dependencies

### Debug Mode

Set `LOG_LEVEL=debug` in `.env` for verbose logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the Gmail API documentation
