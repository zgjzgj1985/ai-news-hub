"""数据库迁移脚本 - 添加评审委员会相关字段"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine, SessionLocal


def migrate_add_review_fields():
    """添加评审委员会相关字段到 articles 表"""
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(articles)"))
        columns = [row[1] for row in result]

        migrations = []

        # 添加 review_grade 字段
        if "review_grade" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN review_grade VARCHAR(1)"
            ))
            migrations.append("添加 review_grade 字段")

        # 添加 review_score 字段
        if "review_score" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN review_score INTEGER"
            ))
            migrations.append("添加 review_score 字段")

        # 添加 review_result 字段
        if "review_result" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN review_result TEXT"
            ))
            migrations.append("添加 review_result 字段")

        # 添加 review_verdict 字段
        if "review_verdict" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN review_verdict TEXT"
            ))
            migrations.append("添加 review_verdict 字段")

        # 添加 reviewed_at 字段
        if "reviewed_at" not in columns:
            conn.execute(text(
                "ALTER TABLE articles ADD COLUMN reviewed_at TIMESTAMP"
            ))
            migrations.append("添加 reviewed_at 字段")

        # 添加索引
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_articles_review_grade ON articles(review_grade)"
            ))
            migrations.append("创建 review_grade 索引")
        except Exception:
            pass

        conn.commit()

        if migrations:
            print("迁移完成:")
            for m in migrations:
                print(f"  - {m}")
        else:
            print("无需迁移，所有字段已存在")


if __name__ == "__main__":
    migrate_add_review_fields()
