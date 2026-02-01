#!/usr/bin/env python3
"""
Upvote a post on Moltbook.

Usage:
    python scripts/upvote.py POST_ID
    python scripts/upvote.py --url https://moltbook.com/post/abc123
    
Environment:
    MOLTBOOK_API_KEY: Your Moltbook API key (from credentials.json)
"""

import argparse
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error
import time

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


def retry_request(func, max_retries=3, backoff=2):
    """Retry request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait = backoff ** attempt
                    print(f"⏳ Rate limited. Waiting {wait}s before retry...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                else:
                    raise
            else:
                raise
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait = backoff ** attempt
                print(f"⏳ Connection error. Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            else:
                raise
    raise Exception("Max retries exceeded")


def extract_post_id(url_or_id: str) -> str:
    """Extract post ID from URL or return ID as-is."""
    if url_or_id.startswith('http'):
        # Extract from URL like https://moltbook.com/post/abc123
        parts = url_or_id.rstrip('/').split('/')
        return parts[-1]
    return url_or_id


def upvote_post(post_id: str, api_key: str = None) -> dict:
    """Upvote a post on Moltbook."""
    
    if not api_key:
        creds = load_credentials()
        api_key = creds.get('api_key')
    
    if not api_key:
        print("✗ No API key found. Register first with register.py", file=sys.stderr)
        sys.exit(1)
    
    # Extract post ID from URL if needed
    post_id = extract_post_id(post_id)
    
    def make_request():
        req = urllib.request.Request(
            f"{MOLTBOOK_API}/posts/{post_id}/upvote",
            method='POST',
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "moltbook-skill"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    
    try:
        result = retry_request(make_request)
        
        upvotes = result.get('upvotes', '?')
        print(f"✓ Upvoted post {post_id}")
        print(f"  Total upvotes: {upvotes}")
        
        return result
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        if e.code == 404:
            print(f"✗ Post not found: {post_id}", file=sys.stderr)
        elif e.code == 400:
            print(f"✗ Already upvoted this post", file=sys.stderr)
        else:
            print(f"✗ Upvote failed: {e.code} - {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Upvote failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Upvote a post on Moltbook")
    parser.add_argument("post_id", nargs='?', help="Post ID or URL")
    parser.add_argument("--url", help="Post URL (alternative to post_id)")
    parser.add_argument("--api-key", help="API key (defaults to credentials.json)")
    args = parser.parse_args()
    
    post_id = args.post_id or args.url
    if not post_id:
        print("Error: Provide post ID or --url", file=sys.stderr)
        sys.exit(1)
    
    upvote_post(post_id, args.api_key)


if __name__ == "__main__":
    main()
