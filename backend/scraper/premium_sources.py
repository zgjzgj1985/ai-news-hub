"""
优质内容订阅源适配器

支持:
1. B站 UP主视频 (直接爬取 B站 API)
2. X (Twitter) (使用 RSSHub 或直接爬取)
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from database import Article, FeedSource, SessionLocal
from scraper.classifier import classify
from review_committee import get_committee

logger = logging.getLogger(__name__)

# B站 UP主配置 (UID: 名称)
BILIBILI_UIDS = {
    # 理论派
    "78284557": "跟李沐学AI",
    "23155631": "Shuhuai008",
    # 实战派
    "365717884": "Jack-Cui",
    "1600567336": "秋葉aaaki",
    # 工具流
    "489346655": "老麦的工具库",
    "1595901912": "赛文乔伊",
    # 资讯派
    "50764938": "图灵的猫",
}

# X (Twitter) AI 大V账号
TWITTER_ACCOUNTS = [
    "karpathy",        # Andrej Karpathy
    "ylecun",          # Yann LeCun
    "swyx",            # swyx - Latent Space
    "rasbt",           # Sebastian Raschka
    "_akhaliq",        # AK - Papers/News
    "sama",            # Sam Altman
    "dair_ai",         # DAIR.AI
    "AndrewYNg",       # Andrew Ng
]

# RSSHub 实例列表
RSSHUB_INSTANCES = [
    "https://rsshub.app",
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _safe_log(level, msg, *args):
    """安全日志记录"""
    try:
        if args:
            msg = str(msg) % tuple(str(a) for a in args)
        msg_str = str(msg)
        safe_msg = msg_str.encode("ascii", errors="replace").decode("ascii")
        logger.log(level, safe_msg)
    except Exception:
        pass


def estimate_read_time(text: str) -> int:
    """估算阅读时间（分钟）"""
    if not text:
        return 1
    words = len(text.split())
    return max(1, round(words / 200))


def clean_html(raw_html: str) -> str:
    """清理 HTML 标签"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000]


def compute_hash(title: str, url: str) -> str:
    """计算内容哈希"""
    return hashlib.sha256(f"{title}|{url}".encode()).hexdigest()


def parse_bilibili_date(date_str: str) -> Optional[datetime]:
    """解析 B站日期格式"""
    try:
        # B站格式: 2024-01-01 12:00:00
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def fetch_bilibili_user(uid: str, name: str, max_articles: int = 10) -> list[dict]:
    """
    抓取 B站 UP主的最新视频

    Args:
        uid: UP主的 UID
        name: UP主显示名称
        max_articles: 最大文章数

    Returns:
        文章列表
    """
    articles = []

    # 方法1: 直接爬取 B站视频列表页
    video_url = f"https://space.bilibili.com/{uid}/video"

    try:
        _safe_log(logging.INFO, "Fetching Bilibili: %s (%s)", name, uid)
        response = requests.get(video_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            _safe_log(logging.WARNING, "Bilibili %s returned %d", name, response.status_code)
            return articles

        # 从页面提取 JSON 数据
        html = response.text

        # B站使用 JSON 注入数据到页面
        json_match = re.search(r'<script>window\.__INITIAL_STATE__=({.*?});</script>', html, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))

                # 提取视频列表
                uploader_data = data.get("user", {}).get("upData", {})
                videos = data.get("uDashPlayVideo", {}).get("video", [])

                for video in videos[:max_articles]:
                    title = video.get("title", "")
                    bvid = video.get("bvid", "")
                    description = video.get("description", "")
                    duration = video.get("duration", 0)

                    # 构建视频链接
                    link = f"https://www.bilibili.com/video/{bvid}"

                    # 解析时长
                    minutes = max(1, duration // 60)

                    article = {
                        "title": title,
                        "url": link,
                        "summary": description[:1000] if description else "",
                        "source_name": f"B站: {name}",
                        "source_url": video_url,
                        "author": name,
                        "published_at": None,
                        "tags": [],
                        "content_hash": compute_hash(title, link),
                        "read_time_minutes": minutes,
                        "score": None,
                    }
                    articles.append(article)
                    _safe_log(logging.INFO, "  -> %s", title[:50])

            except json.JSONDecodeError as e:
                _safe_log(logging.WARNING, "Failed to parse Bilibili JSON for %s: %s", name, str(e))

    except Exception as e:
        _safe_log(logging.WARNING, "Failed to fetch Bilibili %s: %s", name, str(e))

    # 方法2: 如果页面抓取失败，尝试 RSSHub
    if not articles:
        for rsshub in RSSHUB_INSTANCES:
            try:
                rss_url = f"{rsshub}/bilibili/user/video/{uid}"
                response = requests.get(rss_url, headers=HEADERS, timeout=15)

                if response.status_code == 200:
                    import feedparser
                    feed = feedparser.parse(response.text)

                    for entry in feed.entries[:max_articles]:
                        title = entry.get("title", "")
                        link = entry.get("link", "")

                        description = ""
                        if hasattr(entry, "summary"):
                            description = clean_html(entry.summary)

                        article = {
                            "title": title,
                            "url": link,
                            "summary": description[:1000],
                            "source_name": f"B站: {name}",
                            "source_url": rss_url,
                            "author": name,
                            "published_at": None,
                            "tags": [],
                            "content_hash": compute_hash(title, link),
                            "read_time_minutes": estimate_read_time(description),
                            "score": None,
                        }
                        articles.append(article)

                    if articles:
                        _safe_log(logging.INFO, "  Fetched %d videos via RSSHub", len(articles))
                        break

            except Exception as e:
                _safe_log(logging.WARNING, "RSSHub failed for %s: %s", name, str(e))

    return articles


def fetch_twitter_rss(username: str, max_articles: int = 10) -> list[dict]:
    """
    抓取 X (Twitter) 用户的推文

    Args:
        username: Twitter 用户名
        max_articles: 最大文章数

    Returns:
        文章列表
    """
    articles = []

    for rsshub in RSSHUB_INSTANCES:
        try:
            rss_url = f"{rsshub}/twitter/user/{username}"
            _safe_log(logging.INFO, "Fetching Twitter: @%s from %s", username, rsshub)

            response = requests.get(rss_url, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                _safe_log(logging.WARNING, "RSSHub %s returned %d for @%s", rsshub, response.status_code, username)
                continue

            import feedparser
            feed = feedparser.parse(response.text)

            for entry in feed.entries[:max_articles]:
                title = entry.get("title", "")
                # Twitter 标题格式: "用户 @username: 推文内容"
                if f"@{username}" in title:
                    parts = title.split(":", 1)
                    if len(parts) > 1:
                        title = parts[1].strip()

                link = entry.get("link", "")

                description = ""
                if hasattr(entry, "summary"):
                    description = clean_html(entry.summary)
                elif hasattr(entry, "description"):
                    description = clean_html(entry.description)

                # 提取发布时间
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])

                article = {
                    "title": title[:200],
                    "url": link,
                    "summary": description[:500],
                    "source_name": f"X: @{username}",
                    "source_url": f"https://x.com/{username}",
                    "author": f"@{username}",
                    "published_at": published,
                    "tags": [],
                    "content_hash": compute_hash(title, link),
                    "read_time_minutes": 1,
                    "score": None,
                }
                articles.append(article)

            if articles:
                _safe_log(logging.INFO, "  Fetched %d tweets from @%s", len(articles), username)
                break

        except Exception as e:
            _safe_log(logging.WARNING, "Failed to fetch Twitter @%s: %s", username, str(e))

    if not articles:
        _safe_log(logging.WARNING, "All RSSHub instances failed for @%s", username)

    return articles


def save_articles(articles: list[dict], db) -> int:
    """保存文章到数据库，返回实际保存的数量"""
    saved = 0

    for article_data in articles:
        # 检查是否已存在
        existing = db.query(Article).filter(
            Article.url == article_data["url"]
        ).first()

        if existing:
            continue

        # 创建文章
        article = Article(**article_data)
        db.add(article)
        saved += 1

    db.commit()
    return saved


def fetch_all_premium_sources(max_per_source: int = 10) -> dict:
    """
    抓取所有优质内容源

    Returns:
        {
            "total_added": int,
            "total_seen": int,
            "sources_count": int,
            "errors": list
        }
    """
    db = SessionLocal()
    all_articles = []
    errors = []
    sources_count = 0

    # ========== 1. 抓取 B站 UP主 ==========
    _safe_log(logging.INFO, "=" * 50)
    _safe_log(logging.INFO, "Fetching Bilibili UP主...")

    for uid, name in BILIBILI_UIDS.items():
        try:
            articles = fetch_bilibili_user(uid, name, max_per_source)
            all_articles.extend(articles)
            sources_count += 1
        except Exception as e:
            errors.append(f"B站 {name}: {str(e)}")
            _safe_log(logging.WARNING, "Error fetching Bilibili %s: %s", name, str(e))

    # ========== 2. 抓取 X (Twitter) ==========
    _safe_log(logging.INFO, "=" * 50)
    _safe_log(logging.INFO, "Fetching Twitter accounts...")

    for username in TWITTER_ACCOUNTS:
        try:
            articles = fetch_twitter_rss(username, max_per_source)
            all_articles.extend(articles)
            sources_count += 1
        except Exception as e:
            errors.append(f"X @{username}: {str(e)}")
            _safe_log(logging.WARNING, "Error fetching Twitter @%s: %s", username, str(e))

    # ========== 3. 保存文章 ==========
    _safe_log(logging.INFO, "=" * 50)
    _safe_log(logging.INFO, "Saving %d articles...", len(all_articles))

    total_added = save_articles(all_articles, db)

    db.close()

    return {
        "total_added": total_added,
        "total_seen": len(all_articles),
        "sources_count": sources_count,
        "errors": errors
    }


if __name__ == "__main__":
    # 测试抓取
    logging.basicConfig(level=logging.INFO)
    result = fetch_all_premium_sources(max_per_source=5)
    print(f"Result: {result}")
