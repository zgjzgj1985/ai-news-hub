# -*- coding: utf-8 -*-
import json
from database import SessionLocal, Article

db = SessionLocal()

# 获取最新翻译的文章
articles = db.query(Article).filter(
    Article.title_zh != None,
    Article.title_zh != ''
).order_by(Article.translated_at.desc()).limit(10).all()

results = []
for a in articles:
    results.append({
        'id': a.id,
        'original_title': a.title,
        'chinese_title': a.title_zh,
        'source': a.source_name,
        'translated_at': str(a.translated_at) if a.translated_at else None
    })

db.close()

# 保存到文件
output_path = 'translation_results.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Results saved to {output_path}")
print(f"Found {len(results)} articles with translated titles")
