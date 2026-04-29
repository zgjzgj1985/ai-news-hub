"""数据库迁移脚本 - 添加深度评审相关字段"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine


def migrate_add_deep_review_fields():
    """添加深度评审相关字段到 articles 表"""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(articles)"))
        columns = [row[1] for row in result]

        migrations = []

        if "deep_review_done" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN deep_review_done INTEGER DEFAULT 0"
            ))
            migrations.append("添加 deep_review_done 字段")
            conn.execute(text(
                "UPDATE articles SET deep_review_done = 1 WHERE review_grade IS NOT NULL"
            ))
            migrations.append("将已有评级的文章标记为已完成深度评审")

        if "deep_review_body" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN deep_review_body TEXT"
            ))
            migrations.append("添加 deep_review_body 字段")

        if "translated_at" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN translated_at TIMESTAMP"
            ))
            migrations.append("添加 translated_at 字段")

        conn.commit()

        # 创建索引
        index_migrations = []
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_articles_deep_review_done ON articles(deep_review_done)"
            ))
            index_migrations.append("创建 deep_review_done 索引")
        except Exception:
            pass

        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_articles_translated ON articles(is_translated)"
            ))
            index_migrations.append("创建 is_translated 索引")
        except Exception:
            pass

        conn.commit()

        if migrations or index_migrations:
            print("迁移完成:")
            for m in migrations:
                print(f"  - {m}")
            for m in index_migrations:
                print(f"  - {m}")
        else:
            print("无需迁移，所有字段已存在")


if __name__ == "__main__":
    migrate_add_deep_review_fields()
