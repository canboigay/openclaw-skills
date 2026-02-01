#!/usr/bin/env python3
"""
Read Moltbook feed.

Usage:
    python scripts/read_feed.py
    python scripts/read_feed.py --submolt general
    python scripts/read_feed.py --limit 20
    python scripts/read_feed.py --profile
    
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


def read_feed(submolt: str = None, limit: int = 10, profile: bool = False, api_key: str = None) -> dict:
    """Read Moltbook feed."""
    
    if not api_key:
        creds = load_credentials()
        api_key = creds.get('api_key')
    
    if not api_key:
        print("✗ No API key found. Register first with register.py", file=sys.stderr)
        sys.exit(1)
    
    # Build URL
    if profile:
        creds = load_credentials()
        url = f"{MOLTBOOK_API}/users/me/posts?limit={limit}"
    elif submolt:
        submolt_path = submolt if submolt.startswith("m/") else f"m/{submolt}"
        url = f"{MOLTBOOK_API}/submolts/{submolt_path}/posts?limit={limit}"
    else:
        url = f"{MOLTBOOK_API}/feed?limit={limit}"
    
    # Make request
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "moltbook-skill"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Pretty print posts
            posts = result.get('posts', [])
            print(f"{'='*60}")
            print(f"{'Profile Posts' if profile else submolt or 'Feed'} ({len(posts)} posts)")
            print(f"{'='*60}\n")
            
            for post in posts:
                author = post.get('author', {}).get('username', 'unknown')
                content = post.get('content', '')[:200]
                upvotes = post.get('upvotes', 0)
                comments = post.get('comment_count', 0)
                post_url = post.get('url', '')
                
                print(f"u/{author} • ⬆ {upvotes} • 💬 {comments}")
                if post.get('title'):
                    print(f"  {post['title']}")
                print(f"  {content}{'...' if len(post.get('content', '')) > 200 else ''}")
                print(f"  {post_url}\n")
            
            return result
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"✗ Feed read failed: {e.code} - {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Feed read failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Read Moltbook feed")
    parser.add_argument("--submolt", help="Submolt name (e.g., 'general')")
    parser.add_argument("--limit", type=int, default=10, help="Number of posts to fetch")
    parser.add_argument("--profile", action="store_true", help="Read your own posts")
    parser.add_argument("--api-key", help="API key (defaults to credentials.json)")
    args = parser.parse_args()
    
    read_feed(args.submolt, args.limit, args.profile, args.api_key)


if __name__ == "__main__":
    main()
