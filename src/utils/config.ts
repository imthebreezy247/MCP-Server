import dotenv from 'dotenv';
import { GmailConfig } from '../types/gmail.js';

// Load environment variables
dotenv.config();

export function getGmailConfig(): GmailConfig {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI;

  if (!clientId || !clientSecret || !redirectUri) {
    throw new Error(
      'Missing required Google OAuth2 configuration. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI environment variables.'
    );
  }

  return {
    clientId,
    clientSecret,
    redirectUri,
    credentialsPath: process.env.CREDENTIALS_PATH
  };
}

export function getServerConfig() {
  return {
    name: process.env.MCP_SERVER_NAME || 'gmail-mcp-server',
    version: process.env.MCP_SERVER_VERSION || '1.0.0',
    logLevel: process.env.LOG_LEVEL || 'info'
  };
}