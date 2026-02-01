#!/usr/bin/env python3
"""
Comment on a post on Moltbook.

Usage:
    python scripts/comment.py POST_ID "Your comment here"
    python scripts/comment.py --url https://moltbook.com/post/abc123 "Great post!"
    
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
        parts = url_or_id.rstrip('/').split('/')
        return parts[-1]
    return url_or_id


def comment_on_post(post_id: str, content: str, api_key: str = None) -> dict:
    """Comment on a post on Moltbook."""
    
    if not api_key:
        creds = load_credentials()
        api_key = creds.get('api_key')
    
    if not api_key:
        print("✗ No API key found. Register first with register.py", file=sys.stderr)
        sys.exit(1)
    
    # Extract post ID from URL if needed
    post_id = extract_post_id(post_id)
    
    # Prepare payload
    payload = {"content": content}
    
    def make_request():
        req = urllib.request.Request(
            f"{MOLTBOOK_API}/posts/{post_id}/comments",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "moltbook-skill"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    
    try:
        result = retry_request(make_request)
        
        comment_id = result.get('id', 'unknown')
        print(f"✓ Comment posted!")
        print(f"  Post: {post_id}")
        print(f"  Comment ID: {comment_id}")
        print(f"  Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        return result
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        if e.code == 404:
            print(f"✗ Post not found: {post_id}", file=sys.stderr)
        elif e.code == 400:
            print(f"✗ Invalid comment: {error_msg}", file=sys.stderr)
        else:
            print(f"✗ Comment failed: {e.code} - {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Comment failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Comment on a post on Moltbook")
    parser.add_argument("post_id", nargs='?', help="Post ID or URL")
    parser.add_argument("content", nargs='?', help="Comment content")
    parser.add_argument("--url", help="Post URL (alternative to post_id)")
    parser.add_argument("--api-key", help="API key (defaults to credentials.json)")
    args = parser.parse_args()
    
    post_id = args.post_id or args.url
    content = args.content
    
    if not post_id or not content:
        print("Error: Provide post ID/URL and comment content", file=sys.stderr)
        print("Example: python comment.py POST_ID \"Your comment\"", file=sys.stderr)
        sys.exit(1)
    
    comment_on_post(post_id, content, args.api_key)


if __name__ == "__main__":
    main()
