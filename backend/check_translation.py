# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal, Article

db = SessionLocal()

print("=" * 70)
print("Translation Results - 翻译结果验证")
print("=" * 70)

articles = db.query(Article).filter(Article.is_translated == True).limit(10).all()

for i, a in enumerate(articles, 1):
    print(f"\n[{i}] Original Title: {a.title[:60]}")
    print(f"    Chinese Title: {a.title_zh[:60] if a.title_zh else '(none)'}")
    print(f"    Source: {a.source_name}")

print("\n" + "=" * 70)

# 统计
total = db.query(Article).count()
translated = db.query(Article).filter(Article.is_translated == True).count()
has_title_zh = db.query(Article).filter(Article.title_zh != None, Article.title_zh != '').count()
has_summary_zh = db.query(Article).filter(Article.summary_zh != None, Article.summary_zh != '').count()

print(f"Total articles: {total}")
print(f"Translated (is_translated=True): {translated}")
print(f"Has Chinese title (title_zh): {has_title_zh}")
print(f"Has Chinese summary (summary_zh): {has_summary_zh}")
print(f"Remaining: {total - translated}")

db.close()
