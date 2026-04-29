"""重新翻译缺失的标题"""
import sys
import os
import asyncio
import io

sys.path.insert(0, r'D:\Vibe coding\AI情报站\backend')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from database import Article, SessionLocal
from scraper.translator import translate_title

async def fix_missing_titles():
    db = SessionLocal()

    try:
        # 找出 is_translated=True 但 title_zh 为空的文章
        articles = db.query(Article).filter(
            Article.is_translated == True,
            Article.title_zh == None,
            Article.summary_zh != None  # 有摘要翻译，说明已经处理过
        ).all()

        print(f"Found {len(articles)} articles with missing title_zh")

        if not articles:
            return

        success = 0
        failed = 0

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] Translating: {article.title[:40]}...")

            try:
                title_zh = await translate_title(article.title)
                if title_zh:
                    article.title_zh = title_zh
                    db.commit()
                    print(f"  [OK] {title_zh[:40]}...")
                    success += 1
                else:
                    print(f"  [--] No translation result")
                    failed += 1
            except Exception as e:
                print(f"  [ERROR] {e}")
                failed += 1

            # 避免请求过快
            await asyncio.sleep(0.5)

        print(f"\n{'='*50}")
        print(f"Done! Success: {success}, Failed: {failed}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(fix_missing_titles())
