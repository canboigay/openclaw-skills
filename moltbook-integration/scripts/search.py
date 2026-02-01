#!/usr/bin/env python3
"""
Search posts on Moltbook.

Usage:
    python scripts/search.py "search query"
    python scripts/search.py "ai agents" --submolt general
    python scripts/search.py "OpenClaw" --limit 20
    
Environment:
    MOLTBOOK_API_KEY: Your Moltbook API key (from credentials.json)
"""

import argparse
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse
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
            if e.code == 429:
                if attempt < max_retries - 1:
                    wait = backoff ** attempt
                    print(f"⏳ Rate limited. Waiting {wait}s...", file=sys.stderr)
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


def search_posts(query: str, submolt: str = None, limit: int = 10, api_key: str = None) -> dict:
    """Search posts on Moltbook."""
    
    if not api_key:
        creds = load_credentials()
        api_key = creds.get('api_key')
    
    if not api_key:
        print("✗ No API key found. Register first with register.py", file=sys.stderr)
        sys.exit(1)
    
    # Build query parameters
    params = {
        'q': query,
        'limit': limit
    }
    if submolt:
        params['submolt'] = submolt if submolt.startswith('m/') else f'm/{submolt}'
    
    query_string = urllib.parse.urlencode(params)
    url = f"{MOLTBOOK_API}/search?{query_string}"
    
    def make_request():
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "moltbook-skill"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    
    try:
        result = retry_request(make_request)
        
        posts = result.get('posts', [])
        total = result.get('total', len(posts))
        
        # Pretty print results
        print("=" * 70)
        print(f"Search: '{query}' {f'in {submolt}' if submolt else ''}")
        print(f"Found: {total} results (showing {len(posts)})")
        print("=" * 70 + "\n")
        
        if not posts:
            print("No results found.")
            return result
        
        for i, post in enumerate(posts, 1):
            author = post.get('author', {}).get('username', 'unknown')
            title = post.get('title', '')
            content = post.get('content', '')[:150]
            upvotes = post.get('upvotes', 0)
            comments = post.get('comment_count', 0)
            post_url = post.get('url', '')
            submolt_name = post.get('submolt', '')
            
            print(f"{i}. u/{author} • {submolt_name} • ⬆ {upvotes} • 💬 {comments}")
            if title:
                print(f"   {title}")
            print(f"   {content}{'...' if len(post.get('content', '')) > 150 else ''}")
            print(f"   {post_url}\n")
        
        return result
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"✗ Search failed: {e.code} - {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Search failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Search posts on Moltbook")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--submolt", help="Limit search to specific submolt")
    parser.add_argument("--limit", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--api-key", help="API key (defaults to credentials.json)")
    args = parser.parse_args()
    
    search_posts(args.query, args.submolt, args.limit, args.api_key)


if __name__ == "__main__":
    main()
