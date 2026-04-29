# -*- coding: utf-8 -*-
"""数据库状态检查脚本"""
import sys
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

print("=" * 60)
print("AI情报站 - 数据库状态检查")
print("=" * 60)

if not os.path.exists(db_path):
    print(f"[ERROR] 数据库文件不存在: {db_path}")
    sys.exit(1)

print(f"\n数据库路径: {db_path}")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 文章总数
cursor.execute("SELECT COUNT(*) FROM articles")
total_articles = cursor.fetchone()[0]
print(f"\n[1] 文章总数: {total_articles}")

# 2. 各来源分布
print("\n[2] 各来源文章分布:")
cursor.execute("""
    SELECT source_name, COUNT(*) as cnt, MAX(fetched_at) as last_fetch
    FROM articles
    GROUP BY source_name
    ORDER BY cnt DESC
""")
source_stats = cursor.fetchall()
for row in source_stats:
    print(f"  - {row['source_name']}: {row['cnt']} 篇 (最后抓取: {row['last_fetch'][:10] if row['last_fetch'] else 'N/A'})")

# 3. 评审等级分布
print("\n[3] 评审等级分布:")
cursor.execute("""
    SELECT review_grade, COUNT(*) as cnt
    FROM articles
    GROUP BY review_grade
    ORDER BY review_grade
""")
grade_stats = cursor.fetchall()
for row in grade_stats:
    grade = row['review_grade'] or '未评审'
    print(f"  - {grade}: {row['cnt']} 篇")

# 4. 翻译状态
print("\n[4] 翻译状态:")
cursor.execute("SELECT is_translated, COUNT(*) as cnt FROM articles GROUP BY is_translated")
trans_stats = cursor.fetchall()
for row in trans_stats:
    status = "已翻译" if row['is_translated'] else "未翻译"
    print(f"  - {status}: {row['cnt']} 篇")

# 5. 缺失摘要的文章
print("\n[5] 数据质量问题:")
cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NULL OR summary = ''")
no_summary = cursor.fetchone()[0]
print(f"  - 缺失摘要: {no_summary} 篇 ({no_summary/total_articles*100:.1f}%)" if total_articles else "")

# 6. 近期抓取统计
print("\n[6] 近期抓取统计:")
cursor.execute("SELECT COUNT(*) FROM articles WHERE fetched_at > ?", (datetime.now() - timedelta(days=7),))
last_7d = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM articles WHERE fetched_at > ?", (datetime.now() - timedelta(days=1),))
last_24h = cursor.fetchone()[0]
print(f"  - 最近7天: {last_7d} 篇")
print(f"  - 最近24小时: {last_24h} 篇")

# 7. 收藏统计
print("\n[7] 收藏统计:")
cursor.execute("SELECT COUNT(*) FROM bookmarks")
bookmarks = cursor.fetchone()[0]
print(f"  - 总收藏数: {bookmarks} 篇")

# 8. 订阅源统计
print("\n[8] 订阅源统计:")
cursor.execute("SELECT COUNT(*) FROM feed_sources")
total_sources = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM feed_sources WHERE enabled = 1")
enabled_sources = cursor.fetchone()[0]
print(f"  - 总订阅源: {total_sources} 个")
print(f"  - 已启用: {enabled_sources} 个")
print(f"  - 已禁用: {total_sources - enabled_sources} 个")

# 9. 重复URL检测
print("\n[9] 数据质量 - 重复检测:")
cursor.execute("SELECT url, COUNT(*) as cnt FROM articles GROUP BY url HAVING cnt > 1")
duplicates = cursor.fetchall()
print(f"  - 重复URL数量: {len(duplicates)}")

# 10. 标签分布
print("\n[10] 标签分布 (Top 10):")
cursor.execute("""
    SELECT value as tag, COUNT(*) as cnt
    FROM articles, json_each(articles.tags)
    GROUP BY tag
    ORDER BY cnt DESC
    LIMIT 10
""")
tag_stats = cursor.fetchall()
for row in tag_stats:
    print(f"  - {row['tag']}: {row['cnt']}")

print("\n" + "=" * 60)
conn.close()
