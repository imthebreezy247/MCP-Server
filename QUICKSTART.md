# Gmail MCP Server - Quick Start Guide

## 1. Setup Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth2 Desktop Application credentials
5. Download credentials file

## 2. Install and Setup

```bash
# Install dependencies
npm install

# Place your credentials file
cp /path/to/downloaded/file.json credentials.json

# Build project
npm run build

# Run authentication setup
npm run setup
```

## 3. Start Server

```bash
npm start
```

## 4. Test with MCP Client

```bash
# List available tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | npm start

# List emails
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_emails","arguments":{"maxResults":5}}}' | npm start
```

## 5. Integration Examples

### N8N Workflow
- Use HTTP Request node to send MCP requests
- Parse JSON responses
- Automate email workflows

### Common Operations
- List unread emails: `{"name":"list_emails","arguments":{"query":"is:unread"}}`
- Send email: `{"name":"send_email","arguments":{"to":"user@example.com","subject":"Test","body":"Hello"}}`
- Mark as read: `{"name":"mark_as_read","arguments":{"messageIds":["123"]}}`