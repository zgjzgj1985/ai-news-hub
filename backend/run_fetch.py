# -*- coding: utf-8 -*-
"""运行 RSS 抓取脚本"""

import sys
import time
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from scraper.rss_parser import fetch_all_feeds

print("=" * 60)
print("RSS Feed Fetcher - 开始抓取")
print("=" * 60)

start = time.time()
result = fetch_all_feeds()
elapsed = time.time() - start

print(f"\n抓取完成！")
print(f"耗时: {elapsed:.1f} 秒")
print(f"新增文章: {result['total_added']}")
print(f"检查文章: {result['total_seen']}")
print(f"订阅源数量: {result['sources_count']}")

if result.get('sources_skipped'):
    print(f"跳过订阅源: {result['sources_skipped']}")

if result.get('skipped_reasons'):
    print(f"\n跳过原因:")
    for reason in result['skipped_reasons']:
        print(f"  - {reason}")

if result['errors']:
    print(f"\n抓取错误:")
    for error in result['errors']:
        print(f"  - {error}")
else:
    print("\n无抓取错误！")

print("=" * 60)
