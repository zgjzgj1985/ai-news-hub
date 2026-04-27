"""RSS data source configuration."""

# =============================================================================
# 来源分类配置
# =============================================================================

# 学术来源 - 极低优先级，仅保留有代码的论文
ACADEMIC_SOURCES = {
    "arxiv_cs_ai": {
        "name": "ArXiv cs.AI",
        "url": "https://arxiv.org/rss/cs.AI",
        "category": "research",
        "priority": 1,  # 极低优先级
        "strict_mode": True,
    },
    "arxiv_cs_cv": {
        "name": "ArXiv cs.CV (视觉)",
        "url": "https://arxiv.org/rss/cs.CV",
        "category": "research",
        "priority": 1,  # 极低优先级
        "strict_mode": True,
    },
}

# 实用型来源 - 优先推荐
PRACTICAL_SOURCES = [
    # AI 官方博客
    "OpenAI Blog",
    "Hugging Face Blog",
    "Stability AI Blog",
    "Anthropic Blog",
    "Google DeepMind Blog",
    "Meta AI Blog",
    "Mistral AI Blog",
    "MiniMax",
    "Kimi AI",
    "智谱AI",
    # 技术博客
    "AI Stack Exchange",
    "Simon Willison",
    "Towards Data Science",
    # 中文 AI 媒体
    "机器之心",
    "量子位",
    "少数派",
    # 社区
    "Reddit r/LocalLLaMA",
    "Reddit r/ComfyUI",
    "Reddit r/StableDiffusion",
    "Reddit r/GameAI",
    "Game Developer",
]

# 必须有代码/实战的来源
REQUIRE_CODE_SOURCES = [
    "ArXiv cs.AI",
    "ArXiv cs.CV (视觉)",
    "Papers with Code",
]


# =============================================================================
# 游戏开发者专用来源 - 高优先级
# =============================================================================
GAME_DEV_SOURCES = {
    "gdc_vault": {
        "name": "GDC Vault",
        "url": "https://gdcvault.com/rss.xml",
        "category": "game_dev",
        "priority": 9,
    },
    "gamedeveloper": {
        "name": "Game Developer",
        "url": "https://www.gamedeveloper.com/rss.xml",
        "category": "game_dev",
        "priority": 8,
    },
    "indiegamesplus": {
        "name": "Indie Games Plus",
        "url": "https://indiegamesplus.com/feed",
        "category": "game_dev",
        "priority": 7,
    },
    "80_lv": {
        "name": "80 Level",
        "url": "https://80.lv/feed/",
        "category": "game_dev",
        "priority": 8,  # 技术美术核心来源
    },
}

# =============================================================================
# Vibe Coding 专用来源 - 高优先级
# 注意: Cursor Blog RSS (cursor.com/blog/rss.xml) 已失效，改用社区替代
# =============================================================================
VIBE_CODING_SOURCES = {
    "windsurf_blog": {
        "name": "Windsurf Blog",
        "url": "https://www.codeium.com/blog/rss.xml",
        "category": "vibe_coding",
        "priority": 9,
    },
    "github_blog": {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "category": "vibe_coding",
        "priority": 8,
    },
    "cursor_blog": {
        "name": "Cursor Blog (社区RSS)",
        "url": "https://raw.githubusercontent.com/leontloveless/ai-rss-feeds/main/feeds/cursor-blog.xml",
        "category": "vibe_coding",
        "priority": 9,
        "note": "官方RSS失效，使用社区维护版本，每小时更新",
    },
}

# =============================================================================
# AI 工具资讯来源 - 中高优先级
# =============================================================================
AI_TOOLS_SOURCES = {
    "product_hunt": {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "category": "tools",
        "priority": 7,
    },
    "there's_an_ai": {
        "name": "There's an AI for That",
        "url": "https://theresanaiforthat.com/rss/",
        "category": "tools",
        "priority": 7,
    },
    "futuretools": {
        "name": "Future Tools",
        "url": "https://www.futuretools.io/feed",
        "category": "tools",
        "priority": 7,
    },
}

FEED_SOURCES = {
    "hacker_news_ai": {
        "name": "Hacker News AI",
        "url": "https://hnrss.org/newest?q=ai&count=30",
        "category": "news",
        "priority": 8,
        "strict_mode": True,  # 启用严格模式，只收录AI相关内容
    },
    "mit_tech_review": {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "news",
        "priority": 7,
        "strict_mode": True,
    },
    "openai_blog": {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "blog",
        "priority": 9,
    },
    "huggingface_blog": {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "blog",
        "priority": 9,
    },
    "verge_ai": {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "news",
        "priority": 7,
    },
    "stability_ai": {
        "name": "Stability AI Blog",
        "url": "https://stability.ai/news/feed",
        "category": "blog",
        "priority": 8,
    },
    "game_developer": {
        "name": "Game Developer",
        "url": "https://www.gamedeveloper.com/rss.xml",
        "category": "community",
        "priority": 7,
    },
    "arxiv_cs_ai": {
        "name": "ArXiv cs.AI",
        "url": "https://arxiv.org/rss/cs.AI",
        "category": "research",
        "priority": 1,  # 极低优先级
        "strict_mode": True,  # 必须有代码或实战
    },
    # ========== 新增高质量来源 ==========
    "anthropic_blog": {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/blog/rss.xml",
        "category": "blog",
        "priority": 9,
    },
    "deepmind_blog": {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "blog",
        "priority": 9,
    },
    "meta_ai": {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/rss/",
        "category": "blog",
        "priority": 8,
    },
    "mistral_ai": {
        "name": "Mistral AI Blog",
        "url": "https://mistral.ai/news/rss/",
        "category": "blog",
        "priority": 8,
    },
    "import_ai": {
        "name": "Import AI Newsletter",
        "url": "https://importai.substack.com/feed",
        "category": "newsletter",
        "priority": 7,
    },
    "the_batch": {
        "name": "The Batch",
        "url": "https://www.deeplearning.ai/the-batch/rss/",
        "category": "newsletter",
        "priority": 7,
    },
    "venturebeat_ai": {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/ai/feed/",
        "category": "news",
        "priority": 7,
    },
    "techcrunch_ai": {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "news",
        "priority": 7,
    },
    "wired_ai": {
        "name": "Wired AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "news",
        "priority": 6,
    },
    "ars Technica AI": {
        "name": "Ars Technica AI",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "news",
        "priority": 6,
    },
    "towards_data_science": {
        "name": "Towards Data Science",
        "url": "https://towardsdatascience.com/feed",
        "category": "blog",
        "priority": 6,
    },
    "simonwillison": {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom Einträge",
        "category": "blog",
        "priority": 7,
    },
    "jimfan": {
        "name": "Jim Fan (AI Scientist)",
        "url": "https://notes.neuronsharvest.com/feed",
        "category": "blog",
        "priority": 6,
    },
    "minimax": {
        "name": "MiniMax",
        "url": "https://www.minimaxi.com/news/rss",
        "category": "blog",
        "priority": 7,
    },
    "kimi": {
        "name": "Kimi AI",
        "url": "https://kimi.moonshot.cn/rss",
        "category": "blog",
        "priority": 7,
    },
    "zhipuai": {
        "name": "智谱AI",
        "url": "https://www.zhipuai.cn/rss",
        "category": "blog",
        "priority": 7,
    },
    # ========== Cursor 官方来源 (社区维护的RSS) ==========
    "cursor_blog": {
        "name": "Cursor Blog (社区RSS)",
        "url": "https://raw.githubusercontent.com/leontloveless/ai-rss-feeds/main/feeds/cursor-blog.xml",
        "category": "vibe_coding",
        "priority": 9,
        "note": "官方RSS失效，使用社区维护版本，每小时更新",
    },
}


# =============================================================================
# 来源判断函数
# =============================================================================

def is_academic_source(source_name: str) -> bool:
    """判断是否为学术来源"""
    return source_name in ACADEMIC_SOURCES or source_name in REQUIRE_CODE_SOURCES


def is_practical_source(source_name: str) -> bool:
    """判断是否为实用型来源"""
    return source_name in PRACTICAL_SOURCES


def requires_code(source_name: str) -> bool:
    """判断来源是否必须有代码"""
    return source_name in REQUIRE_CODE_SOURCES


def get_source_priority(source_name: str) -> int:
    """获取来源优先级（实用型来源优先）"""
    if is_practical_source(source_name):
        return 10
    if is_academic_source(source_name):
        return 3
    return 5
