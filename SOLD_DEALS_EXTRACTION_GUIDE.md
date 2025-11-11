# Sold Deals Email Extraction Guide

## Overview
This guide will help you extract sold deal emails from 4 Gmail accounts with specific label filtering.

### Accounts to Process
1. danielhera.ushealth@gmail.com
2. jordang.ushealth@gmail.com
3. danielberman.ushealth@gmail.com
4. richardodle.ushealth@gmail.com

### Email Filtering Criteria

**INCLUDE emails with these labels:**
- `processed-sold-deals-using-automation-to-final-label`
- `sold-deal-paid---sold-deals`

**EXCLUDE emails with these labels (DEAD deals):**
- `aca-leads-to-be-worked-dead-deal`
- `aca-leads-to-be-worked-tanya-deals-processed-tanya-sold-deals`
- `aca-leads-to-be-worked-tanya-deals-tanya-sold-deals`
- `aca-leads-to-be-worked-tanya-deals`

### Data Extracted from Each Email
- First Name
- Last Name
- Agent Name (from sender)
- Phone Number
- Email address (client email)
- Premium (dollar amount)
- Subject
- Date
- Source Account

## Setup Instructions

### Step 1: Obtain OAuth Credentials from Google

You need OAuth 2.0 credentials to access Gmail. Run the setup helper:

```bash
python3 setup_oauth_credentials.py
```

This interactive script will guide you through:
1. Opening Google Cloud Console
2. Creating/selecting a project
3. Enabling Gmail API
4. Creating OAuth 2.0 credentials
5. Downloading and installing the credentials

**Quick Steps for Google Cloud Console:**
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Gmail API in API Library
4. Go to Credentials → Create Credentials → OAuth client ID
5. Choose "Desktop app" as application type
6. Download the JSON file
7. Save it as `credentials.json` in `/home/user/MCP-Server/`

### Step 2: Run the Extraction Script

Once you have the credentials.json file in place, run:

```bash
python3 extract_sold_deals_multi_account.py
```

The script will:
1. Prompt you to authenticate each Gmail account (first time only)
2. Search for emails with the INCLUDE labels
3. Filter out emails with EXCLUDE labels
4. Extract client information from each email
5. Save results to JSON files

### Step 3: Authentication Process

For each account, you'll need to:
1. Copy the authentication URL shown in the terminal
2. Open it in a web browser
3. Sign in with the specific Gmail account (e.g., danielhera.ushealth@gmail.com)
4. Accept the permissions (Gmail read access)
5. Copy the authorization code
6. Paste it back in the terminal

**Note:** The authentication tokens are saved, so you only need to do this once per account.

## Output Files

The script creates these files:

### Individual Account Files
- `danielhera_ushealth_sold_deals.json`
- `jordang_ushealth_sold_deals.json`
- `danielberman_ushealth_sold_deals.json`
- `richardodle_ushealth_sold_deals.json`

### Consolidated Files
- `all_sold_deals_consolidated.json` - Organized by account
- `all_sold_deals_flat.json` - All records in a single array

## File Locations

All files are saved in: `/home/user/MCP-Server/`

## Troubleshooting

### "No OAuth credentials file found"
- Run `python3 setup_oauth_credentials.py` to set up credentials
- Make sure `credentials.json` exists in `/home/user/MCP-Server/`

### "Authentication failed"
- Make sure you're signing in with the correct Gmail account
- Check that Gmail API is enabled in your Google Cloud project
- Verify the OAuth consent screen is configured

### "No messages found"
- Verify the labels exist in the Gmail accounts
- Check that the label names match exactly (case-sensitive)

### "Permission denied" errors
- Make sure the OAuth app has Gmail readonly scope
- Re-authenticate by deleting the token file and running again

## Alternative Scripts Available

- `extract_all_sold_deals.py` - Original version (requires manual credential setup)
- `extract_sold_deals_multi_account.py` - Enhanced version with better error handling

## Summary Report

After successful extraction, you'll see:
- Total emails extracted per account
- Total across all accounts
- List of created files with full paths

## Security Notes

- The `credentials.json` file contains your OAuth app credentials - keep it secure
- Token files (`token_*.json`) contain access tokens - do not share them
- These files are gitignored to prevent accidental commits

## Next Steps

Once extraction is complete, you can:
1. Review the JSON files for data quality
2. Import into Excel or other tools for analysis
3. Process the data further as needed

For any issues or questions, refer to the error messages in the terminal output, which provide specific guidance for resolution.