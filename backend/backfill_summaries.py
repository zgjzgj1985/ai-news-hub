# -*- coding: utf-8 -*-
"""为没有摘要的旧文章补充抓取摘要"""

import sys
import time
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal, Article
from sqlalchemy import or_
from scraper.rss_parser import _fetch_page_summary, SOURCES_NEED_PAGE_FETCH

def backfill_summaries():
    """为没有摘要的文章补充摘要"""
    db = SessionLocal()

    try:
        # 找出没有摘要的文章
        articles = db.query(Article).filter(
            or_(Article.summary == None, Article.summary == '')
        ).all()

        total = len(articles)
        print(f"需要处理 {total} 篇没有摘要的文章")
        print("=" * 60)

        if total == 0:
            print("没有需要处理的文章")
            return

        success_count = 0
        fail_count = 0
        skipped_count = 0

        for i, article in enumerate(articles):
            # 进度显示
            progress = f"[{i+1}/{total}]"
            print(f"\n{progress} 处理: {article.title[:50]}...")
            print(f"      来源: {article.source_name}")

            # 检查来源是否需要从页面抓取
            if article.source_name not in SOURCES_NEED_PAGE_FETCH:
                print(f"      跳过: 来源 {article.source_name} 不支持页面抓取")
                skipped_count += 1
                continue

            # 检查 URL 是否有效
            if not article.url or not article.url.startswith('http'):
                print(f"      跳过: 无效 URL")
                skipped_count += 1
                continue

            # 抓取摘要
            summary = _fetch_page_summary(article.url)

            if summary:
                article.summary = summary
                db.commit()
                success_count += 1
                print(f"      成功: 摘要长度 {len(summary)}")
            else:
                fail_count += 1
                print(f"      失败: 无法获取摘要")

            # 避免请求过快
            time.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"处理完成!")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        print(f"跳过: {skipped_count}")

    finally:
        db.close()

if __name__ == "__main__":
    backfill_summaries()
