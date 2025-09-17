#!/usr/bin/env node

import { OAuth2Client } from 'google-auth-library';
import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import readline from 'readline';

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/gmail.labels',
  'https://www.googleapis.com/auth/gmail.compose',
];

const TOKEN_PATH = 'token.json';
const CREDENTIALS_PATH = 'credentials.json';

async function authorize() {
  try {
    // Load client secrets from credentials file
    if (!existsSync(CREDENTIALS_PATH)) {
      console.error(`
Error: Credentials file not found: ${CREDENTIALS_PATH}

To set up Gmail API access:
1. Go to the Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials file and save it as '${CREDENTIALS_PATH}'
6. Run this setup script again
      `);
      process.exit(1);
    }

    const credentials = JSON.parse(await readFile(CREDENTIALS_PATH, 'utf-8'));
    const { client_secret, client_id, redirect_uris } = credentials.web || credentials.installed;

    const oAuth2Client = new OAuth2Client(client_id, client_secret, redirect_uris[0]);

    // Check if we already have a token
    if (existsSync(TOKEN_PATH)) {
      console.log('Token already exists. Remove token.json if you want to re-authenticate.');
      return;
    }

    // Generate auth URL
    const authUrl = oAuth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
    });

    console.log('Authorize this app by visiting this url:', authUrl);

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    const code = await new Promise<string>((resolve) => {
      rl.question('Enter the code from that page here: ', (code) => {
        rl.close();
        resolve(code);
      });
    });

    try {
      const { tokens } = await oAuth2Client.getToken(code);
      await writeFile(TOKEN_PATH, JSON.stringify(tokens, null, 2));
      console.log('Token stored to', TOKEN_PATH);
      console.log('Setup complete! You can now use the Gmail MCP server.');
    } catch (error) {
      console.error('Error retrieving access token:', error);
      process.exit(1);
    }
  } catch (error) {
    console.error('Error during authorization:', error);
    process.exit(1);
  }
}

authorize();