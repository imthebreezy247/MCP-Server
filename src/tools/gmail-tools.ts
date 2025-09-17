import { Tool, CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { GmailService } from '../services/gmail.js';
import {
  SendEmailInputSchema,
  SearchEmailsInputSchema,
  GetEmailInputSchema,
  ModifyEmailInputSchema,
  DeleteEmailInputSchema,
  CreateLabelInputSchema
} from '../types/gmail.js';

export class GmailTools {
  private gmailService: GmailService;

  constructor(gmailService: GmailService) {
    this.gmailService = gmailService;
  }

  /**
   * Get all available tools
   */
  getTools(): Tool[] {
    return [
      {
        name: 'gmail_send_email',
        description: 'Send an email through Gmail',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              type: ['string', 'array'],
              items: { type: 'string' },
              description: 'Recipient email address(es)'
            },
            subject: {
              type: 'string',
              description: 'Email subject'
            },
            body: {
              type: 'string',
              description: 'Email body content'
            },
            cc: {
              type: ['string', 'array'],
              items: { type: 'string' },
              description: 'CC email address(es)',
              optional: true
            },
            bcc: {
              type: ['string', 'array'],
              items: { type: 'string' },
              description: 'BCC email address(es)',
              optional: true
            }
          },
          required: ['to', 'subject', 'body']
        }
      },
      {
        name: 'gmail_search_emails',
        description: 'Search for emails in Gmail using Gmail search syntax',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Gmail search query (e.g., "from:example@gmail.com", "is:unread", "subject:important")'
            },
            maxResults: {
              type: 'number',
              minimum: 1,
              maximum: 500,
              default: 10,
              description: 'Maximum number of emails to return'
            },
            labelIds: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by specific label IDs',
              optional: true
            },
            includeSpamTrash: {
              type: 'boolean',
              default: false,
              description: 'Include spam and trash folders in search'
            }
          },
          required: ['query']
        }
      },
      {
        name: 'gmail_get_email',
        description: 'Get a specific email by its ID',
        inputSchema: {
          type: 'object',
          properties: {
            messageId: {
              type: 'string',
              description: 'Gmail message ID'
            },
            format: {
              type: 'string',
              enum: ['minimal', 'full', 'raw', 'metadata'],
              default: 'full',
              description: 'Format of the email to retrieve'
            }
          },
          required: ['messageId']
        }
      },
      {
        name: 'gmail_modify_email',
        description: 'Modify email labels (mark as read/unread, add/remove labels)',
        inputSchema: {
          type: 'object',
          properties: {
            messageId: {
              type: 'string',
              description: 'Gmail message ID'
            },
            addLabelIds: {
              type: 'array',
              items: { type: 'string' },
              description: 'Label IDs to add to the email',
              optional: true
            },
            removeLabelIds: {
              type: 'array',
              items: { type: 'string' },
              description: 'Label IDs to remove from the email',
              optional: true
            }
          },
          required: ['messageId']
        }
      },
      {
        name: 'gmail_delete_email',
        description: 'Delete an email permanently',
        inputSchema: {
          type: 'object',
          properties: {
            messageId: {
              type: 'string',
              description: 'Gmail message ID to delete'
            }
          },
          required: ['messageId']
        }
      },
      {
        name: 'gmail_get_labels',
        description: 'Get all Gmail labels/folders',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        }
      },
      {
        name: 'gmail_create_label',
        description: 'Create a new Gmail label/folder',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Name of the new label'
            },
            labelListVisibility: {
              type: 'string',
              enum: ['labelShow', 'labelShowIfUnread', 'labelHide'],
              default: 'labelShow',
              description: 'Visibility in the label list'
            },
            messageListVisibility: {
              type: 'string',
              enum: ['show', 'hide'],
              default: 'show',
              description: 'Visibility in the message list'
            }
          },
          required: ['name']
        }
      },
      {
        name: 'gmail_get_profile',
        description: 'Get Gmail user profile information',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        }
      },
      {
        name: 'gmail_auth_url',
        description: 'Get OAuth2 authorization URL for Gmail access',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        }
      },
      {
        name: 'gmail_auth_token',
        description: 'Exchange authorization code for access token',
        inputSchema: {
          type: 'object',
          properties: {
            code: {
              type: 'string',
              description: 'Authorization code from OAuth2 flow'
            }
          },
          required: ['code']
        }
      }
    ];
  }

  /**
   * Call a specific tool
   */
  async callTool(request: CallToolRequest): Promise<any> {
    const { name, arguments: args } = request.params;

    switch (name) {
      case 'gmail_send_email':
        return this.sendEmail(args);

      case 'gmail_search_emails':
        return this.searchEmails(args);

      case 'gmail_get_email':
        return this.getEmail(args);

      case 'gmail_modify_email':
        return this.modifyEmail(args);

      case 'gmail_delete_email':
        return this.deleteEmail(args);

      case 'gmail_get_labels':
        return this.getLabels();

      case 'gmail_create_label':
        return this.createLabel(args);

      case 'gmail_get_profile':
        return this.getProfile();

      case 'gmail_auth_url':
        return this.getAuthUrl();

      case 'gmail_auth_token':
        return this.getAuthToken(args);

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  private async sendEmail(args: any) {
    const input = SendEmailInputSchema.parse(args);
    const messageId = await this.gmailService.sendEmail(input);
    return {
      success: true,
      messageId,
      message: 'Email sent successfully'
    };
  }

  private async searchEmails(args: any) {
    const input = SearchEmailsInputSchema.parse(args);
    const emails = await this.gmailService.searchEmails(
      input.query,
      input.maxResults,
      input.labelIds
    );
    return {
      success: true,
      emails,
      count: emails.length
    };
  }

  private async getEmail(args: any) {
    const input = GetEmailInputSchema.parse(args);
    const email = await this.gmailService.getEmail(input.messageId, input.format);
    return {
      success: true,
      email
    };
  }

  private async modifyEmail(args: any) {
    const input = ModifyEmailInputSchema.parse(args);
    const email = await this.gmailService.modifyEmail(
      input.messageId,
      input.addLabelIds,
      input.removeLabelIds
    );
    return {
      success: true,
      email,
      message: 'Email modified successfully'
    };
  }

  private async deleteEmail(args: any) {
    const input = DeleteEmailInputSchema.parse(args);
    await this.gmailService.deleteEmail(input.messageId);
    return {
      success: true,
      message: 'Email deleted successfully'
    };
  }

  private async getLabels() {
    const labels = await this.gmailService.getLabels();
    return {
      success: true,
      labels
    };
  }

  private async createLabel(args: any) {
    const input = CreateLabelInputSchema.parse(args);
    const label = await this.gmailService.createLabel(
      input.name,
      input.labelListVisibility,
      input.messageListVisibility
    );
    return {
      success: true,
      label,
      message: 'Label created successfully'
    };
  }

  private async getProfile() {
    const profile = await this.gmailService.getProfile();
    return {
      success: true,
      profile
    };
  }

  private getAuthUrl() {
    const authUrl = this.gmailService.getAuthUrl();
    return {
      success: true,
      authUrl,
      message: 'Visit this URL to authorize the application'
    };
  }

  private async getAuthToken(args: any) {
    const { code } = args;
    if (!code) {
      throw new Error('Authorization code is required');
    }

    const credentials = await this.gmailService.getTokenFromCode(code);
    return {
      success: true,
      credentials,
      message: 'Authentication successful'
    };
  }
}