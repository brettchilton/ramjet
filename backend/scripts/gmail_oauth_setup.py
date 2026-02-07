#!/usr/bin/env python3
"""
One-time Gmail OAuth2 setup script.

Prerequisites:
  1. Go to Google Cloud Console → APIs & Services → Credentials
  2. Create an OAuth 2.0 Client ID (Desktop app type)
  3. Download the JSON and save it as `client_secret.json` in this directory

Usage:
  python gmail_oauth_setup.py

This opens a browser for Google sign-in. After consent, it prints the
three env vars you need to add to your .env file.
"""

import json
import os
import sys

# Ensure google packages are importable
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: google-auth-oauthlib not installed.")
    print("Run: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")


def main():
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERROR: {CLIENT_SECRET_FILE} not found.")
        print("Download your OAuth client JSON from Google Cloud Console")
        print("and save it as 'client_secret.json' in the scripts/ directory.")
        sys.exit(1)

    print("Starting OAuth2 consent flow...")
    print("A browser window will open for Google sign-in.\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=8090)

    # Read client_id and client_secret from the JSON file
    with open(CLIENT_SECRET_FILE) as f:
        client_config = json.load(f)

    # Handle both "installed" and "web" app types
    app_config = client_config.get("installed") or client_config.get("web", {})
    client_id = app_config.get("client_id", "")
    client_secret = app_config.get("client_secret", "")

    print("\n" + "=" * 60)
    print("SUCCESS! Add these to your .env file:")
    print("=" * 60)
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print(f"GMAIL_POLL_INTERVAL_SECONDS=60")
    print("=" * 60)


if __name__ == "__main__":
    main()
