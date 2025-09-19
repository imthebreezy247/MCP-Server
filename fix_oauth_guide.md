# Gmail MCP Server OAuth Fix Guide

## Step 1: Google Cloud Console Configuration

1. **Access Google Cloud Console**
   - Go to: https://console.cloud.google.com/
   - Select your project: `gmail-mcp-server-472517`

2. **Check OAuth Consent Screen Status**
   - Navigate to: APIs & Services → OAuth consent screen
   - Verify the following:
     - **Publishing status**: Should be "In production" or "Testing"
     - **User type**: Should be "External" or "Internal"
   - If in "Testing" mode:
     - Add your email to the test users list
     - Click "ADD USERS" and enter your Gmail address

3. **Fix OAuth 2.0 Client Configuration**
   - Go to: APIs & Services → Credentials
   - Find your OAuth 2.0 Client ID (ending in `.apps.googleusercontent.com`)
   - Click on it to edit
   - **Important**: Update the Authorized redirect URIs:
     ```
     http://localhost
     http://localhost:8080
     http://localhost:8080/
     http://127.0.0.1
     http://127.0.0.1:8080
     http://127.0.0.1:8080/
     urn:ietf:wg:oauth:2.0:oob
     ```
   - Click "SAVE"

4. **Verify Gmail API is Enabled**
   - Go to: APIs & Services → Enabled APIs
   - Ensure "Gmail API" is listed
   - If not, click "ENABLE APIS AND SERVICES" and search for "Gmail API"

## Step 2: Create New OAuth Client (Alternative Approach)

If the above doesn't work, create a new OAuth client:

1. **Delete existing client and create new**
   - Go to: APIs & Services → Credentials
   - Delete the current OAuth 2.0 Client
   - Click "CREATE CREDENTIALS" → "OAuth client ID"
   - Choose "Desktop app" as Application type
   - Name it "Gmail MCP Server"
   - Click "CREATE"
   - Download the new credentials JSON

2. **Replace credentials.json**
   - Save the downloaded file as `credentials.json` in `/mnt/c/Coding-projects/MCP-Server/`

## Step 3: Test Manual Authentication

Run the server with manual authentication flag:
```bash
cd /mnt/c/Coding-projects/MCP-Server
python3 gmail_mcp_server.py --manual-auth --test-auth
```

## Step 4: Alternative - Use Web Application Type

If Desktop type continues to fail:

1. **Create Web Application OAuth Client**
   - Go to: APIs & Services → Credentials
   - Click "CREATE CREDENTIALS" → "OAuth client ID"
   - Choose "Web application"
   - Add Authorized redirect URIs:
     ```
     http://localhost:8080
     http://localhost:8080/
     ```
   - Download and save as credentials.json

## Step 5: Clear Cache and Tokens

Remove any existing token files:
```bash
rm -f token.json
```

## Step 6: Debug OAuth URL

If still getting errors, inspect the generated OAuth URL:
1. Run the authentication manually
2. Copy the generated URL
3. Check for these parameters:
   - `client_id` should match your credentials.json
   - `redirect_uri` should be properly encoded
   - `scope` should be present

## Common Issues and Solutions

### Issue: "Access blocked: This app's request is invalid"
**Solution**: The redirect URI in the URL doesn't match configured URIs in Google Cloud Console

### Issue: "The OAuth client was not found"
**Solution**: The client_id is incorrect or the OAuth client was deleted

### Issue: "Redirect URI mismatch"
**Solution**: Add all variations of localhost URLs to authorized redirect URIs

### Issue: "This app is blocked"
**Solution**: OAuth consent screen needs to be configured properly or app needs verification

## Verification Steps

After fixing, verify with:
```bash
python3 gmail_mcp_server.py --test-auth
```

Expected output:
```
Testing Gmail authentication...
✓ Authentication successful!
✓ Connected to: your-email@gmail.com
✓ Total messages: XXXX
✓ Total threads: XXXX
Gmail MCP Server is ready to use!
```