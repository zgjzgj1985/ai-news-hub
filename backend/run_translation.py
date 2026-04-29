"""
手动翻译脚本 - 立即翻译未翻译的文章（标题 + 摘要）

运行方式: python run_translation.py [数量]
示例: python run_translation.py 50
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows 控制台 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from database import Article, SessionLocal
from scraper.translator import (
    CHINESE_SOURCES,
    detect_language,
    translate_text,
    translate_title,
    save_translation,
    is_chinese_source
)
from llm_client import get_llm_client


async def translate_articles(limit: int = 30):
    """翻译指定数量的未翻译文章（标题 + 摘要）"""
    db = SessionLocal()

    try:
        # 检查 LLM 服务
        llm_client = get_llm_client()
        if not llm_client.is_available():
            print("[ERROR] LLM service is not available. Please start Ollama first.")
            print("Run: ollama serve")
            return

        print(f"[INFO] LLM service is available")

        # 获取未翻译的文章
        articles = (
            db.query(Article)
            .filter(
                Article.is_translated == False,
            )
            .filter(~Article.source_name.in_(CHINESE_SOURCES))
            .limit(limit)
            .all()
        )

        print(f"[INFO] Found {len(articles)} articles to translate")

        if not articles:
            print("[INFO] No articles to translate")
            return

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] Processing: {article.title[:50]}...")

            # 检测语言
            lang = detect_language(article.title)
            if lang == "zh":
                # 已经是中文，标记为已翻译
                article.is_translated = True
                article.translated_at = datetime.utcnow()
                db.commit()
                print(f"  [SKIP] Already Chinese content")
                skipped_count += 1
                continue

            translated_summary = None
            translated_title = None

            # 翻译标题
            try:
                translated_title = await translate_title(article.title)
                if translated_title:
                    print(f"  [OK] Title: {translated_title[:40]}...")
                else:
                    print(f"  [--] Title translation skipped")
            except Exception as e:
                print(f"  [ERROR] Title translation failed: {e}")

            # 翻译摘要
            if article.summary:
                try:
                    translated_summary = await translate_text(article.summary)
                    if translated_summary:
                        print(f"  [OK] Summary translated ({len(translated_summary)} chars)")
                    else:
                        print(f"  [--] Summary translation skipped")
                except Exception as e:
                    print(f"  [ERROR] Summary translation failed: {e}")

            # 保存翻译结果
            if translated_summary or translated_title:
                article.summary_zh = translated_summary
                article.title_zh = translated_title
                article.is_translated = True
                article.translated_at = datetime.utcnow()
                db.commit()
                print(f"  [SAVED] Translation complete")
                success_count += 1
            else:
                failed_count += 1
                print(f"  [FAIL] No translation results")

        print(f"\n{'='*50}")
        print(f"Translation complete!")
        print(f"  - Success: {success_count}")
        print(f"  - Failed: {failed_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"{'='*50}")

    finally:
        db.close()


if __name__ == "__main__":
    # 获取翻译数量参数
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30

    print(f"Starting translation for up to {limit} articles...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    asyncio.run(translate_articles(limit))
