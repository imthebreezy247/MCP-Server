# Quick Start Guide

Get your Gmail MCP Server up and running in 5 minutes!

## Prerequisites
- Node.js 18+
- Gmail account
- Google Cloud Console access

## 1. Setup Google Cloud (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project
3. Enable Gmail API: `APIs & Services` → `Library` → Search `Gmail API` → `Enable`
4. Create credentials: `APIs & Services` → `Credentials` → `Create Credentials` → `OAuth 2.0 Client IDs`
5. Choose `Desktop application`
6. Download credentials JSON

## 2. Install & Configure (1 minute)

```bash
# Run setup script
./setup.sh

# Edit .env with your credentials
nano .env
```

Add your Google OAuth2 credentials:
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth/callback
```

## 3. Authenticate (1 minute)

```bash
# Start server
npm start

# In another terminal, get auth URL
curl -X POST -H "Content-Type: application/json" \
  -d '{"tool":"gmail_auth_url"}' \
  http://localhost:3000/mcp

# Visit the returned URL, authorize, copy code

# Exchange code for token
curl -X POST -H "Content-Type: application/json" \
  -d '{"tool":"gmail_auth_token","arguments":{"code":"YOUR_CODE"}}' \
  http://localhost:3000/mcp
```

## 4. Test (1 minute)

```bash
# Send test email
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "tool": "gmail_send_email",
    "arguments": {
      "to": "test@example.com",
      "subject": "Test from MCP Server",
      "body": "Hello from Gmail MCP Server!"
    }
  }' \
  http://localhost:3000/mcp

# Search emails
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "tool": "gmail_search_emails",
    "arguments": {
      "query": "is:unread",
      "maxResults": 5
    }
  }' \
  http://localhost:3000/mcp
```

## 5. Use with N8N

1. Import workflow from `examples/n8n-workflows/`
2. Update MCP server path in workflow
3. Activate workflow

## Common Commands

```bash
# Development mode
npm run dev

# Build
npm run build

# Production
npm start

# Get server status
curl http://localhost:3000/health
```

## Need Help?

- Check `README.md` for detailed documentation
- See `docs/api-reference.md` for complete API docs
- Review `docs/n8n-integration.md` for N8N setup
- Look at `examples/` for workflow templates

## Security Notes

- Keep `.env` file secure (never commit)
- Credentials stored in `credentials.json` (also never commit)
- Use HTTPS in production
- Regularly rotate OAuth2 tokens

You're all set! 🎉