"""
推荐的订阅源列表

使用方法：
1. 复制对应的 FeedSource 添加到数据库
2. 或使用 add_source() 函数添加

分类说明：
- AI前沿: 大模型、基础研究、重大发布
- 游戏美术: AI生成游戏资产生相关内容
- 游戏策划: AI驱动游戏设计、NPC对话
- 使用技巧: 教程、最佳实践
- 工具推荐: 新工具发布、产品
"""

# ============================================================
# 教程/工作流类 (高质量实用内容)
# ============================================================

TUTORIAL_SOURCES = [
    {
        "name": "PyImageSearch",
        "url": "https://pyimagesearch.com/feed/",
        "category": "tutorial",
        "priority": 8,
        "description": "OpenCV和计算机视觉实战教程",
        "tags": ["游戏美术", "使用技巧"],
        "is_practical": True,
    },
    {
        "name": "Towards Data Science - AI",
        "url": "https://towardsdatascience.com/feed",
        "category": "tutorial",
        "priority": 7,
        "description": "AI实战技巧和教程",
        "tags": ["使用技巧", "工具推荐"],
        "is_practical": True,
    },
    {
        "name": "Medium - AI Engineering",
        "url": "https://medium.com/feed/tag/ai-engineering",
        "category": "tutorial",
        "priority": 7,
        "description": "AI工程实践文章",
        "tags": ["使用技巧", "工具推荐"],
        "is_practical": True,
    },
]


# ============================================================
# 高质量垂直源 (强烈推荐)
# ============================================================

RECOMMENDED_SOURCES = [
    # --- 核心AI公司博客 ---
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss/",
        "category": "blog",
        "priority": 10,
        "description": "OpenAI 官方博客，最权威的GPT相关动态",
        "tags": ["AI前沿", "工具推荐"],
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "blog",
        "priority": 10,
        "description": "开源模型生态最活跃的社区博客",
        "tags": ["AI前沿", "使用技巧", "工具推荐"],
    },
    {
        "name": "Stability AI Blog",
        "url": "https://stability.ai/news/feed",
        "category": "blog",
        "priority": 9,
        "description": "Stable Diffusion 背后的公司",
        "tags": ["游戏美术", "AI前沿", "工具推荐"],
    },
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/news/rss",
        "category": "blog",
        "priority": 9,
        "description": "Claude 模型开发商博客",
        "tags": ["AI前沿", "工具推荐"],
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "blog",
        "priority": 9,
        "description": "Google AI 研究院博客",
        "tags": ["AI前沿", "游戏美术"],
    },
    {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/",
        "category": "blog",
        "priority": 8,
        "description": "Meta AI 研究博客，Llama 模型发布地",
        "tags": ["AI前沿", "工具推荐"],
    },
    {
        "name": "Mistral AI Blog",
        "url": "https://mistral.ai/news/feed",
        "category": "blog",
        "priority": 8,
        "description": "欧洲AI独角兽，技术实力强",
        "tags": ["AI前沿", "工具推荐"],
    },

    # --- AI 问答/社区 ---
    {
        "name": "AI Stack Exchange",
        "url": "https://ai.stackexchange.com/feed",
        "category": "community",
        "priority": 8,
        "description": "AI领域专业问答社区，实用的技巧很多",
        "tags": ["AI前沿", "使用技巧"],
        "quality_threshold": 5,  # 至少5票
    },
    {
        "name": "Data Stack Exchange",
        "url": "https://datascience.stackexchange.com/feed",
        "category": "community",
        "priority": 7,
        "description": "数据科学问答社区",
        "tags": ["AI前沿", "使用技巧"],
    },

    # --- Hacker News AI ---
    {
        "name": "Hacker News AI",
        "url": "https://hnrss.org/newest?q=ai&count=30",
        "category": "news",
        "priority": 7,
        "description": "HN上AI相关帖子，已经过社区筛选",
        "tags": ["AI前沿", "工具推荐"],
        "daily_limit": 30,
    },

    # --- Reddit 精选 ---
    {
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA.rss",
        "category": "community",
        "priority": 8,
        "description": "本地LLM部署最活跃社区，实操经验多",
        "tags": ["AI前沿", "使用技巧", "游戏策划"],
        "quality_threshold": 20,
    },
    {
        "name": "Reddit r/StableDiffusion",
        "url": "https://www.reddit.com/r/StableDiffusion.rss",
        "category": "community",
        "priority": 8,
        "description": "SD最活跃社区，工作流和技巧丰富",
        "tags": ["游戏美术", "使用技巧"],
        "quality_threshold": 15,
    },
    {
        "name": "Reddit r/ComfyUI",
        "url": "https://www.reddit.com/r/ComfyUI.rss",
        "category": "community",
        "priority": 8,
        "description": "ComfyUI专属社区，工作流分享",
        "tags": ["游戏美术", "使用技巧"],
        "quality_threshold": 10,
    },
    {
        "name": "Reddit r/GameAI",
        "url": "https://www.reddit.com/r/gameai.rss",
        "category": "community",
        "priority": 7,
        "description": "游戏AI研究社区",
        "tags": ["游戏策划", "AI前沿"],
        "quality_threshold": 5,
    },

    # --- 游戏行业 ---
    {
        "name": "Game Developer",
        "url": "https://www.gamedeveloper.com/rss.xml",
        "category": "community",
        "priority": 8,
        "description": "游戏开发者首选资讯站",
        "tags": ["游戏美术", "游戏策划"],
    },
    {
        "name": "Gamasutra / GameIndustry",
        "url": "https://www.gameindustry.com/rss",
        "category": "news",
        "priority": 7,
        "description": "游戏行业深度分析",
        "tags": ["游戏策划", "游戏美术"],
    },

    # --- 中文AI媒体 ---
    {
        "name": "机器之心",
        "url": "https://jiqizhixin.m.zeoer.com/rss",
        "category": "news",
        "priority": 9,
        "description": "中文最专业的AI媒体，内容质量高",
        "tags": ["AI前沿", "使用技巧", "工具推荐"],
        "language": "zh",
    },
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "category": "news",
        "priority": 8,
        "description": "覆盖全面的中文AI媒体",
        "tags": ["AI前沿", "工具推荐"],
        "language": "zh",
    },
    {
        "name": "少数派",
        "url": "https://sspai.com/feed",
        "category": "blog",
        "priority": 7,
        "description": "中文优质工具使用技巧分享",
        "tags": ["使用技巧", "工具推荐"],
        "language": "zh",
    },
    {
        "name": "即刻",
        "url": "https://web.okjike.com/rss",
        "category": "community",
        "priority": 7,
        "description": "中文互联网人社区，AI讨论活跃",
        "tags": ["AI前沿", "使用技巧"],
        "language": "zh",
    },

    # --- 工具/产品发布 ---
    {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "category": "tools",
        "priority": 6,
        "description": "新产品发布平台，AI工具集中地",
        "tags": ["工具推荐"],
    },
    {
        "name": "Future Tools",
        "url": "https://www.futuretools.io/feed",
        "category": "tools",
        "priority": 6,
        "description": "AI工具精选目录",
        "tags": ["工具推荐"],
    },

    # --- 学术论文 (严格限制) ---
    {
        "name": "ArXiv cs.AI",
        "url": "https://arxiv.org/rss/cs.AI",
        "category": "research",
        "priority": 2,
        "description": "AI学术论文 - 仅保留有代码的高质量研究",
        "tags": ["AI前沿"],
        "daily_limit": 5,
        "is_academic": True,
        "strict_mode": True,  # 必须有代码/实战才能通过
    },
    {
        "name": "ArXiv cs.CV (视觉)",
        "url": "https://arxiv.org/rss/cs.CV",
        "category": "research",
        "priority": 2,
        "description": "计算机视觉论文 - 仅保留有代码的图像生成相关研究",
        "tags": ["AI前沿", "游戏美术"],
        "daily_limit": 5,
        "is_academic": True,
        "strict_mode": True,
    },
    {
        "name": "Papers with Code",
        "url": "https://paperswithcode.com/feed",
        "category": "research",
        "priority": 3,
        "description": "带代码的论文 - 实用性较强",
        "tags": ["AI前沿", "使用技巧"],
        "is_academic": True,
    },

    # --- 行业Newsletter ---
    {
        "name": "The Batch (Andrew Ng)",
        "url": "https://www.deeplearning.ai/the-batch/feed/",
        "category": "newsletter",
        "priority": 8,
        "description": "吴恩达的AI周报，精选有深度",
        "tags": ["AI前沿", "使用技巧"],
    },
    {
        "name": "Import AI",
        "url": "https://importai.substack.com/feed",
        "category": "newsletter",
        "priority": 7,
        "description": "Jack Clark的AI Newsletter",
        "tags": ["AI前沿", "工具推荐"],
    },
    {
        "name": "Last Week in AI",
        "url": "https://lastweekin.ai/feed",
        "category": "newsletter",
        "priority": 7,
        "description": "AI周报，摘要式呈现",
        "tags": ["AI前沿"],
    },

    # --- 游戏AI垂直 ---
    {
        "name": "Midjourney Styles",
        "url": "https://www.midjourney.com/feed/rss",
        "category": "community",
        "priority": 6,
        "description": "MJ官方风格参考",
        "tags": ["游戏美术", "工具推荐"],
    },
]


# ============================================================
# 分类筛选建议
# ============================================================

# 如果你只关注AI前沿，选择这些源：
AI_FRONTIER_SOURCES = [
    "OpenAI Blog",
    "Hugging Face Blog",
    "Anthropic Blog",
    "Google DeepMind Blog",
    "Meta AI Blog",
    "Mistral AI Blog",
    "Hacker News AI",
    "Reddit r/LocalLLaMA",
    "机器之心",
    "The Batch",
    "Import AI",
    "ArXiv cs.AI",
]

# 如果你关注游戏制作，选择这些源：
GAME_DEV_SOURCES = [
    "Hugging Face Blog",
    "Stability AI Blog",
    "Reddit r/StableDiffusion",
    "Reddit r/ComfyUI",
    "Reddit r/GameAI",
    "Game Developer",
    "机器之心",
    "少数派",
]

# 如果你关注工具和效率，选择这些源：
TOOLS_SOURCES = [
    "Hugging Face Blog",
    "Stability AI Blog",
    "AI Stack Exchange",
    "Reddit r/LocalLLaMA",
    "Reddit r/ComfyUI",
    "Product Hunt",
    "Future Tools",
    "少数派",
]


def get_sources_by_category(category: str) -> list:
    """按类别获取订阅源"""
    return [s for s in RECOMMENDED_SOURCES if s.get("category") == category]


def get_sources_by_tags(tags: list) -> list:
    """获取包含指定标签的订阅源"""
    return [s for s in RECOMMENDED_SOURCES if any(t in s.get("tags", []) for t in tags)]


def get_sources_by_language(lang: str) -> list:
    """按语言获取订阅源"""
    return [s for s in RECOMMENDED_SOURCES if s.get("language") == lang]


if __name__ == "__main__":
    print("=== AI情报站 推荐订阅源 ===\n")
    print(f"总计 {len(RECOMMENDED_SOURCES)} 个推荐订阅源\n")

    print("按类别:")
    for cat in ["blog", "community", "news", "tools", "research", "newsletter"]:
        sources = get_sources_by_category(cat)
        if sources:
            print(f"\n  [{cat.upper()}] ({len(sources)}个)")
            for s in sources:
                print(f"    - {s['name']}: {s.get('description', '')[:40]}")

    print("\n\n按语言:")
    print(f"  英文源: {len(get_sources_by_language('en'))}个")
    print(f"  中文源: {len(get_sources_by_language('zh'))}个")
