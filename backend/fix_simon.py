# -*- coding: utf-8 -*-
"""修复Simon Willison订阅源URL"""
import sqlite3
import os
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 查找Simon Willison
cursor.execute("SELECT id, name, url FROM feed_sources WHERE name LIKE '%Simon%'")
rows = cursor.fetchall()
print(f"Found {len(rows)} Simon Willison records:")

# 更新URL
new_url = "https://simonwillison.net/atom/everything/"
for row in rows:
    cursor.execute("UPDATE feed_sources SET url = ? WHERE id = ?", (new_url, row[0]))
    print(f"Updated ID {row[0]}")

conn.commit()
conn.close()
print("Done!")
