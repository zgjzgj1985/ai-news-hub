# -*- coding: utf-8 -*-
"""清空文章表脚本"""

import sqlite3
import os
from pathlib import Path

# 获取数据库路径
BASE_DIR = Path(__file__).resolve().parent.parent
db_path = os.path.join(BASE_DIR, 'data', 'articles.db')
db_path = os.path.normpath(db_path)

print(f"Database path: {db_path}")

if not os.path.exists(db_path):
    print("Database file does not exist!")
else:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 获取当前统计
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        print(f"Current articles count: {count}")

        # 删除所有文章
        cursor.execute("DELETE FROM articles")
        print(f"Deleted {cursor.rowcount} articles from articles table")

        # 删除所有书签（级联删除应该已经处理，但确保数据干净）
        cursor.execute("DELETE FROM bookmarks")
        print(f"Deleted bookmarks")

        conn.commit()

        # 验证
        cursor.execute("SELECT COUNT(*) FROM articles")
        remaining = cursor.fetchone()[0]
        print(f"\nVerification - Remaining articles: {remaining}")

    print("\nDatabase cleaned successfully!")
