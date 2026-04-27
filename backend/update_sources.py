"""
更新订阅源为新的精选配置 - 游戏开发者专用版

针对用户需求：
1. AI + 游戏设计/工作流
2. 最新 AI 模型动态 (Deepseek V4 等)
3. Vibe coding 最佳实践
4. 实用 AI 工具推荐
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, FeedSource

# 新的订阅源配置（游戏开发者专用精选源）
GAME_DEV_SOURCES = [
    # === AI 前沿动态（最新模型发布）===
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "category": "ai-frontier", "priority": 10},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "category": "ai-frontier", "priority": 10},
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "category": "ai-frontier", "priority": 9},

    # === 游戏 + AI 垂直源 ===
    {"name": "Game Developer", "url": "https://www.gamedeveloper.com/rss.xml", "category": "game-dev", "priority": 9},
    {"name": "r/LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA.rss", "category": "llm-community", "priority": 8},
    {"name": "r/StableDiffusion", "url": "https://www.reddit.com/r/StableDiffusion.rss", "category": "game-art", "priority": 9},
    {"name": "r/ComfyUI", "url": "https://www.reddit.com/r/ComfyUI.rss", "category": "game-art", "priority": 9},
    {"name": "r/GameAI", "url": "https://www.reddit.com/r/gameai.rss", "category": "game-dev", "priority": 8},

    # === Vibe Coding / AI 编程工具 ===
    # Cursor Blog 官方 RSS 已失效，使用社区维护的 RSS 源
    {"name": "Cursor Blog", "url": "https://raw.githubusercontent.com/leontloveless/ai-rss-feeds/main/feeds/cursor-blog.xml", "category": "vibe-coding", "priority": 9},
    {"name": "Windsurf Blog", "url": "https://www.codeium.com/blog/rss.xml", "category": "vibe-coding", "priority": 9},
    {"name": "GitHub Blog", "url": "https://github.blog/feed/", "category": "vibe-coding", "priority": 8},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/blog/rss.xml", "category": "vibe-coding", "priority": 8},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "category": "vibe-coding", "priority": 8},
    {"name": "Hacker News AI", "url": "https://hnrss.org/newest?q=ai+code&count=15", "category": "vibe-coding", "priority": 7},

    # === 中文社区（工具推荐/使用技巧）===
    {"name": "少数派", "url": "https://sspai.com/feed", "category": "tips", "priority": 8},

    # === 学术 + 代码（有代码的论文）===
    {"name": "Papers with Code", "url": "https://paperswithcode.com/feed", "category": "research", "priority": 6},
]

def update_sources():
    db = SessionLocal()

    # 删除旧的订阅源
    old_sources = db.query(FeedSource).all()
    print(f"删除 {len(old_sources)} 个旧订阅源:")
    for s in old_sources:
        print(f"  - {s.name}")

    for s in old_sources:
        db.delete(s)
    db.commit()

    # 添加新的订阅源
    print(f"\n添加 {len(GAME_DEV_SOURCES)} 个游戏开发者专用订阅源:")
    for src in GAME_DEV_SOURCES:
        source = FeedSource(**src)
        db.add(source)
        print(f"  + {src['name']} ({src['category']}) [priority={src['priority']}]")

    db.commit()

    # 验证
    sources = db.query(FeedSource).order_by(FeedSource.priority.desc()).all()
    print(f"\n当前订阅源 ({len(sources)} 个):")
    for s in sources:
        status = "enabled" if s.enabled else "disabled"
        print(f"  [{status}] {s.name} - {s.url[:60]}...")

    db.close()
    print("\n订阅源更新完成!")

if __name__ == "__main__":
    update_sources()
