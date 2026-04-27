"""
测试抓取功能
"""
import sys
sys.path.insert(0, '.')
from scraper.rss_parser import fetch_all_feeds

print('Starting feed fetch...')
result = fetch_all_feeds()
print()
print('=== Fetch Results ===')
print(f'Total added: {result["total_added"]}')
print(f'Total seen: {result["total_seen"]}')
print(f'Sources count: {result["sources_count"]}')
if result['errors']:
    print(f'Errors: {result["errors"]}')
