"""
Awesome 列表抓取模块

抓取 GitHub 上流行的 awesome 列表（如 awesome-vibe-coding），提取其中与 AI 相关的项目。
"""

import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import hashlib
import logging
import re
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from database import Article, SessionLocal

logger = logging.getLogger(__name__)

# Awesome 列表配置
AWESOME_LISTS = [
    {
        "name": "awesome-vibe-coding",
        "repo": "0xWelt/Awesome-Vibe-Coding",
        "url_master": "https://raw.githubusercontent.com/0xWelt/Awesome-Vibe-Coding/master/README.md",
        "url_main": "https://raw.githubusercontent.com/0xWelt/Awesome-Vibe-Coding/main/README.md",
        "category": "vibe_coding",
        "keywords": ["cursor", "windsurf", "bolt", "lovable", "v0", "claude", "agent", "coding", "vibe", "github", "copilot", "zed", "replit"],
    },
    {
        "name": "awesome-ai-agents",
        "repo": "caramaschiHG/awesome-ai-agents-2026",
        "url_master": "https://raw.githubusercontent.com/caramaschiHG/awesome-ai-agents-2026/master/README.md",
        "url_main": "https://raw.githubusercontent.com/caramaschiHG/awesome-ai-agents-2026/main/README.md",
        "category": "vibe_coding",
        "keywords": ["agent", "llm", "gpt", "claude", "coding", "tool", "assistant", "cursor", "windsurf"],
    },
    {
        "name": "awesome-ai-tools",
        "repo": "eudk/awesome-ai-tools",
        "url_master": "https://raw.githubusercontent.com/eudk/awesome-ai-tools/master/README.md",
        "url_main": "https://raw.githubusercontent.com/eudk/awesome-ai-tools/main/README.md",
        "category": "tools",
        "keywords": ["ai", "llm", "gpt", "claude", "openai", "tool", "assistant", "copilot", "cursor", "agent"],
    },
]

# GitHub Raw URL 前缀
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/{}/master/README.md"
GITHUB_RAW_BASE_V2 = "https://raw.githubusercontent.com/{}/main/README.md"


def fetch_raw_readme(config: dict, timeout: int = 30) -> Optional[str]:
    """获取 GitHub README 原始内容，尝试多个可能的 URL"""
    urls_to_try = [
        config.get("url_main"),
        config.get("url_master"),
    ]

    for url in urls_to_try:
        if not url:
            continue
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            logger.info(f"  成功获取: {config['name']} from {url.split('/')[-3:]}")
            return response.text
        except requests.RequestException as e:
            logger.debug(f"  尝试 URL 失败 {url}: {e}")
            continue

    logger.error(f"获取 README 失败 {config['name']}: 所有 URL 都失败")
    return None


def parse_awesome_links(content: str, keywords: list[str]) -> list[dict]:
    """解析 awesome 列表，提取链接和描述

    Args:
        content: README 原始内容
        keywords: 关键词列表，用于过滤相关内容

    Returns:
        项目列表，每项包含 title, url, description
    """
    projects = []
    lines = content.split("\n")

    current_category = ""
    current_description = ""

    for line in lines:
        line = line.strip()

        # 检测分类标题（## 开头的行）
        if line.startswith("##") and not line.startswith("###"):
            current_category = line.replace("##", "").strip()
            continue

        # 检测项目链接 [title](url)
        link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", line)
        if link_match:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()

            # 过滤非 GitHub 链接
            if not url.startswith("http"):
                continue

            # 检查关键词匹配
            title_lower = title.lower()
            desc_lower = current_description.lower()
            combined = f"{title_lower} {desc_lower}"

            matched_keyword = None
            for keyword in keywords:
                if keyword.lower() in combined:
                    matched_keyword = keyword
                    break

            # 如果没有匹配关键词，跳过
            if not matched_keyword:
                continue

            # 过滤常见的无关内容
            skip_patterns = [
                "awesome", "curated", "list", "resources",
                "contributing", "license", " Stars",
            ]
            if any(p.lower() in title_lower for p in skip_patterns):
                if "github.com" not in url:  # 但保留 GitHub 链接
                    continue

            # 去重（相同 URL）
            if any(p["url"] == url for p in projects):
                continue

            projects.append({
                "title": title,
                "url": url,
                "description": current_description.strip(),
                "category": current_category,
                "matched_keyword": matched_keyword,
            })

        # 更新当前描述（收集链接前的文字）
        elif line and not line.startswith("#") and not line.startswith("-"):
            if current_description:
                current_description += " " + line
            else:
                current_description = line

    return projects


def generate_summary_from_project(project: dict) -> str:
    """从项目信息生成摘要"""
    title = project.get("title", "")
    desc = project.get("description", "")
    category = project.get("category", "")
    matched = project.get("matched_keyword", "")

    summary = f"[Awesome List] {title}"

    if category:
        summary += f"\n\n分类: {category}"

    if desc:
        summary += f"\n\n{desc[:200]}"
        if len(desc) > 200:
            summary += "..."

    summary += f"\n\n关键词匹配: {matched}"
    summary += "\n\n来源: Awesome List 精选项目"

    return summary


def scrape_awesome_lists() -> dict:
    """抓取所有 awesome 列表

    Returns:
        包含抓取结果的字典
    """
    db = SessionLocal()
    total_added = 0
    total_seen = 0
    errors = []

    for list_config in AWESOME_LISTS:
        list_name = list_config["name"]
        logger.info(f"抓取 awesome 列表: {list_name}")

        try:
            # 获取 README
            content = fetch_raw_readme(list_config)
            if not content:
                errors.append(f"{list_name}: 获取内容失败")
                continue

            # 解析链接
            projects = parse_awesome_links(content, list_config["keywords"])
            logger.info(f"  解析到 {len(projects)} 个匹配项目")

            # 添加到数据库
            for project in projects:
                total_seen += 1

                # 检查是否已存在
                existing = db.query(Article).filter(Article.url == project["url"]).first()
                if existing:
                    continue

                # 生成摘要
                summary = generate_summary_from_project(project)

                # 创建文章记录
                article = Article(
                    title=project["title"],
                    title_zh=None,  # 可选：自动翻译
                    url=project["url"],
                    summary=summary,
                    summary_zh=None,
                    source_name=f"Awesome - {list_name}",
                    source_url=f"https://github.com/{list_config['repo']}",
                    author=None,
                    published_at=datetime.utcnow(),
                    tags=[list_config["category"], "awesome-list", project.get("matched_keyword", "")],
                    content_hash=hashlib.md5(project["url"].encode()).hexdigest(),
                    read_time_minutes=2,  # Awesome 列表项目通常是短描述
                )

                db.add(article)
                total_added += 1

            db.commit()
            logger.info(f"  新增 {total_added} 个项目")

        except Exception as e:
            logger.error(f"抓取 {list_name} 失败: {e}")
            errors.append(f"{list_name}: {str(e)}")

    db.close()

    return {
        "total_added": total_added,
        "total_seen": total_seen,
        "errors": errors,
        "sources_count": len(AWESOME_LISTS),
    }


def add_awesome_sources_to_db():
    """将 awesome 列表作为订阅源添加到数据库（可选）"""
    from database import FeedSource

    db = SessionLocal()
    added = 0

    for list_config in AWESOME_LISTS:
        # 检查是否已存在
        existing = db.query(FeedSource).filter(
            FeedSource.name == f"Awesome - {list_config['name']}"
        ).first()

        if not existing:
            source = FeedSource(
                name=f"Awesome - {list_config['name']}",
                url=list_config["url"],
                category=list_config["category"],
                priority=7,
                enabled=True,
            )
            db.add(source)
            added += 1
            logger.info(f"添加订阅源: {source.name}")

    db.commit()
    db.close()

    return added


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")  # 添加当前目录到路径

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("Awesome 列表抓取工具")
    print("=" * 60)

    # 添加订阅源
    print("\n[1] 添加 Awesome 列表订阅源到数据库...")
    added = add_awesome_sources_to_db()
    print(f"    新增 {added} 个订阅源")

    # 抓取内容
    print("\n[2] 抓取 Awesome 列表内容...")
    result = scrape_awesome_lists()

    print(f"\n抓取完成:")
    print(f"  新增文章: {result['total_added']} 篇")
    print(f"  发现项目: {result['total_seen']} 个")

    if result["errors"]:
        print(f"\n错误:")
        for err in result["errors"]:
            print(f"  - {err}")
