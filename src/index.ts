#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { GmailService } from './services/gmail.js';
import { GmailTools } from './tools/gmail-tools.js';
import { getGmailConfig, getServerConfig } from './utils/config.js';
import { logger } from './utils/logger.js';

class GmailMCPServer {
  private server: Server;
  private gmailService: GmailService;
  private gmailTools: GmailTools;

  constructor() {
    const serverConfig = getServerConfig();
    
    this.server = new Server(
      {
        name: serverConfig.name,
        version: serverConfig.version,
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    // Initialize Gmail service and tools
    const gmailConfig = getGmailConfig();
    this.gmailService = new GmailService(gmailConfig);
    this.gmailTools = new GmailTools(this.gmailService);

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      logger.info('Listing available tools');
      return {
        tools: this.gmailTools.getTools(),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name } = request.params;
      logger.info(`Calling tool: ${name}`);
      
      try {
        const result = await this.gmailTools.callTool(request);
        logger.info(`Tool ${name} executed successfully`);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        logger.error(`Tool ${name} failed:`, error);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
              }, null, 2),
            },
          ],
          isError: true,
        };
      }
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      logger.info('Listing available resources');
      
      const resources = [];
      
      // Try to load authentication status
      const isAuthenticated = await this.gmailService.loadCredentials() && this.gmailService.isAuthenticated();
      
      if (isAuthenticated) {
        try {
          const profile = await this.gmailService.getProfile();
          resources.push({
            uri: 'gmail://profile',
            name: 'Gmail Profile',
            description: `Gmail profile for ${profile.emailAddress}`,
            mimeType: 'application/json',
          });
          
          const labels = await this.gmailService.getLabels();
          resources.push({
            uri: 'gmail://labels',
            name: 'Gmail Labels',
            description: 'List of all Gmail labels/folders',
            mimeType: 'application/json',
          });
        } catch (error) {
          logger.warn('Failed to load Gmail resources:', error);
        }
      }

      resources.push({
        uri: 'gmail://auth-status',
        name: 'Authentication Status',
        description: 'Current Gmail authentication status',
        mimeType: 'application/json',
      });

      return { resources };
    });

    // Read specific resources
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      logger.info(`Reading resource: ${uri}`);

      try {
        switch (uri) {
          case 'gmail://profile':
            if (!this.gmailService.isAuthenticated()) {
              throw new Error('Not authenticated with Gmail');
            }
            const profile = await this.gmailService.getProfile();
            return {
              contents: [
                {
                  uri,
                  mimeType: 'application/json',
                  text: JSON.stringify(profile, null, 2),
                },
              ],
            };

          case 'gmail://labels':
            if (!this.gmailService.isAuthenticated()) {
              throw new Error('Not authenticated with Gmail');
            }
            const labels = await this.gmailService.getLabels();
            return {
              contents: [
                {
                  uri,
                  mimeType: 'application/json',
                  text: JSON.stringify(labels, null, 2),
                },
              ],
            };

          case 'gmail://auth-status':
            const authStatus = {
              isAuthenticated: this.gmailService.isAuthenticated(),
              authUrl: !this.gmailService.isAuthenticated() ? this.gmailService.getAuthUrl() : null,
              message: this.gmailService.isAuthenticated() 
                ? 'Authenticated with Gmail' 
                : 'Not authenticated. Use the authUrl to begin OAuth2 flow.'
            };
            return {
              contents: [
                {
                  uri,
                  mimeType: 'application/json',
                  text: JSON.stringify(authStatus, null, 2),
                },
              ],
            };

          default:
            throw new Error(`Unknown resource: ${uri}`);
        }
      } catch (error) {
        logger.error(`Failed to read resource ${uri}:`, error);
        throw error;
      }
    });
  }

  async start() {
    logger.info('Starting Gmail MCP Server...');
    
    try {
      // Try to load existing credentials
      const loaded = await this.gmailService.loadCredentials();
      if (loaded && this.gmailService.isAuthenticated()) {
        logger.info('Loaded existing Gmail credentials');
      } else {
        logger.info('No valid credentials found. Authentication required.');
        logger.info('Use the gmail_auth_url tool to get the authorization URL');
      }

      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      logger.info('Gmail MCP Server started successfully');
    } catch (error) {
      logger.error('Failed to start server:', error);
      process.exit(1);
    }
  }
}

// Start the server
async function main() {
  try {
    const server = new GmailMCPServer();
    await server.start();
  } catch (error) {
    logger.error('Server startup failed:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  process.exit(0);
});

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    logger.error('Unhandled error:', error);
    process.exit(1);
  });
}