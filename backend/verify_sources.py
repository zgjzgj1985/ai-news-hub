# -*- coding: utf-8 -*-
"""验证订阅源RSS链接的有效性"""
import sys
import requests
from pathlib import Path
import sqlite3
import os

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

print("=" * 60)
print("AI情报站 - 订阅源有效性验证")
print("=" * 60)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 获取所有订阅源
cursor.execute("SELECT id, name, url, enabled, last_fetched FROM feed_sources ORDER BY priority DESC")
sources = cursor.fetchall()

print(f"\n共 {len(sources)} 个订阅源待验证...\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

valid = []
invalid = []
unreachable = []

for row in sources:
    source_id, name, url, enabled, last_fetch = row
    status_icon = "[启用]" if enabled else "[禁用]"
    
    try:
        response = requests.get(url, headers=headers, timeout=(5, 15))
        if response.status_code == 200:
            valid.append((name, url, "正常"))
            print(f"[OK] {status_icon} {name}")
        elif response.status_code == 404:
            invalid.append((name, url, "404 Not Found"))
            print(f"[FAIL] {status_icon} {name} - 404 Not Found")
        elif response.status_code == 403:
            invalid.append((name, url, "403 Forbidden"))
            print(f"[FAIL] {status_icon} {name} - 403 Forbidden")
        else:
            unreachable.append((name, url, f"HTTP {response.status_code}"))
            print(f"[WARN] {status_icon} {name} - HTTP {response.status_code}")
    except requests.exceptions.Timeout:
        unreachable.append((name, url, "请求超时"))
        print(f"[WARN] {status_icon} {name} - 请求超时")
    except requests.exceptions.ConnectionError:
        unreachable.append((name, url, "连接失败"))
        print(f"[WARN] {status_icon} {name} - 连接失败")
    except Exception as e:
        unreachable.append((name, url, str(e)[:30]))
        print(f"[ERROR] {status_icon} {name} - {str(e)[:30]}")

print("\n" + "=" * 60)
print("验证结果汇总")
print("=" * 60)
print(f"\n[正常] {len(valid)} 个")
print(f"[失效] {len(invalid)} 个")
print(f"[不可达] {len(unreachable)} 个")

if invalid:
    print("\n【失效订阅源 - 需要修复】")
    for name, url, reason in invalid:
        print(f"  - {name}: {url}")
        print(f"    原因: {reason}")

if unreachable:
    print("\n【不可达订阅源 - 需要排查】")
    for name, url, reason in unreachable:
        print(f"  - {name}: {reason}")

conn.close()
