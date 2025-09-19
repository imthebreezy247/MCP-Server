# Gmail MCP Server OAuth 400 Error - Complete Solution Guide

## Quick Diagnosis

The "Error 400: invalid_request" with flowName=GeneralOAuthFlow indicates an OAuth configuration mismatch between your local credentials and Google Cloud Console settings.

## Immediate Fix Steps

### Step 1: Run Diagnostic Tool
```bash
cd /mnt/c/Coding-projects/MCP-Server
python3 fix_oauth_auth.py
```

This will:
- Validate your credentials.json file
- Test the authentication flow
- Provide specific error details

### Step 2: Fix Google Cloud Console Configuration

#### A. OAuth Consent Screen
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `gmail-mcp-server-472517`
3. Navigate to **APIs & Services** → **OAuth consent screen**
4. Check these settings:
   - **Publishing status**: Should be "Testing" or "In production"
   - If "Testing": Add your email to test users
   - **User type**: External or Internal
   - **App name**: Gmail MCP Server
   - **User support email**: Your email
   - **Developer contact**: Your email

#### B. Fix Redirect URIs
1. Go to **APIs & Services** → **Credentials**
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add ALL of these:
   ```
   http://localhost
   http://localhost/
   http://localhost:8080
   http://localhost:8080/
   http://127.0.0.1
   http://127.0.0.1/
   http://127.0.0.1:8080
   http://127.0.0.1:8080/
   urn:ietf:wg:oauth:2.0:oob
   ```
4. Click **SAVE**

#### C. Verify Gmail API
1. Go to **APIs & Services** → **Enabled APIs**
2. Confirm "Gmail API" is listed
3. If not, enable it

### Step 3: Clean Slate Authentication

```bash
# Remove old token
rm -f token.json

# Update local credentials file
python3 update_credentials.py

# Test authentication with manual mode
python3 gmail_mcp_server.py --manual-auth --test-auth
```

## Common Error Patterns and Solutions

### Error: "Access blocked: This app's request is invalid"
**Cause**: Redirect URI mismatch
**Solution**:
1. Copy the exact redirect_uri from the error message
2. Add it to Google Cloud Console authorized redirect URIs
3. Wait 5 minutes for propagation

### Error: "This app is blocked"
**Cause**: OAuth consent screen not configured
**Solution**:
1. Complete OAuth consent screen setup
2. Add test users if in testing mode
3. Consider publishing to production if needed

### Error: "The OAuth client was deleted"
**Cause**: Client ID no longer exists
**Solution**:
1. Create new OAuth 2.0 Client ID
2. Download new credentials.json
3. Replace the old file

### Error: "Authorization code was already redeemed"
**Cause**: Trying to use the same auth code twice
**Solution**: Start fresh authentication flow

## Alternative: Create New OAuth Client

If issues persist, create a fresh OAuth client:

```bash
# 1. In Google Cloud Console, create new OAuth 2.0 Client ID
# 2. Choose "Desktop app" type
# 3. Download JSON

# 4. Replace credentials file
mv credentials.json credentials.json.old
# Copy new downloaded file as credentials.json

# 5. Test
python3 fix_oauth_auth.py
```

## WSL-Specific Issues

If running in WSL:

1. **Browser won't open automatically**:
   ```bash
   python3 gmail_mcp_server.py --manual-auth
   ```

2. **Copy URL manually**:
   - The script will display an OAuth URL
   - Copy it completely
   - Paste in Windows browser
   - Copy auth code back

3. **Network issues**:
   ```bash
   # Check WSL can reach Google
   curl -I https://oauth2.googleapis.com/token
   ```

## Verification Checklist

- [ ] credentials.json exists and is valid JSON
- [ ] OAuth consent screen is configured
- [ ] Gmail API is enabled
- [ ] Redirect URIs match in both places
- [ ] Test users added (if in testing mode)
- [ ] token.json deleted before retry
- [ ] Using correct project in Google Cloud Console

## Debug Information

Run this to see the actual OAuth URL being generated:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    ['https://www.googleapis.com/auth/gmail.modify']
)
auth_url, _ = flow.authorization_url(prompt='consent')
print(auth_url)
```

Check for:
- Correct client_id
- Proper redirect_uri encoding
- Valid scope parameter

## Still Having Issues?

1. **Check token.json permissions**:
   ```bash
   ls -la token.json
   # Should be readable/writable
   ```

2. **Test with curl**:
   ```bash
   # Test if you can reach Google OAuth
   curl -I https://accounts.google.com/o/oauth2/auth
   ```

3. **Enable verbose logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Try OAuth Playground**:
   - Go to: https://developers.google.com/oauthplayground/
   - Test your client credentials there

## Success Indicators

When working correctly, you should see:
```
✅ Authentication successful!
✅ Connected to: your-email@gmail.com
✅ Total messages: XXXX
✅ Total threads: XXXX
Gmail MCP Server is ready to use!
```

## Contact Support

If none of these solutions work:
1. Document the exact error message
2. Save the OAuth URL that's generated
3. Note your Google Cloud project ID
4. Check Google Cloud Console for any warnings/alerts