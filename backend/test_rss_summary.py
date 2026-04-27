# -*- coding: utf-8 -*-
"""测试 RSS 摘要获取"""

import requests
import feedparser
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 测试 Hugging Face Blog RSS
url = 'https://huggingface.co/blog/feed.xml'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
}

resp = requests.get(url, headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'Content length: {len(resp.content)}')

feed = feedparser.parse(resp.content)
print(f'Entries: {len(feed.entries)}')

if feed.entries:
    entry = feed.entries[0]
    print(f'\nFirst entry:')
    print(f'  Title: {entry.get("title", "")[:60]}...')
    print(f'  Has summary: {bool(entry.get("summary"))}')
    print(f'  Has content: {bool(entry.get("content"))}')
    print(f'  Summary length: {len(entry.get("summary", ""))}')
    
    if entry.get('content'):
        for c in entry.get('content', []):
            print(f'  Content value length: {len(c.get("value", ""))}')
            print(f'  Content preview: {c.get("value", "")[:150]}...')
    
    # 检查所有字段
    print(f'\nAll keys: {list(entry.keys())}')
