# Gmail MCP Server API Reference

Complete API reference for all tools and resources available in the Gmail MCP Server.

## Authentication

All tools except `gmail_auth_url` and `gmail_auth_token` require authentication with Gmail.

### Authentication Flow

1. Call `gmail_auth_url` to get authorization URL
2. Visit URL and authorize application
3. Call `gmail_auth_token` with authorization code
4. Server will store credentials automatically

## Tools

### Authentication Tools

#### `gmail_auth_url`

Get OAuth2 authorization URL for Gmail access.

**Arguments:** None

**Response:**
```json
{
  "success": true,
  "authUrl": "https://accounts.google.com/oauth2/auth?...",
  "message": "Visit this URL to authorize the application"
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_auth_url"
}
```

---

#### `gmail_auth_token`

Exchange authorization code for access token.

**Arguments:**
- `code` (string, required): Authorization code from OAuth2 flow

**Response:**
```json
{
  "success": true,
  "credentials": {
    "access_token": "ya29.a0...",
    "refresh_token": "1//04...",
    "scope": "https://www.googleapis.com/auth/gmail.readonly ...",
    "token_type": "Bearer",
    "expiry_date": 1640995200000
  },
  "message": "Authentication successful"
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_auth_token",
  "arguments": {
    "code": "4/0AX4XfWj..."
  }
}
```

---

### Email Management Tools

#### `gmail_send_email`

Send an email through Gmail.

**Arguments:**
- `to` (string | string[], required): Recipient email address(es)
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `cc` (string | string[], optional): CC email address(es)
- `bcc` (string | string[], optional): BCC email address(es)

**Response:**
```json
{
  "success": true,
  "messageId": "18c2c...",
  "message": "Email sent successfully"
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email sent via Gmail MCP Server",
    "cc": ["cc@example.com"]
  }
}
```

---

#### `gmail_search_emails`

Search for emails using Gmail search syntax.

**Arguments:**
- `query` (string, required): Gmail search query
- `maxResults` (number, optional): Maximum emails to return (1-500, default: 10)
- `labelIds` (string[], optional): Filter by specific label IDs
- `includeSpamTrash` (boolean, optional): Include spam and trash (default: false)

**Response:**
```json
{
  "success": true,
  "emails": [
    {
      "id": "18c2c...",
      "threadId": "18c2c...",
      "snippet": "Email preview text...",
      "payload": {
        "headers": [
          {
            "name": "From",
            "value": "sender@example.com"
          },
          {
            "name": "Subject",
            "value": "Email Subject"
          }
        ]
      }
    }
  ],
  "count": 1
}
```

**Common Query Examples:**
- `is:unread` - Unread emails
- `from:example@gmail.com` - From specific sender
- `subject:important` - Subject contains "important"
- `has:attachment` - Has attachments
- `newer_than:2d` - Newer than 2 days
- `label:work` - Has "work" label

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_search_emails",
  "arguments": {
    "query": "is:unread from:important@example.com",
    "maxResults": 5,
    "labelIds": ["INBOX"]
  }
}
```

---

#### `gmail_get_email`

Get a specific email by its ID.

**Arguments:**
- `messageId` (string, required): Gmail message ID
- `format` (string, optional): Format of email data
  - `minimal`: ID and thread ID only
  - `full`: Full message data (default)
  - `raw`: Raw email content
  - `metadata`: Headers only

**Response:**
```json
{
  "success": true,
  "email": {
    "id": "18c2c...",
    "threadId": "18c2c...",
    "snippet": "Email preview...",
    "payload": {
      "headers": [...],
      "body": {
        "data": "base64_encoded_content"
      }
    }
  }
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_get_email",
  "arguments": {
    "messageId": "18c2c8f1234567890",
    "format": "full"
  }
}
```

---

#### `gmail_modify_email`

Modify email labels (mark as read/unread, add/remove labels).

**Arguments:**
- `messageId` (string, required): Gmail message ID
- `addLabelIds` (string[], optional): Label IDs to add
- `removeLabelIds` (string[], optional): Label IDs to remove

**Common Label IDs:**
- `INBOX` - Inbox
- `UNREAD` - Unread status
- `STARRED` - Starred
- `IMPORTANT` - Important
- `SENT` - Sent mail
- `DRAFT` - Draft
- `SPAM` - Spam
- `TRASH` - Trash

**Response:**
```json
{
  "success": true,
  "email": {
    "id": "18c2c...",
    "labelIds": ["INBOX", "STARRED"]
  },
  "message": "Email modified successfully"
}
```

**Example (Mark as Read):**
```bash
# MCP Tool Call
{
  "tool": "gmail_modify_email",
  "arguments": {
    "messageId": "18c2c8f1234567890",
    "removeLabelIds": ["UNREAD"]
  }
}
```

**Example (Star Email):**
```bash
# MCP Tool Call
{
  "tool": "gmail_modify_email",
  "arguments": {
    "messageId": "18c2c8f1234567890",
    "addLabelIds": ["STARRED"]
  }
}
```

---

#### `gmail_delete_email`

Delete an email permanently.

**Arguments:**
- `messageId` (string, required): Gmail message ID to delete

**Response:**
```json
{
  "success": true,
  "message": "Email deleted successfully"
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_delete_email",
  "arguments": {
    "messageId": "18c2c8f1234567890"
  }
}
```

---

### Label Management Tools

#### `gmail_get_labels`

Get all Gmail labels/folders.

**Arguments:** None

**Response:**
```json
{
  "success": true,
  "labels": [
    {
      "id": "INBOX",
      "name": "INBOX",
      "type": "system",
      "messagesTotal": 100,
      "messagesUnread": 5
    },
    {
      "id": "Label_123",
      "name": "Work",
      "type": "user",
      "messagesTotal": 50,
      "messagesUnread": 2
    }
  ]
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_get_labels"
}
```

---

#### `gmail_create_label`

Create a new Gmail label/folder.

**Arguments:**
- `name` (string, required): Name of the new label
- `labelListVisibility` (string, optional): Label list visibility
  - `labelShow` - Show in label list (default)
  - `labelShowIfUnread` - Show if unread
  - `labelHide` - Hide from label list
- `messageListVisibility` (string, optional): Message list visibility
  - `show` - Show in message list (default)
  - `hide` - Hide from message list

**Response:**
```json
{
  "success": true,
  "label": {
    "id": "Label_456",
    "name": "My New Label",
    "type": "user",
    "labelListVisibility": "labelShow",
    "messageListVisibility": "show"
  },
  "message": "Label created successfully"
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_create_label",
  "arguments": {
    "name": "Project Alpha",
    "labelListVisibility": "labelShow",
    "messageListVisibility": "show"
  }
}
```

---

### Information Tools

#### `gmail_get_profile`

Get Gmail user profile information.

**Arguments:** None

**Response:**
```json
{
  "success": true,
  "profile": {
    "emailAddress": "user@gmail.com",
    "messagesTotal": 1000,
    "threadsTotal": 500,
    "historyId": "123456"
  }
}
```

**Example:**
```bash
# MCP Tool Call
{
  "tool": "gmail_get_profile"
}
```

---

## Resources

The server provides MCP resources for commonly accessed data.

### `gmail://profile`

Current user's Gmail profile information.

**Content Type:** `application/json`

**Example Response:**
```json
{
  "emailAddress": "user@gmail.com",
  "messagesTotal": 1000,
  "threadsTotal": 500,
  "historyId": "123456"
}
```

---

### `gmail://labels`

List of all Gmail labels/folders.

**Content Type:** `application/json`

**Example Response:**
```json
[
  {
    "id": "INBOX",
    "name": "INBOX",
    "type": "system",
    "messagesTotal": 100,
    "messagesUnread": 5
  }
]
```

---

### `gmail://auth-status`

Current authentication status.

**Content Type:** `application/json`

**Example Response (Authenticated):**
```json
{
  "isAuthenticated": true,
  "authUrl": null,
  "message": "Authenticated with Gmail"
}
```

**Example Response (Not Authenticated):**
```json
{
  "isAuthenticated": false,
  "authUrl": "https://accounts.google.com/oauth2/auth?...",
  "message": "Not authenticated. Use the authUrl to begin OAuth2 flow."
}
```

---

## Error Responses

All tools return standardized error responses:

```json
{
  "success": false,
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `NOT_AUTHENTICATED` - Gmail service not authenticated
- `SEND_EMAIL_FAILED` - Failed to send email
- `SEARCH_EMAILS_FAILED` - Failed to search emails
- `GET_EMAIL_FAILED` - Failed to get email
- `MODIFY_EMAIL_FAILED` - Failed to modify email
- `DELETE_EMAIL_FAILED` - Failed to delete email
- `GET_LABELS_FAILED` - Failed to get labels
- `CREATE_LABEL_FAILED` - Failed to create label
- `GET_PROFILE_FAILED` - Failed to get profile

---

## Rate Limits

Gmail API has the following rate limits:

- **250 quota units per user per second**
- **1,000,000,000 quota units per day**

Common operations and their quota costs:
- Send email: 100 units
- Search emails: 5 units
- Get email: 5 units
- Modify email: 5 units
- Delete email: 10 units

The server implements automatic retry with exponential backoff for rate limit errors.

---

## Best Practices

### 1. Efficient Searches
Use specific queries to reduce API calls:
```bash
# Good: Specific query
"from:important@example.com newer_than:1d"

# Avoid: Broad queries
"is:unread"
```

### 2. Batch Operations
Process multiple emails efficiently:
```bash
# Search once, process many
{
  "tool": "gmail_search_emails",
  "arguments": {
    "query": "is:unread",
    "maxResults": 50
  }
}
```

### 3. Label Management
Use labels instead of folders for better organization:
```bash
# Create meaningful labels
{
  "tool": "gmail_create_label",
  "arguments": {
    "name": "Project/Alpha/Urgent"
  }
}
```

### 4. Error Handling
Always check for errors in tool responses:
```javascript
if (!response.success) {
  console.error('Tool failed:', response.error);
  // Handle error appropriately
}
```