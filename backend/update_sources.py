# -*- coding: utf-8 -*-
"""更新订阅源URL脚本 - 修复失效的RSS源"""

import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

print("=" * 60)
print("更新订阅源URL - 修复失效RSS")
print("=" * 60)

# 需要更新的订阅源映射
SOURCE_UPDATES = [
    # (原URL, 新URL, 新名称, 新优先级, 是否启用)
    ("https://www.anthropic.com/blog/rss.xml",
     "https://www.anthropic.com/news/feed_anthropic.xml",
     "Anthropic Blog", 9, True),

    ("https://stability.ai/news/feed",
     "https://stability.ai/news?format=rss",
     "Stability AI Blog", 8, True),

    ("https://venturebeat.com/ai/feed/",
     "https://venturebeat.com/feed/",
     "VentureBeat AI", 7, True),

    ("https://simonwillison.net/atom Eintraege",
     "https://simonwillison.net/atom/everything/",
     "Simon Willison", 7, True),

    # Game Developer - 尝试备用源
    ("https://www.gamedeveloper.com/rss.xml",
     "http://www.gamasutra.com/rss/",  # Gamasutra是Game Developer的前身
     "Game Developer", 6, True),
]

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

updated_count = 0
for old_url, new_url, new_name, new_priority, enabled in SOURCE_UPDATES:
    cursor.execute("""
        UPDATE feed_sources
        SET url = ?, name = ?, priority = ?, enabled = ?
        WHERE url = ?
    """, (new_url, new_name, new_priority, enabled, old_url))

    if cursor.rowcount > 0:
        print(f"[OK] 已更新: {new_name}")
        print(f"      {old_url[:50]}...")
        print(f"      -> {new_url}")
        updated_count += cursor.rowcount
    else:
        print(f"[SKIP] 未找到匹配: {old_url[:50]}")

# 禁用无RSS的订阅源
DISABLE_SOURCES = [
    "https://www.deeplearning.ai/the-batch/rss/",
    "https://www.minimaxi.com/news/rss",
    "https://www.minimax.io/news",
]

print("\n禁用无RSS的订阅源...")
for url in DISABLE_SOURCES:
    cursor.execute("""
        UPDATE feed_sources
        SET enabled = 0, priority = 0
        WHERE url = ?
    """, (url,))
    if cursor.rowcount > 0:
        print(f"[OK] 已禁用: {url[:50]}")

conn.commit()

# 显示当前状态
print("\n" + "=" * 60)
print("当前订阅源状态")
print("=" * 60)

cursor.execute("""
    SELECT name, enabled, priority, url
    FROM feed_sources
    ORDER BY priority DESC, name
""")

print("\n[启用的订阅源]")
for row in cursor.fetchall():
    name, enabled, priority, url = row
    if enabled:
        print(f"  [{priority}] {name}")

print("\n[已禁用的订阅源]")
cursor.execute("SELECT name, url FROM feed_sources WHERE enabled = 0")
for row in cursor.fetchall():
    name, url = row
    print(f"  [0] {name}")

print(f"\n总计更新: {updated_count} 个订阅源")
conn.close()
