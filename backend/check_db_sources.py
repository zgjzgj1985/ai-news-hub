"""
检查数据库中的订阅源配置
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, FeedSource

db = SessionLocal()

print("=== 数据库中的订阅源配置 ===\n")

sources = db.query(FeedSource).filter(
    FeedSource.name.in_([
        "Latent Space",
        "Cursor Changelog",
        "Simon Willison",
        "DEV.to Cursor",
    ])
).all()

for s in sources:
    print(f"【{s.name}】")
    print(f"  URL: {s.url}")
    print(f"  启用: {s.enabled}")
    print(f"  优先级: {s.priority}")
    print()

db.close()
