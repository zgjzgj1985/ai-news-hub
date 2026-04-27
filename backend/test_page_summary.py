# -*- coding: utf-8 -*-
"""测试页面摘要抓取"""

import requests
import feedparser
import sys
sys.stdout.reconfigure(encoding='utf-8')

from scraper.rss_parser import _fetch_page_summary

# 获取 HF 博客的真实 URL
url = 'https://huggingface.co/blog/feed.xml'
resp = requests.get(url, timeout=30)
feed = feedparser.parse(resp.content)

print('Testing page summary fetch for HuggingFace articles:')
print('=' * 60)

for i, entry in enumerate(feed.entries[:3]):
    article_url = entry.get('link', '')
    title = entry.get('title', '')[:50]
    print(f'\n{i+1}. Title: {title}...')
    print(f'   URL: {article_url}')

    summary = _fetch_page_summary(article_url)
    if summary:
        print(f'   Summary: {summary[:150]}...')
    else:
        print('   Summary: None')
