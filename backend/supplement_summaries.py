"""
补充文章摘要脚本

对于摘要为空或过短的文章，自动抓取原文内容来补充摘要
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

import requests
import re
from bs4 import BeautifulSoup
from database import SessionLocal, Article

FETCH_TIMEOUT = 15


def extract_article_content(url: str) -> str:
    """
    从文章页面提取正文内容
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        return ""

    # 解析 HTML
    soup = BeautifulSoup(response.text, 'lxml')

    # 尝试移除脚本、导航、页脚等无关内容
    for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()

    # 尝试找正文容器
    content = ""

    # 常见正文章容器选择器
    content_selectors = [
        'article',
        '[role="main"]',
        '.post-content',
        '.article-content',
        '.entry-content',
        '.content-body',
        '#content',
        '.post-body',
        '.article-body',
        'main',
        '.main-content',
    ]

    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            content = element.get_text(separator=" ", strip=True)
            if len(content) > 200:
                break

    # 如果没找到，用 body
    if not content or len(content) < 200:
        body = soup.find('body')
        if body:
            content = body.get_text(separator=" ", strip=True)

    # 清理内容
    content = re.sub(r'\s+', ' ', content).strip()

    # 移除过短的内容
    if len(content) < 100:
        return ""

    return content[:3000]  # 限制长度


def supplement_summaries():
    """
    为摘要为空或过短的文章补充内容
    """
    db = SessionLocal()

    # 找出需要补充的文章（摘要为空或少于50字）
    # 使用 Python 过滤而不是 SQL 字符串函数（SQLite 兼容性）
    all_articles = db.query(Article).all()
    articles = [a for a in all_articles if not a.summary or len(a.summary) < 50]

    print(f"发现 {len(articles)} 篇文章需要补充摘要")

    updated = 0
    failed = 0

    for article in articles:
        print(f"\n处理: {article.title[:50]}...")
        print(f"  URL: {article.url[:80]}...")

        content = extract_article_content(article.url)

        if content:
            old_len = len(article.summary) if article.summary else 0
            article.summary = content[:2000]
            print(f"  摘要: {old_len} -> {len(article.summary)} 字")
            updated += 1
        else:
            print(f"  失败: 无法获取内容")
            failed += 1

        # 每10篇提交一次
        if (updated + failed) % 10 == 0:
            db.commit()
            print(f"\n已提交... (更新: {updated}, 失败: {failed})")

    db.commit()
    db.close()

    print(f"\n=== 完成 ===")
    print(f"成功更新: {updated} 篇")
    print(f"抓取失败: {failed} 篇")


if __name__ == "__main__":
    supplement_summaries()
