# N8N Integration Guide

This guide provides detailed instructions for integrating the Gmail MCP Server with N8N workflows.

## Prerequisites

- N8N installed and running
- Gmail MCP Server set up and authenticated
- Basic understanding of N8N workflows

## Setup MCP Server in N8N

### Method 1: Using Execute Command Node

1. Add an "Execute Command" node to your workflow
2. Configure the command to start the MCP server:
   ```bash
   cd /path/to/MCP-Server && npm start
   ```

### Method 2: Using HTTP Request Node (Recommended)

For better integration, run the MCP server as a service and use HTTP requests to communicate.

## Example Workflows

### 1. Daily Email Summary

**Workflow**: Check for unread emails every morning and send a summary

```json
{
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "hour": 9,
          "minute": 0
        }
      }
    },
    {
      "name": "Search Unread Emails",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "node",
        "arguments": [
          "dist/index.js"
        ],
        "options": {
          "cwd": "/path/to/MCP-Server"
        }
      },
      "executeOnce": true
    }
  ]
}
```

### 2. Auto-Response for Important Emails

**Workflow**: Automatically respond to emails from VIP contacts

```javascript
// N8N JavaScript Code Node
const tool = "gmail_search_emails";
const args = {
  query: "is:unread from:vip@example.com",
  maxResults: 10
};

// Process each email found
for (const email of $json.emails) {
  // Send auto-response
  const responseArgs = {
    to: email.payload.headers.find(h => h.name === 'From').value,
    subject: `Re: ${email.payload.headers.find(h => h.name === 'Subject').value}`,
    body: "Thank you for your email. I'll review it shortly and respond within 24 hours."
  };
  
  // Mark original as read
  const modifyArgs = {
    messageId: email.id,
    removeLabelIds: ["UNREAD"]
  };
}

return { success: true };
```

### 3. Email Backup Workflow

**Workflow**: Backup emails to external storage

```json
{
  "trigger": "schedule_daily",
  "steps": [
    {
      "tool": "gmail_search_emails",
      "args": {
        "query": "older_than:30d",
        "maxResults": 100
      }
    },
    {
      "node": "process_emails",
      "code": "// Export emails to JSON format"
    },
    {
      "node": "save_to_cloud",
      "service": "google_drive"
    }
  ]
}
```

### 4. Smart Email Labeling

**Workflow**: Automatically label emails based on content

```javascript
// N8N Function Node for Smart Labeling
const emailContent = $json.email.snippet.toLowerCase();
const subject = $json.email.payload.headers
  .find(h => h.name === 'Subject').value.toLowerCase();

let labels = [];

// Business logic for labeling
if (emailContent.includes('invoice') || subject.includes('bill')) {
  labels.push('Finance');
}
if (emailContent.includes('meeting') || subject.includes('schedule')) {
  labels.push('Meetings');
}
if (emailContent.includes('urgent') || subject.includes('asap')) {
  labels.push('Urgent');
}

// Apply labels
if (labels.length > 0) {
  return {
    tool: "gmail_modify_email",
    args: {
      messageId: $json.email.id,
      addLabelIds: labels
    }
  };
}

return { skip: true };
```

## Advanced Integration Patterns

### 1. Webhook-Triggered Email Actions

Set up webhooks in N8N to trigger email actions:

```json
{
  "webhook_url": "https://your-n8n.com/webhook/gmail-action",
  "payload": {
    "action": "send_email",
    "to": "recipient@example.com",
    "subject": "Automated notification",
    "body": "This is an automated message triggered by webhook"
  }
}
```

### 2. Multi-Step Email Processing

Create complex workflows that process emails through multiple stages:

1. **Intake**: Search for new emails
2. **Classify**: Determine email type/priority
3. **Process**: Take appropriate action
4. **Archive**: Move to appropriate folder
5. **Notify**: Send notifications if needed

### 3. Email Analytics Dashboard

Use N8N to collect email statistics and send to analytics platforms:

```javascript
// N8N Analytics Collection Node
const stats = {
  date: new Date().toISOString().split('T')[0],
  unread_count: $json.unread_emails.length,
  sent_count: $json.sent_emails.length,
  important_emails: $json.emails.filter(e => 
    e.labelIds && e.labelIds.includes('IMPORTANT')
  ).length
};

// Send to analytics platform
return {
  url: 'https://analytics-api.com/email-stats',
  method: 'POST',
  body: stats
};
```

## Error Handling in N8N

### Retry Logic

```javascript
// N8N Error Handling Node
const maxRetries = 3;
let currentRetry = $json.retry || 0;

try {
  // Your Gmail MCP tool call here
  const result = await callGmailTool(tool, args);
  return result;
} catch (error) {
  if (currentRetry < maxRetries) {
    return {
      retry: currentRetry + 1,
      delay: Math.pow(2, currentRetry) * 1000, // Exponential backoff
      error: error.message
    };
  } else {
    // Send alert after max retries
    return {
      alert: true,
      error: `Failed after ${maxRetries} retries: ${error.message}`
    };
  }
}
```

### Error Notifications

```json
{
  "error_handler": {
    "type": "slack_notification",
    "webhook": "https://hooks.slack.com/your-webhook",
    "message": "Gmail MCP Server error: {{$json.error}}"
  }
}
```

## Performance Optimization

### 1. Batch Operations

Process multiple emails in batches to improve performance:

```javascript
// N8N Batch Processing Node
const emails = $json.emails;
const batchSize = 10;
const batches = [];

for (let i = 0; i < emails.length; i += batchSize) {
  batches.push(emails.slice(i, i + batchSize));
}

return batches.map((batch, index) => ({
  batch_id: index,
  emails: batch
}));
```

### 2. Caching

Cache frequently accessed data like labels:

```javascript
// N8N Caching Node
const cacheKey = 'gmail_labels';
const cacheExpiry = 3600000; // 1 hour

let labels = $workflow.getStaticData(cacheKey);
const now = Date.now();

if (!labels || (now - labels.timestamp) > cacheExpiry) {
  // Fetch fresh labels
  labels = {
    data: await callGmailTool('gmail_get_labels', {}),
    timestamp: now
  };
  $workflow.setStaticData(cacheKey, labels);
}

return labels.data;
```

## Security Best Practices

### 1. Credential Management

- Store MCP server credentials securely in N8N's credential system
- Use environment variables for sensitive configuration
- Regularly rotate OAuth2 tokens

### 2. Access Control

- Limit N8N workflow access to authorized users
- Use least-privilege principles for Gmail API scopes
- Monitor and log all email operations

### 3. Data Protection

- Encrypt sensitive email data in transit and at rest
- Implement data retention policies
- Comply with privacy regulations (GDPR, etc.)

## Monitoring and Logging

### 1. Workflow Monitoring

Set up monitoring for your Gmail workflows:

```json
{
  "monitoring": {
    "success_webhook": "https://monitoring.com/success",
    "error_webhook": "https://monitoring.com/error",
    "metrics": [
      "emails_processed",
      "response_time",
      "error_rate"
    ]
  }
}
```

### 2. Custom Logging

```javascript
// N8N Logging Node
const logEntry = {
  timestamp: new Date().toISOString(),
  workflow: $workflow.name,
  node: $node.name,
  action: $json.tool,
  status: $json.success ? 'success' : 'error',
  details: $json
};

// Send to logging service
await $http.post('https://logs.example.com/gmail-mcp', logEntry);
```

## Troubleshooting N8N Integration

### Common Issues

1. **Connection Timeouts**
   - Increase timeout settings in N8N nodes
   - Implement retry logic
   - Use async processing for large operations

2. **Memory Issues**
   - Process emails in smaller batches
   - Clear variables after processing
   - Use streaming for large datasets

3. **Rate Limiting**
   - Implement delays between API calls
   - Use exponential backoff
   - Monitor Gmail API quotas

### Debug Mode

Enable debug logging in both N8N and the MCP server:

```javascript
// N8N Debug Node
const debug = process.env.N8N_DEBUG === 'true';

if (debug) {
  console.log('Tool call:', tool, args);
  console.log('Response:', result);
}
```

## Example N8N Workflow Templates

See the `examples/n8n-workflows/` directory for complete workflow templates:

- `daily-email-summary.json` - Daily unread email summary
- `auto-responder.json` - Automatic email responses
- `email-backup.json` - Email backup and archiving
- `smart-labeling.json` - AI-powered email labeling
- `priority-alerts.json` - VIP email notifications

These templates can be imported directly into N8N and customized for your needs.