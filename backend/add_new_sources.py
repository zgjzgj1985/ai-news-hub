# -*- coding: utf-8 -*-
"""
添加高质量订阅源脚本

添加 GitHub Trending、Newsletter 等新订阅源，并修复失效的订阅源 URL
"""

import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

print("=" * 60)
print("添加高质量订阅源 - 扩展 Vibe Coding 内容覆盖")
print("=" * 60)

# 新增订阅源
NEW_SOURCES = [
    # GitHub Trending 订阅源
    ("github_trending_python",
     "GitHub Trending Python",
     "https://raw.githubusercontent.com/isboyjc/github-trending-api/main/data/daily/Python.xml",
     "vibe_coding", 8,
     "GitHub 每日热门 Python 项目"),

    ("github_trending_jupyter",
     "GitHub Trending Jupyter",
     "https://raw.githubusercontent.com/isboyjc/github-trending-api/main/data/daily/Jupyter.xml",
     "vibe_coding", 8,
     "GitHub 每日热门 Jupyter/Notebook 项目"),

    ("github_trending_all",
     "GitHub Trending All",
     "https://raw.githubusercontent.com/isboyjc/github-trending-api/main/data/daily/all.xml",
     "vibe_coding", 7,
     "GitHub 每日热门全部分类"),

    # Newsletter 订阅源
    ("latent_space",
     "Latent Space",
     "https://latent.space/feed",
     "newsletter", 8,
     "AI 技术深度 Newsletter"),

    ("the_gradient",
     "The Gradient",
     "https://thegradient.pub/rss/",
     "newsletter", 7,
     "AI 学术与产业分析"),
]

# 需要修复 URL 的订阅源
FIXED_SOURCES = [
    # (原 URL 或名称, 新 URL, 新名称, 新优先级)
    ("simonwillison.net/atom/everything",
     "https://feeds.simonwillison.net/",
     "Simon Willison", 8,
     "AI Coding 专家博客 - 已修复 RSS 地址"),
]

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 添加新订阅源
print("\n[1] 添加新订阅源...")
added_count = 0
for key, name, url, category, priority, note in NEW_SOURCES:
    # 检查是否已存在
    cursor.execute("SELECT id FROM feed_sources WHERE url = ?", (url,))
    if cursor.fetchone():
        print(f"  [SKIP] {name} (已存在)")
        continue

    cursor.execute("""
        INSERT INTO feed_sources (name, url, category, priority, enabled)
        VALUES (?, ?, ?, ?, 1)
    """, (name, url, category, priority))
    print(f"  [ADD] {name}")
    print(f"        类别: {category}, 优先级: {priority}")
    print(f"        说明: {note}")
    added_count += 1

print(f"\n  总计新增: {added_count} 个订阅源")

# 修复失效订阅源 URL
print("\n[2] 修复失效订阅源 URL...")
fixed_count = 0
for old_pattern, new_url, new_name, new_priority, note in FIXED_SOURCES:
    # 尝试通过 URL 或名称匹配
    cursor.execute("""
        SELECT id, name, url FROM feed_sources
        WHERE url LIKE ? OR name = ?
    """, (f"%{old_pattern}%", new_name))

    row = cursor.fetchone()
    if row:
        source_id, old_name, old_url = row
        cursor.execute("""
            UPDATE feed_sources
            SET url = ?, name = ?, priority = ?, enabled = 1
            WHERE id = ?
        """, (new_url, new_name, new_priority, source_id))
        print(f"  [FIX] {old_name}")
        print(f"        原URL: {old_url[:60]}...")
        print(f"        新URL: {new_url}")
        print(f"        说明: {note}")
        fixed_count += 1
    else:
        print(f"  [SKIP] 未找到匹配: {old_pattern}")

print(f"\n  总计修复: {fixed_count} 个订阅源")

conn.commit()

# 显示当前所有订阅源
print("\n" + "=" * 60)
print("当前订阅源状态")
print("=" * 60)

cursor.execute("""
    SELECT name, enabled, priority, category, url
    FROM feed_sources
    ORDER BY priority DESC, name
""")

print("\n[启用的订阅源 - 按优先级排序]")
enabled_count = 0
for row in cursor.fetchall():
    name, enabled, priority, category, url = row
    if enabled:
        enabled_count += 1
        print(f"  [{priority:2d}] [{category:12s}] {name}")

print(f"\n  总计启用: {enabled_count} 个订阅源")

# 按类别统计
print("\n[按类别统计]")
cursor.execute("""
    SELECT category, COUNT(*) as cnt
    FROM feed_sources
    WHERE enabled = 1
    GROUP BY category
    ORDER BY cnt DESC
""")
for row in cursor.fetchall():
    cat, cnt = row
    print(f"  {cat}: {cnt} 个")

print("\n" + "=" * 60)
print("完成!")
print("=" * 60)

conn.close()
