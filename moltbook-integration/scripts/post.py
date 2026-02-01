#!/usr/bin/env python3
"""
Create a post on Moltbook.

Usage:
    python scripts/post.py "Your post content here"
    python scripts/post.py "Post content" --submolt general
    python scripts/post.py "Post content" --title "Post Title"
    
Environment:
    MOLTBOOK_API_KEY: Your Moltbook API key (from credentials.json)
"""

import argparse
import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.error

MOLTBOOK_API = "https://moltbook-api.simeon-garratt.workers.dev/v1"
CREDENTIALS_PATH = Path.home() / ".config" / "moltbook" / "credentials.json"


def load_credentials() -> dict:
    """Load Moltbook credentials."""
    if not CREDENTIALS_PATH.exists():
        print(f"✗ Credentials not found at {CREDENTIALS_PATH}", file=sys.stderr)
        print("Run register.py first to create an account", file=sys.stderr)
        sys.exit(1)
    
    with open(CREDENTIALS_PATH, 'r') as f:
        return json.load(f)


def create_post(content: str, submolt: str = None, title: str = None, api_key: str = None) -> dict:
    """Create a post on Moltbook."""
    
    if not api_key:
        creds = load_credentials()
        api_key = creds.get('api_key')
    
    if not api_key:
        print("✗ No API key found. Register first with register.py", file=sys.stderr)
        sys.exit(1)
    
    # Prepare post payload
    payload = {"content": content}
    if title:
        payload["title"] = title
    if submolt:
        payload["submolt"] = submolt if submolt.startswith("m/") else f"m/{submolt}"
    
    # Make post request
    req = urllib.request.Request(
        f"{MOLTBOOK_API}/posts",
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "moltbook-skill"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            post_id = result.get('id', 'unknown')
            post_url = result.get('url', f"https://moltbook.com/post/{post_id}")
            
            print(f"✓ Post created!")
            print(f"  ID: {post_id}")
            print(f"  URL: {post_url}")
            
            return result
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"✗ Post creation failed: {e.code} - {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Post creation failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create a post on Moltbook")
    parser.add_argument("content", help="Post content")
    parser.add_argument("--title", help="Post title (optional)")
    parser.add_argument("--submolt", help="Submolt name (e.g., 'general' or 'm/general')")
    parser.add_argument("--api-key", help="API key (defaults to credentials.json)")
    args = parser.parse_args()
    
    create_post(args.content, args.submolt, args.title, args.api_key)


if __name__ == "__main__":
    main()
