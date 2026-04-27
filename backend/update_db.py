"""
数据库迁移脚本 - 添加翻译相关字段

运行方式: python update_db.py
"""

import sqlite3
import os
from pathlib import Path

# 获取数据库路径
BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

print(f"Database path: {db_path}")


def upgrade():
    """Add translation-related columns to articles table"""
    if not os.path.exists(db_path):
        print("Database file does not exist. Please initialize it first.")
        return

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        # Check if articles table exists
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='articles'"
        )
        row = cursor.fetchone()
        if not row:
            print("articles table does not exist. Please initialize database first.")
            return

        table_sql = row[0]

        # Add title_zh column
        if 'title_zh' not in table_sql:
            cursor.execute("ALTER TABLE articles ADD COLUMN title_zh TEXT")
            print("[OK] Added title_zh column")
        else:
            print("[--] title_zh column already exists")

        # Add is_translated column
        if 'is_translated' not in table_sql:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_translated INTEGER DEFAULT 0")
            print("[OK] Added is_translated column")
        else:
            print("[--] is_translated column already exists")

        # Add translated_at column
        if 'translated_at' not in table_sql:
            cursor.execute("ALTER TABLE articles ADD COLUMN translated_at TIMESTAMP")
            print("[OK] Added translated_at column")
        else:
            print("[--] translated_at column already exists")

        conn.commit()

    # Verify columns
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\nCurrent articles table columns: {columns}")

        # Statistics
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_translated = 1")
        translated = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE summary_zh IS NOT NULL AND summary_zh != ''")
        has_zh = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE title_zh IS NOT NULL AND title_zh != ''")
        has_title_zh = cursor.fetchone()[0]

        print(f"\nTranslation statistics:")
        print(f"  - Total articles: {total}")
        print(f"  - Translated (is_translated=True): {translated}")
        print(f"  - Has Chinese summary: {has_zh}")
        print(f"  - Has Chinese title: {has_title_zh}")


if __name__ == "__main__":
    print("Starting database migration...")
    upgrade()
    print("\nMigration complete!")
