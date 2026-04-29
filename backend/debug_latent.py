"""
调试 Latent Space 抓取问题
"""
import sys
sys.path.insert(0, '.')

from scraper.rss_parser import _fetch_with_retry, _is_feed_url_valid, _fetch_feed_impl
import feedparser

class MockFeedSource:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.id = 0
        self.category = "newsletter"
        self.priority = 9
        self.enabled = True

print("=== 调试 Latent Space ===\n")

source = MockFeedSource("Latent Space", "https://www.latent.space/feed")

# 1. 检查 URL
print("[1] URL 验证")
valid, err = _is_feed_url_valid(source.url)
print(f"  有效: {valid}, 错误: {err}")

# 2. 抓取内容
print("\n[2] 抓取内容")
content = _fetch_with_retry(source)
if content:
    print(f"  成功: {len(content)} 字符")
else:
    print("  失败")
    sys.exit(1)

# 3. 解析 feed
print("\n[3] 解析 feed")
feed = feedparser.parse(content)
print(f"  条目数: {len(feed.entries)}")
print(f"  Bozo: {feed.bozo}")

# 4. 检查去重
print("\n[4] 检查去重情况")
from database import SessionLocal, Article
from datetime import timedelta

db = SessionLocal()
recent_date = __import__('datetime').datetime.utcnow() - timedelta(days=7)
existing_urls = set(
    row[0]
    for row in db.query(Article.url)
    .filter(Article.fetched_at >= recent_date)
    .all()
)
print(f"  数据库中已有 URL 数: {len(existing_urls)}")

# 检查 feed 中有多少 URL 已在数据库中
in_db = 0
not_in_db = 0
for entry in feed.entries:
    url = entry.get("link") or entry.get("id", "")
    if url in existing_urls:
        in_db += 1
    else:
        not_in_db += 1

print(f"  Feed 中 URL 在数据库中: {in_db}")
print(f"  Feed 中新 URL: {not_in_db}")
db.close()

if not_in_db == 0:
    print("\n  ⚠️ 所有 URL 都已在数据库中（去重跳过）")
    print("  这是正常行为，说明文章已抓取过")

print("\n✅ 调试完成")
