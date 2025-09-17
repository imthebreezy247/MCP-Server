#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ToolSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { gmail_v1, google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import { z } from 'zod';
import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';

// Gmail MCP Server
// Provides comprehensive Gmail functionality through MCP tools

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/gmail.labels',
  'https://www.googleapis.com/auth/gmail.compose',
];

const TOKEN_PATH = 'token.json';
const CREDENTIALS_PATH = 'credentials.json';

class GmailMCPServer {
  private server: Server;
  private gmail: gmail_v1.Gmail | null = null;

  constructor() {
    this.server = new Server(
      { name: 'gmail-mcp-server', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'list_emails',
          description: 'List emails with optional filters (sender, subject, date range, labels)',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Gmail search query (e.g., "from:sender@example.com", "subject:important", "is:unread")',
              },
              maxResults: {
                type: 'number',
                description: 'Maximum number of emails to return (default: 10, max: 500)',
                default: 10,
              },
              labelIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Filter by label IDs',
              },
            },
          },
        },
        {
          name: 'get_email',
          description: 'Get detailed information about a specific email',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: {
                type: 'string',
                description: 'Gmail message ID',
              },
              format: {
                type: 'string',
                enum: ['minimal', 'full', 'raw', 'metadata'],
                description: 'Email format to retrieve',
                default: 'full',
              },
            },
            required: ['messageId'],
          },
        },
        {
          name: 'send_email',
          description: 'Send a new email',
          inputSchema: {
            type: 'object',
            properties: {
              to: {
                type: 'string',
                description: 'Recipient email address(es), comma-separated',
              },
              cc: {
                type: 'string',
                description: 'CC email address(es), comma-separated',
              },
              bcc: {
                type: 'string',
                description: 'BCC email address(es), comma-separated',
              },
              subject: {
                type: 'string',
                description: 'Email subject',
              },
              body: {
                type: 'string',
                description: 'Email body (HTML or plain text)',
              },
              isHtml: {
                type: 'boolean',
                description: 'Whether the body is HTML',
                default: false,
              },
            },
            required: ['to', 'subject', 'body'],
          },
        },
        {
          name: 'reply_to_email',
          description: 'Reply to an existing email',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: {
                type: 'string',
                description: 'Original message ID to reply to',
              },
              body: {
                type: 'string',
                description: 'Reply body',
              },
              isHtml: {
                type: 'boolean',
                description: 'Whether the body is HTML',
                default: false,
              },
              replyAll: {
                type: 'boolean',
                description: 'Reply to all recipients',
                default: false,
              },
            },
            required: ['messageId', 'body'],
          },
        },
        {
          name: 'modify_email',
          description: 'Modify email labels (mark as read/unread, archive, delete, add/remove labels)',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: {
                type: 'string',
                description: 'Gmail message ID',
              },
              addLabelIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Label IDs to add',
              },
              removeLabelIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Label IDs to remove',
              },
            },
            required: ['messageId'],
          },
        },
        {
          name: 'get_labels',
          description: 'Get all available Gmail labels',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'create_label',
          description: 'Create a new Gmail label',
          inputSchema: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: 'Label name',
              },
              messageListVisibility: {
                type: 'string',
                enum: ['show', 'hide'],
                description: 'Message list visibility',
                default: 'show',
              },
              labelListVisibility: {
                type: 'string',
                enum: ['labelShow', 'labelShowIfUnread', 'labelHide'],
                description: 'Label list visibility',
                default: 'labelShow',
              },
            },
            required: ['name'],
          },
        },
        {
          name: 'search_emails',
          description: 'Advanced email search with multiple criteria',
          inputSchema: {
            type: 'object',
            properties: {
              from: {
                type: 'string',
                description: 'Search emails from specific sender',
              },
              to: {
                type: 'string',
                description: 'Search emails to specific recipient',
              },
              subject: {
                type: 'string',
                description: 'Search by subject keywords',
              },
              hasAttachment: {
                type: 'boolean',
                description: 'Filter emails with attachments',
              },
              isUnread: {
                type: 'boolean',
                description: 'Filter unread emails',
              },
              dateAfter: {
                type: 'string',
                description: 'Date after (YYYY/MM/DD format)',
              },
              dateBefore: {
                type: 'string',
                description: 'Date before (YYYY/MM/DD format)',
              },
              maxResults: {
                type: 'number',
                description: 'Maximum results to return',
                default: 50,
              },
            },
          },
        },
        {
          name: 'get_attachments',
          description: 'Get attachments from an email',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: {
                type: 'string',
                description: 'Gmail message ID',
              },
            },
            required: ['messageId'],
          },
        },
        {
          name: 'mark_as_read',
          description: 'Mark email(s) as read',
          inputSchema: {
            type: 'object',
            properties: {
              messageIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of message IDs to mark as read',
              },
            },
            required: ['messageIds'],
          },
        },
        {
          name: 'mark_as_unread',
          description: 'Mark email(s) as unread',
          inputSchema: {
            type: 'object',
            properties: {
              messageIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of message IDs to mark as unread',
              },
            },
            required: ['messageIds'],
          },
        },
        {
          name: 'archive_emails',
          description: 'Archive email(s)',
          inputSchema: {
            type: 'object',
            properties: {
              messageIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of message IDs to archive',
              },
            },
            required: ['messageIds'],
          },
        },
        {
          name: 'delete_emails',
          description: 'Delete email(s) permanently',
          inputSchema: {
            type: 'object',
            properties: {
              messageIds: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of message IDs to delete',
              },
            },
            required: ['messageIds'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        await this.ensureGmailClient();

        switch (name) {
          case 'list_emails':
            return await this.listEmails(args);
          case 'get_email':
            return await this.getEmail(args);
          case 'send_email':
            return await this.sendEmail(args);
          case 'reply_to_email':
            return await this.replyToEmail(args);
          case 'modify_email':
            return await this.modifyEmail(args);
          case 'get_labels':
            return await this.getLabels();
          case 'create_label':
            return await this.createLabel(args);
          case 'search_emails':
            return await this.searchEmails(args);
          case 'get_attachments':
            return await this.getAttachments(args);
          case 'mark_as_read':
            return await this.markAsRead(args);
          case 'mark_as_unread':
            return await this.markAsUnread(args);
          case 'archive_emails':
            return await this.archiveEmails(args);
          case 'delete_emails':
            return await this.deleteEmails(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async ensureGmailClient() {
    if (this.gmail) return;

    try {
      // Load client secrets from credentials file
      if (!existsSync(CREDENTIALS_PATH)) {
        throw new Error(`Credentials file not found: ${CREDENTIALS_PATH}. Please download from Google Cloud Console.`);
      }

      const credentials = JSON.parse(await readFile(CREDENTIALS_PATH, 'utf-8'));
      const { client_secret, client_id, redirect_uris } = credentials.web || credentials.installed;

      const oAuth2Client = new OAuth2Client(client_id, client_secret, redirect_uris[0]);

      // Load existing token or require authorization
      if (existsSync(TOKEN_PATH)) {
        const token = JSON.parse(await readFile(TOKEN_PATH, 'utf-8'));
        oAuth2Client.setCredentials(token);
      } else {
        throw new Error('Token file not found. Please run authentication setup first.');
      }

      this.gmail = google.gmail({ version: 'v1', auth: oAuth2Client });
    } catch (error) {
      throw new Error(`Failed to initialize Gmail client: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async listEmails(args: any) {
    const { query = '', maxResults = 10, labelIds } = args;
    
    const response = await this.gmail!.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: Math.min(maxResults, 500),
      labelIds,
    });

    const messages = response.data.messages || [];
    const emailDetails = [];

    for (const message of messages.slice(0, maxResults)) {
      const detail = await this.gmail!.users.messages.get({
        userId: 'me',
        id: message.id!,
        format: 'metadata',
        metadataHeaders: ['From', 'Subject', 'Date'],
      });

      const headers = detail.data.payload?.headers || [];
      const from = headers.find(h => h.name === 'From')?.value || '';
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';

      emailDetails.push({
        id: message.id,
        from,
        subject,
        date,
        snippet: detail.data.snippet,
        labelIds: detail.data.labelIds,
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ emails: emailDetails, total: response.data.resultSizeEstimate }, null, 2),
        },
      ],
    };
  }

  private async getEmail(args: any) {
    const { messageId, format = 'full' } = args;

    const response = await this.gmail!.users.messages.get({
      userId: 'me',
      id: messageId,
      format,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(response.data, null, 2),
        },
      ],
    };
  }

  private async sendEmail(args: any) {
    const { to, cc, bcc, subject, body, isHtml = false } = args;

    const email = [
      `To: ${to}`,
      cc ? `Cc: ${cc}` : '',
      bcc ? `Bcc: ${bcc}` : '',
      `Subject: ${subject}`,
      `Content-Type: ${isHtml ? 'text/html' : 'text/plain'}; charset=utf-8`,
      '',
      body,
    ].filter(line => line !== '').join('\n');

    const encodedEmail = Buffer.from(email).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const response = await this.gmail!.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedEmail,
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ success: true, messageId: response.data.id }, null, 2),
        },
      ],
    };
  }

  private async replyToEmail(args: any) {
    const { messageId, body, isHtml = false, replyAll = false } = args;

    // Get original message
    const original = await this.gmail!.users.messages.get({
      userId: 'me',
      id: messageId,
      format: 'full',
    });

    const headers = original.data.payload?.headers || [];
    const from = headers.find(h => h.name === 'From')?.value || '';
    const to = headers.find(h => h.name === 'To')?.value || '';
    const cc = headers.find(h => h.name === 'Cc')?.value || '';
    const subject = headers.find(h => h.name === 'Subject')?.value || '';
    const messageIdHeader = headers.find(h => h.name === 'Message-ID')?.value || '';

    const replySubject = subject.startsWith('Re: ') ? subject : `Re: ${subject}`;
    const replyTo = from;
    const replyCc = replyAll ? cc : '';

    const email = [
      `To: ${replyTo}`,
      replyCc ? `Cc: ${replyCc}` : '',
      `Subject: ${replySubject}`,
      `In-Reply-To: ${messageIdHeader}`,
      `References: ${messageIdHeader}`,
      `Content-Type: ${isHtml ? 'text/html' : 'text/plain'}; charset=utf-8`,
      '',
      body,
    ].filter(line => line !== '').join('\n');

    const encodedEmail = Buffer.from(email).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const response = await this.gmail!.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedEmail,
        threadId: original.data.threadId,
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ success: true, messageId: response.data.id }, null, 2),
        },
      ],
    };
  }

  private async modifyEmail(args: any) {
    const { messageId, addLabelIds = [], removeLabelIds = [] } = args;

    const response = await this.gmail!.users.messages.modify({
      userId: 'me',
      id: messageId,
      requestBody: {
        addLabelIds,
        removeLabelIds,
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ success: true, labelIds: response.data.labelIds }, null, 2),
        },
      ],
    };
  }

  private async getLabels() {
    const response = await this.gmail!.users.labels.list({
      userId: 'me',
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ labels: response.data.labels }, null, 2),
        },
      ],
    };
  }

  private async createLabel(args: any) {
    const { name, messageListVisibility = 'show', labelListVisibility = 'labelShow' } = args;

    const response = await this.gmail!.users.labels.create({
      userId: 'me',
      requestBody: {
        name,
        messageListVisibility,
        labelListVisibility,
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ success: true, label: response.data }, null, 2),
        },
      ],
    };
  }

  private async searchEmails(args: any) {
    const {
      from,
      to,
      subject,
      hasAttachment,
      isUnread,
      dateAfter,
      dateBefore,
      maxResults = 50,
    } = args;

    let query = '';
    if (from) query += `from:${from} `;
    if (to) query += `to:${to} `;
    if (subject) query += `subject:${subject} `;
    if (hasAttachment) query += 'has:attachment ';
    if (isUnread) query += 'is:unread ';
    if (dateAfter) query += `after:${dateAfter} `;
    if (dateBefore) query += `before:${dateBefore} `;

    return await this.listEmails({ query: query.trim(), maxResults });
  }

  private async getAttachments(args: any) {
    const { messageId } = args;

    const message = await this.gmail!.users.messages.get({
      userId: 'me',
      id: messageId,
      format: 'full',
    });

    const attachments: any[] = [];
    
    const extractAttachments = (parts: any[]) => {
      for (const part of parts || []) {
        if (part.filename && part.body?.attachmentId) {
          attachments.push({
            filename: part.filename,
            mimeType: part.mimeType,
            size: part.body.size,
            attachmentId: part.body.attachmentId,
          });
        }
        if (part.parts) {
          extractAttachments(part.parts);
        }
      }
    };

    if (message.data.payload?.parts) {
      extractAttachments(message.data.payload.parts);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ attachments }, null, 2),
        },
      ],
    };
  }

  private async markAsRead(args: any) {
    const { messageIds } = args;
    const results = [];

    for (const messageId of messageIds) {
      try {
        await this.gmail!.users.messages.modify({
          userId: 'me',
          id: messageId,
          requestBody: {
            removeLabelIds: ['UNREAD'],
          },
        });
        results.push({ messageId, success: true });
      } catch (error) {
        results.push({ messageId, success: false, error: error instanceof Error ? error.message : String(error) });
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ results }, null, 2),
        },
      ],
    };
  }

  private async markAsUnread(args: any) {
    const { messageIds } = args;
    const results = [];

    for (const messageId of messageIds) {
      try {
        await this.gmail!.users.messages.modify({
          userId: 'me',
          id: messageId,
          requestBody: {
            addLabelIds: ['UNREAD'],
          },
        });
        results.push({ messageId, success: true });
      } catch (error) {
        results.push({ messageId, success: false, error: error instanceof Error ? error.message : String(error) });
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ results }, null, 2),
        },
      ],
    };
  }

  private async archiveEmails(args: any) {
    const { messageIds } = args;
    const results = [];

    for (const messageId of messageIds) {
      try {
        await this.gmail!.users.messages.modify({
          userId: 'me',
          id: messageId,
          requestBody: {
            removeLabelIds: ['INBOX'],
          },
        });
        results.push({ messageId, success: true });
      } catch (error) {
        results.push({ messageId, success: false, error: error instanceof Error ? error.message : String(error) });
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ results }, null, 2),
        },
      ],
    };
  }

  private async deleteEmails(args: any) {
    const { messageIds } = args;
    const results = [];

    for (const messageId of messageIds) {
      try {
        await this.gmail!.users.messages.delete({
          userId: 'me',
          id: messageId,
        });
        results.push({ messageId, success: true });
      } catch (error) {
        results.push({ messageId, success: false, error: error instanceof Error ? error.message : String(error) });
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ results }, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Gmail MCP server running on stdio');
  }
}

const server = new GmailMCPServer();
server.run().catch(console.error);