# -*- coding: utf-8 -*-
"""
订阅源质量审核脚本

测试所有 RSS 订阅源的有效性和内容质量
"""

import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import requests
import feedparser
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

from scraper.sources import (
    FEED_SOURCES,
    GITHUB_TRENDING_SOURCES,
    NEWSLETTER_SOURCES,
    VIBE_CODING_SOURCES,
    GAME_DEV_SOURCES,
    AI_TOOLS_SOURCES,
)


@dataclass
class SourceAuditResult:
    """订阅源审核结果"""
    name: str
    url: str
    category: str
    priority: int
    status: str  # ok, error, slow, empty
    response_time: float
    article_count: int
    first_article_title: Optional[str]
    quality_notes: list
    recommendation: str  # keep, disable, review


def test_single_source(name: str, url: str, category: str, priority: int) -> SourceAuditResult:
    """测试单个订阅源"""
    import time

    quality_notes = []
    start_time = time.time()

    try:
        # 测试连接
        response = requests.get(url, timeout=15, allow_redirects=True)
        response_time = time.time() - start_time

        if response.status_code != 200:
            return SourceAuditResult(
                name=name, url=url, category=category, priority=priority,
                status="error", response_time=response_time,
                article_count=0, first_article_title=None,
                quality_notes=[f"HTTP {response.status_code}"],
                recommendation="disable"
            )

        # 解析 RSS
        feed = feedparser.parse(response.content)

        if not feed.entries:
            return SourceAuditResult(
                name=name, url=url, category=category, priority=priority,
                status="empty", response_time=response_time,
                article_count=0, first_article_title=None,
                quality_notes=["无文章条目"],
                recommendation="disable"
            )

        article_count = len(feed.entries)
        first_title = feed.entries[0].get("title", "无标题")[:60] if feed.entries else None

        # 检查内容质量
        if response_time > 10:
            quality_notes.append(f"响应慢: {response_time:.1f}s")
            recommendation = "review"
        elif article_count == 0:
            recommendation = "disable"
        elif "cs.a" in url.lower() or "arxiv" in url.lower():
            quality_notes.append("学术论文源（噪音较多）")
            recommendation = "review"
        elif "producthunt" in url.lower():
            quality_notes.append("产品发布平台（非教程/技巧类）")
            recommendation = "review"
        elif "hacker" in url.lower():
            quality_notes.append("Hacker News（需严格过滤）")
            recommendation = "keep"  # 但需要 strict_mode
        else:
            recommendation = "keep"

        return SourceAuditResult(
            name=name, url=url, category=category, priority=priority,
            status="ok", response_time=response_time,
            article_count=article_count, first_article_title=first_title,
            quality_notes=quality_notes,
            recommendation=recommendation
        )

    except requests.Timeout:
        return SourceAuditResult(
            name=name, url=url, category=category, priority=priority,
            status="error", response_time=15.0,
            article_count=0, first_article_title=None,
            quality_notes=["请求超时"],
            recommendation="disable"
        )
    except Exception as e:
        return SourceAuditResult(
            name=name, url=url, category=category, priority=priority,
            status="error", response_time=time.time() - start_time,
            article_count=0, first_article_title=None,
            quality_notes=[f"错误: {str(e)[:50]}"],
            recommendation="disable"
        )


def merge_all_sources() -> list:
    """合并所有订阅源"""
    sources = []

    for config in GITHUB_TRENDING_SOURCES.values():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    for config in NEWSLETTER_SOURCES.values():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    for config in VIBE_CODING_SOURCES.values():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    for config in GAME_DEV_SOURCES.values():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    for config in AI_TOOLS_SOURCES.values():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    for key, config in FEED_SOURCES.items():
        sources.append((config["name"], config["url"], config.get("category", "general"), config.get("priority", 5)))

    return sources


def run_audit():
    """运行订阅源审核"""
    all_sources = merge_all_sources()
    print("=" * 80)
    print(f"订阅源质量审核")
    print("=" * 80)
    print(f"\n总计测试 {len(all_sources)} 个订阅源...\n")

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_single_source, name, url, cat, priority): (name, url)
                   for name, url, cat, priority in all_sources}

        for i, future in enumerate(as_completed(futures), 1):
            name, url = futures[future]
            try:
                result = future.result()
                results.append(result)

                status_icon = {
                    "ok": "[OK]",
                    "error": "[ERR]",
                    "empty": "[空]",
                    "slow": "[慢]"
                }.get(result.status, "[?]")

                print(f"{status_icon} {result.name[:35]:<35} | {result.article_count:3d} 篇 | {result.response_time:5.2f}s")

            except Exception as e:
                print(f"[ERR] {name}: {e}")

    # 分类显示结果
    print("\n" + "=" * 80)
    print("审核结果汇总")
    print("=" * 80)

    keep_sources = [r for r in results if r.recommendation == "keep"]
    review_sources = [r for r in results if r.recommendation == "review"]
    disable_sources = [r for r in results if r.recommendation == "disable"]

    print(f"\n[推荐保留] {len(keep_sources)} 个")
    print("-" * 80)
    for r in sorted(keep_sources, key=lambda x: -x.priority):
        print(f"  [{r.priority}] {r.name}")

    print(f"\n[建议审核] {len(review_sources)} 个")
    print("-" * 80)
    for r in sorted(review_sources, key=lambda x: -x.priority):
        notes = ", ".join(r.quality_notes) if r.quality_notes else ""
        print(f"  [{r.priority}] {r.name}")
        if notes:
            print(f"           备注: {notes}")

    print(f"\n[建议禁用] {len(disable_sources)} 个")
    print("-" * 80)
    for r in sorted(disable_sources, key=lambda x: -x.priority):
        notes = ", ".join(r.quality_notes) if r.quality_notes else "无内容"
        print(f"  [{r.priority}] {r.name}: {notes}")

    # 生成禁用 SQL
    print("\n" + "=" * 80)
    print("禁用低质量订阅源的 SQL 语句")
    print("=" * 80)

    for r in disable_sources:
        print(f"UPDATE feed_sources SET enabled = 0, priority = 0 WHERE url = '{r.url}';")

    return results


if __name__ == "__main__":
    run_audit()
