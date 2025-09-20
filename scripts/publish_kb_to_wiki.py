#!/usr/bin/env python3
"""
CLI script for publishing KB files to MediaWiki
Usage:
  python scripts/publish_kb_to_wiki.py --kb-file docs/kb/ui_capabilities.json --wiki-url http://localhost:8080/w/api.php --username admin --password admin123
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.integrations.wiki_publisher import WikiPublisher


def main():
    parser = argparse.ArgumentParser(description="Publish KB file to MediaWiki")
    parser.add_argument("--kb-file", required=True, help="Path to KB JSON file")
    parser.add_argument("--wiki-url", required=True, help="MediaWiki API URL")
    parser.add_argument("--username", required=True, help="MediaWiki username")
    parser.add_argument("--password", required=True, help="MediaWiki password")
    parser.add_argument("--namespace", default="KB", help="Wiki namespace (default: KB)")
    parser.add_argument("--list", action="store_true", help="List published pages instead of publishing")
    parser.add_argument("--delete", help="Delete page with given title")
    
    args = parser.parse_args()
    
    # Validate KB file
    if not os.path.exists(args.kb_file):
        print(f"Error: KB file not found: {args.kb_file}")
        return 1
    
    try:
        publisher = WikiPublisher(args.wiki_url, args.username, args.password)
        
        if args.list:
            print(f"Listing pages in namespace '{args.namespace}':")
            pages = publisher.list_published_pages(args.namespace)
            if pages:
                for page in pages:
                    print(f"  • {page}")
            else:
                print("  No pages found")
            return 0
        
        if args.delete:
            print(f"Deleting page: {args.delete}")
            success, message = publisher.delete_wiki_page(args.delete)
            if success:
                print(f"✓ {message}")
                return 0
            else:
                print(f"✗ {message}")
                return 1
        
        # Publish KB file
        print(f"Publishing {args.kb_file} to {args.wiki_url}...")
        success, message = publisher.publish_kb_to_wiki(args.kb_file, args.namespace)
        
        if success:
            print(f"✓ {message}")
            return 0
        else:
            print(f"✗ {message}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
