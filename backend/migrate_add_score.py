"""
数据库迁移脚本 - 添加 score 字段

使用方法：
    python migrate_add_score.py
"""
import sqlite3
import sys
from pathlib import Path

def migrate():
    db_path = Path(__file__).resolve().parent.parent / "data" / "articles.db"

    if not db_path.exists():
        print(f"数据库不存在: {db_path}")
        print("请先运行后端以创建数据库")
        return False

    print(f"连接数据库: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 检查 score 字段是否已存在
    cursor.execute("PRAGMA table_info(articles)")
    columns = [row[1] for row in cursor.fetchall()]

    print(f"当前字段: {columns}")

    if "score" in columns:
        print("score 字段已存在，无需迁移")
        conn.close()
        return True

    # 添加 score 字段
    print("添加 score 字段...")
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN score INTEGER")
        conn.commit()
        print("score 字段添加成功")

        # 验证
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"更新后字段: {columns}")

        # 为现有文章设置默认分数为 NULL（这些是没有热度分数的旧数据）
        cursor.execute("UPDATE articles SET score = NULL WHERE score IS NULL")
        conn.commit()

        article_count = cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"当前文章数: {article_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
