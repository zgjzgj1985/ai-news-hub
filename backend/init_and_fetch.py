"""
初始化 RSS 来源并重新抓取脚本

从 sources.py 读取所有 RSS 源配置，初始化到数据库，然后执行抓取
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, FeedSource
from scraper.sources import FEED_SOURCES, GITHUB_TRENDING_SOURCES, NEWSLETTER_SOURCES
from scraper.rss_parser import fetch_all_feeds


def get_all_sources():
    """获取所有订阅源配置的合并字典"""
    all_sources = {}

    # 添加 GitHub Trending 订阅源
    for key, config in GITHUB_TRENDING_SOURCES.items():
        all_sources[f"github_{key}"] = config

    # 添加 Newsletter 订阅源
    for key, config in NEWSLETTER_SOURCES.items():
        all_sources[f"newsletter_{key}"] = config

    # 添加原有订阅源
    all_sources.update(FEED_SOURCES)

    return all_sources


def init_sources():
    """初始化所有 RSS 来源到数据库"""
    db = SessionLocal()

    print("=== 初始化 RSS 来源 ===\n")

    # 获取所有订阅源
    all_sources = get_all_sources()

    added = 0
    updated = 0
    skipped = 0

    for key, config in all_sources.items():
        name = config["name"]
        url = config["url"]
        category = config.get("category", "general")
        priority = config.get("priority", 5)

        # 检查是否已存在
        existing = db.query(FeedSource).filter(FeedSource.url == url).first()

        if existing:
            # 更新优先级
            if existing.priority != priority:
                existing.priority = priority
                existing.enabled = True
                updated += 1
            else:
                skipped += 1
        else:
            # 新增来源
            source = FeedSource(
                name=name,
                url=url,
                category=category,
                priority=priority,
                enabled=True
            )
            db.add(source)
            added += 1

    db.commit()

    # 显示当前所有来源
    print(f"新增: {added} 个来源")
    print(f"更新: {updated} 个来源")
    print(f"跳过: {skipped} 个来源（已存在）")

    all_sources = db.query(FeedSource).filter(FeedSource.enabled == True).order_by(FeedSource.priority.desc()).all()
    print(f"\n当前启用的来源 ({len(all_sources)} 个):\n")

    for s in all_sources:
        print(f"  [{s.priority}] {s.name}")

    db.close()
    print("\n=== 来源初始化完成 ===\n")

    return added, updated

def run_fetch():
    """执行抓取"""
    print("\n=== 开始抓取数据 ===\n")
    result = fetch_all_feeds()

    print(f"\n抓取完成:")
    print(f"  新增文章: {result['total_added']} 篇")
    print(f"  发现文章: {result['total_seen']} 篇")
    print(f"  来源数量: {result['sources_count']} 个")

    if result['errors']:
        print(f"\n抓取错误:")
        for err in result['errors']:
            print(f"  - {err}")

    return result

if __name__ == "__main__":
    # 先初始化来源
    init_sources()

    # 再执行抓取
    run_fetch()
