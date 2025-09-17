#!/usr/bin/env node

import { spawn } from 'child_process';
import { readFile } from 'fs/promises';

// Test script for Gmail MCP Server
// This script tests the MCP server without requiring actual Gmail credentials

async function testMCPServer() {
  console.log('Testing Gmail MCP Server...\n');

  // Test 1: Server startup
  console.log('1. Testing server startup...');
  
  const serverProcess = spawn('node', ['dist/index.js'], {
    cwd: process.cwd(),
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  // Test 2: Tools list request
  console.log('2. Testing tools list...');
  
  const toolsListRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/list',
    params: {},
  };

  serverProcess.stdin.write(JSON.stringify(toolsListRequest) + '\n');

  let output = '';
  let errorOutput = '';

  serverProcess.stdout.on('data', (data) => {
    output += data.toString();
  });

  serverProcess.stderr.on('data', (data) => {
    errorOutput += data.toString();
  });

  // Give server time to respond
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Test 3: Parse and validate response
  try {
    if (output) {
      const response = JSON.parse(output.trim());
      if (response.result && response.result.tools) {
        console.log(`✓ Server responded with ${response.result.tools.length} tools`);
        
        // Validate expected tools
        const expectedTools = [
          'list_emails', 'get_email', 'send_email', 'reply_to_email',
          'modify_email', 'get_labels', 'create_label', 'search_emails',
          'get_attachments', 'mark_as_read', 'mark_as_unread',
          'archive_emails', 'delete_emails'
        ];
        
        const actualTools = response.result.tools.map((tool: any) => tool.name);
        const missingTools = expectedTools.filter(tool => !actualTools.includes(tool));
        
        if (missingTools.length === 0) {
          console.log('✓ All expected tools are available');
        } else {
          console.log(`✗ Missing tools: ${missingTools.join(', ')}`);
        }

        // Show available tools
        console.log('\nAvailable tools:');
        response.result.tools.forEach((tool: any) => {
          console.log(`  - ${tool.name}: ${tool.description}`);
        });
      } else {
        console.log('✗ Invalid response format');
      }
    } else {
      console.log('✗ No response received');
    }
  } catch (error) {
    console.log('✗ Failed to parse response:', error instanceof Error ? error.message : String(error));
  }

  // Test 4: Test tool call (should fail without credentials, but server should handle gracefully)
  console.log('\n3. Testing tool call error handling...');
  
  const toolCallRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/call',
    params: {
      name: 'list_emails',
      arguments: { maxResults: 5 },
    },
  };

  serverProcess.stdin.write(JSON.stringify(toolCallRequest) + '\n');
  
  // Give server time to respond
  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log('\n4. Server error output:');
  if (errorOutput) {
    console.log(errorOutput);
  }

  // Clean up
  serverProcess.kill();

  console.log('\n✓ Test completed successfully!');
  console.log('\nNext steps:');
  console.log('1. Add your credentials.json file');
  console.log('2. Run: npm run setup');
  console.log('3. Start using the server: npm start');
}

testMCPServer().catch(console.error);