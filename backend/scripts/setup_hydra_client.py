#!/usr/bin/env python3
"""
Script to create an OAuth2 client in Hydra for the frontend application.
"""
import httpx
import os
import sys
import json

HYDRA_ADMIN_URL = os.getenv("HYDRA_ADMIN_URL", "http://hydra:4445")
HYDRA_CLIENT_ID = os.getenv("HYDRA_CLIENT_ID", "annie-defect-frontend")
HYDRA_CLIENT_SECRET = os.getenv("HYDRA_CLIENT_SECRET", "aXMjPMD7tl4OSczdcIUrYbE9J3X6G5jOxCL5isk9Zyo=")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8006")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5179")

def create_oauth_client():
    """Create or update the OAuth2 client in Hydra."""
    client_config = {
        "client_id": HYDRA_CLIENT_ID,
        "client_secret": HYDRA_CLIENT_SECRET,
        "client_name": "Annie Defect Frontend",
        "scope": "openid email profile",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "redirect_uris": [
            f"{BACKEND_URL}/auth/callback",
            f"{FRONTEND_URL}/auth/callback"
        ],
        "post_logout_redirect_uris": [
            f"{FRONTEND_URL}/logout"
        ],
        "token_endpoint_auth_method": "client_secret_post",
        "skip_consent": True  # For development - remove in production
    }
    
    # Try to create the client
    try:
        # First try to create
        response = httpx.post(
            f"{HYDRA_ADMIN_URL}/admin/clients",
            json=client_config
        )
        
        if response.status_code == 201:
            print(f"✅ OAuth2 client '{HYDRA_CLIENT_ID}' created successfully!")
            print(f"   Redirect URIs: {client_config['redirect_uris']}")
        elif response.status_code == 409:
            # Client already exists, try to update
            response = httpx.put(
                f"{HYDRA_ADMIN_URL}/admin/clients/{HYDRA_CLIENT_ID}",
                json=client_config
            )
            if response.status_code == 200:
                print(f"✅ OAuth2 client '{HYDRA_CLIENT_ID}' updated successfully!")
                print(f"   Redirect URIs: {client_config['redirect_uris']}")
            else:
                print(f"❌ Failed to update client: {response.status_code}")
                print(f"   Response: {response.text}")
                sys.exit(1)
        else:
            print(f"❌ Failed to create client: {response.status_code}")
            print(f"   Response: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error connecting to Hydra: {e}")
        print(f"   Make sure Hydra is running at {HYDRA_ADMIN_URL}")
        sys.exit(1)

if __name__ == "__main__":
    create_oauth_client()