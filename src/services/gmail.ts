import { google, gmail_v1 } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import fs from 'fs/promises';
import path from 'path';
import { GmailConfig, GmailMessage, GmailLabel, SendEmailInput } from '../types/gmail.js';
import { AuthCredentials, MCPError } from '../types/mcp.js';

export class GmailService {
  private oauth2Client: OAuth2Client;
  private gmail: gmail_v1.Gmail;
  private config: GmailConfig;
  private credentialsPath: string;

  constructor(config: GmailConfig) {
    this.config = config;
    this.credentialsPath = config.credentialsPath || './credentials.json';
    
    this.oauth2Client = new google.auth.OAuth2(
      config.clientId,
      config.clientSecret,
      config.redirectUri
    );

    this.gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });
  }

  /**
   * Get authorization URL for OAuth2 flow
   */
  getAuthUrl(): string {
    const scopes = [
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.send',
      'https://www.googleapis.com/auth/gmail.modify',
      'https://www.googleapis.com/auth/gmail.labels'
    ];

    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent'
    });
  }

  /**
   * Exchange authorization code for tokens
   */
  async getTokenFromCode(code: string): Promise<AuthCredentials> {
    try {
      const { tokens } = await this.oauth2Client.getToken(code);
      this.oauth2Client.setCredentials(tokens);
      
      const credentials: AuthCredentials = {
        access_token: tokens.access_token!,
        refresh_token: tokens.refresh_token || undefined,
        scope: tokens.scope!,
        token_type: tokens.token_type!,
        expiry_date: tokens.expiry_date || undefined
      };

      await this.saveCredentials(credentials);
      return credentials;
    } catch (error) {
      throw new Error(`Failed to get token: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Load saved credentials
   */
  async loadCredentials(): Promise<boolean> {
    try {
      const data = await fs.readFile(this.credentialsPath, 'utf8');
      const credentials: AuthCredentials = JSON.parse(data);
      
      this.oauth2Client.setCredentials({
        access_token: credentials.access_token,
        refresh_token: credentials.refresh_token,
        scope: credentials.scope,
        token_type: credentials.token_type,
        expiry_date: credentials.expiry_date
      });

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Save credentials to file
   */
  async saveCredentials(credentials: AuthCredentials): Promise<void> {
    try {
      const dir = path.dirname(this.credentialsPath);
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(this.credentialsPath, JSON.stringify(credentials, null, 2));
    } catch (error) {
      throw new Error(`Failed to save credentials: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Check if authenticated
   */
  isAuthenticated(): boolean {
    return !!this.oauth2Client.credentials?.access_token;
  }

  /**
   * Send an email
   */
  async sendEmail(input: SendEmailInput): Promise<string> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const emailLines: string[] = [];
      
      // Recipients
      const toList = Array.isArray(input.to) ? input.to.join(', ') : input.to;
      emailLines.push(`To: ${toList}`);
      
      if (input.cc) {
        const ccList = Array.isArray(input.cc) ? input.cc.join(', ') : input.cc;
        emailLines.push(`Cc: ${ccList}`);
      }
      
      if (input.bcc) {
        const bccList = Array.isArray(input.bcc) ? input.bcc.join(', ') : input.bcc;
        emailLines.push(`Bcc: ${bccList}`);
      }

      emailLines.push(`Subject: ${input.subject}`);
      emailLines.push('');
      emailLines.push(input.body);

      const email = emailLines.join('\n');
      const encodedEmail = Buffer.from(email).toString('base64url');

      const response = await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          raw: encodedEmail
        }
      });

      return response.data.id!;
    } catch (error) {
      throw this.createError('SEND_EMAIL_FAILED', `Failed to send email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Search emails
   */
  async searchEmails(query: string, maxResults: number = 10, labelIds?: string[]): Promise<GmailMessage[]> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const searchResponse = await this.gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults,
        labelIds
      });

      const messages: GmailMessage[] = [];
      
      if (searchResponse.data.messages) {
        for (const message of searchResponse.data.messages) {
          const fullMessage = await this.gmail.users.messages.get({
            userId: 'me',
            id: message.id!,
            format: 'full'
          });
          
          messages.push(fullMessage.data as GmailMessage);
        }
      }

      return messages;
    } catch (error) {
      throw this.createError('SEARCH_EMAILS_FAILED', `Failed to search emails: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get a specific email by ID
   */
  async getEmail(messageId: string, format: string = 'full'): Promise<GmailMessage> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const response = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: format as any
      });

      return response.data as GmailMessage;
    } catch (error) {
      throw this.createError('GET_EMAIL_FAILED', `Failed to get email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Modify email labels
   */
  async modifyEmail(messageId: string, addLabelIds?: string[], removeLabelIds?: string[]): Promise<GmailMessage> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const response = await this.gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          addLabelIds,
          removeLabelIds
        }
      });

      return response.data as GmailMessage;
    } catch (error) {
      throw this.createError('MODIFY_EMAIL_FAILED', `Failed to modify email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Delete an email
   */
  async deleteEmail(messageId: string): Promise<void> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      await this.gmail.users.messages.delete({
        userId: 'me',
        id: messageId
      });
    } catch (error) {
      throw this.createError('DELETE_EMAIL_FAILED', `Failed to delete email: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get all labels
   */
  async getLabels(): Promise<GmailLabel[]> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const response = await this.gmail.users.labels.list({
        userId: 'me'
      });

      return (response.data.labels || []) as GmailLabel[];
    } catch (error) {
      throw this.createError('GET_LABELS_FAILED', `Failed to get labels: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Create a new label
   */
  async createLabel(name: string, labelListVisibility: string = 'labelShow', messageListVisibility: string = 'show'): Promise<GmailLabel> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const response = await this.gmail.users.labels.create({
        userId: 'me',
        requestBody: {
          name,
          labelListVisibility: labelListVisibility as any,
          messageListVisibility: messageListVisibility as any
        }
      });

      return response.data as GmailLabel;
    } catch (error) {
      throw this.createError('CREATE_LABEL_FAILED', `Failed to create label: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get user profile
   */
  async getProfile(): Promise<any> {
    if (!this.isAuthenticated()) {
      throw this.createError('NOT_AUTHENTICATED', 'Gmail service not authenticated');
    }

    try {
      const response = await this.gmail.users.getProfile({
        userId: 'me'
      });

      return response.data;
    } catch (error) {
      throw this.createError('GET_PROFILE_FAILED', `Failed to get profile: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private createError(code: string, message: string): MCPError {
    const error = new Error(message) as MCPError;
    error.code = code;
    return error;
  }
}