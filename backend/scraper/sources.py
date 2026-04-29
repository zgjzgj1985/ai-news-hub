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
    "Google DeepMind Blog",
    # 技术博客
    "AI Stack Exchange",
    "Simon Willison",
    # 中文 AI 媒体
    "机器之心",
    "量子位",
    "少数派",
    # 社区
    "Reddit r/LocalLLaMA",
    "Reddit r/ComfyUI",
    "Reddit r/GameAI",
    "Game Developer",
    # 开发者平台
    "DEV.to",
    "Supabase Blog",
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
# =============================================================================
VIBE_CODING_SOURCES = {
    "github_blog": {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "category": "vibe_coding",
        "priority": 9,
    },
    "cursor_blog": {
        "name": "Cursor Blog",
        "url": "https://raw.githubusercontent.com/leontloveless/ai-rss-feeds/main/feeds/cursor-blog.xml",
        "category": "vibe_coding",
        "priority": 9,
        "note": "Cursor 官方博客 RSS（社区维护版本）",
    },
    "cursor_changelog": {
        "name": "Cursor Changelog",
        "url": "https://cursor.com/changelog/rss.xml",
        "category": "vibe_coding",
        "priority": 9,
        "note": "Cursor 更新日志",
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
        "priority": 6,
        "note": "产品发布平台",
    },
    "future_tools": {
        "name": "Future Tools",
        "url": "https://www.futuretools.be/rss",
        "category": "tools",
        "priority": 7,
        "note": "AI 工具收录平台",
    },
}

# =============================================================================
# GitHub Trending 订阅源 - 高优先级
# =============================================================================
GITHUB_TRENDING_SOURCES = {
    "github_trending_all": {
        "name": "GitHub Trending All",
        "url": "https://raw.githubusercontent.com/isboyjc/github-trending-api/main/data/daily/all.xml",
        "category": "vibe_coding",
        "priority": 8,
        "note": "GitHub 每日热门全部分类",
    },
}

# =============================================================================
# Newsletter 订阅源 - 中高优先级
# =============================================================================
NEWSLETTER_SOURCES = {
    "latent_space": {
        "name": "Latent Space",
        "url": "https://latent.space/feed",
        "category": "newsletter",
        "priority": 8,
        "note": "AI 技术深度 Newsletter",
    },
    "latent_space_podcast": {
        "name": "Latent Space Podcast",
        "url": "https://api.substack.com/feed/podcast/1084089.rss",
        "category": "newsletter",
        "priority": 8,
        "note": "AI 工程师访谈播客，含 Cursor/Claude/Google 工程师深度对话",
    },
    "the_gradient": {
        "name": "The Gradient",
        "url": "https://thegradient.pub/rss/",
        "category": "newsletter",
        "priority": 7,
        "note": "AI 学术与产业分析",
    },
    "import_ai": {
        "name": "Import AI Newsletter",
        "url": "https://importai.substack.com/feed",
        "category": "newsletter",
        "priority": 7,
    },
}

FEED_SOURCES = {
    # ========== AI 官方博客（高优先级） ==========
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
    "deepmind_blog": {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "blog",
        "priority": 9,
    },
    "anthropic_blog": {
        "name": "Anthropic Blog",
        "url": "https://raw.githubusercontent.com/0xSMW/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "category": "blog",
        "priority": 9,
        "enabled": True,
        "note": "通过 GitHub 社区维护 RSS 获取",
    },
    "anthropic_engineering": {
        "name": "Anthropic Engineering",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "category": "blog",
        "priority": 9,
        "enabled": True,
        "note": "Anthropic 工程团队博客",
    },

    # ========== Vibe Coding 开发者平台（高优先级） ==========
    "cursor_blog": {
        "name": "Cursor Blog",
        "url": "https://raw.githubusercontent.com/leontloveless/ai-rss-feeds/main/feeds/cursor-blog.xml",
        "category": "vibe_coding",
        "priority": 9,
        "enabled": True,
        "note": "Cursor 官方博客 RSS（社区维护版本）",
    },
    "cursor_changelog": {
        "name": "Cursor Changelog",
        "url": "https://cursor.com/changelog/rss.xml",
        "category": "vibe_coding",
        "priority": 9,
        "enabled": True,
        "note": "Cursor 更新日志",
    },
    "github_blog": {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "category": "vibe_coding",
        "priority": 9,
    },
    "github_trending": {
        "name": "GitHub Trending",
        "url": "https://raw.githubusercontent.com/isboyjc/github-trending-api/main/data/daily/all.xml",
        "category": "vibe_coding",
        "priority": 8,
    },

    # ========== 开发者社区（新增，Vibe Coding 内容丰富） ==========
    "devto_ai": {
        "name": "DEV.to AI",
        "url": "https://dev.to/feed/tag/artificial-intelligence",
        "category": "vibe_coding",
        "priority": 8,
        "note": "开发者社区 AI 文章",
    },
    "devto_cursor": {
        "name": "DEV.to Cursor",
        "url": "https://dev.to/feed/tag/cursor",
        "category": "vibe_coding",
        "priority": 9,
        "note": "Cursor 使用技巧",
    },
    "devto_llm": {
        "name": "DEV.to LLM",
        "url": "https://dev.to/feed/tag/llm",
        "category": "vibe_coding",
        "priority": 8,
        "note": "LLM 开发实践",
    },
    "devto_aicoding": {
        "name": "DEV.to AI Coding",
        "url": "https://dev.to/feed/tag/aicoding",
        "category": "vibe_coding",
        "priority": 9,
        "note": "AI 编程实践",
    },
    "supabase_blog": {
        "name": "Supabase Blog",
        "url": "https://supabase.com/blog/rss.xml",
        "category": "blog",
        "priority": 7,
        "note": "开源 Firebase 替代",
    },

    # ========== 技术博客 ==========
    "simonwillison": {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/entries/",
        "category": "vibe_coding",
        "priority": 9,
        "enabled": True,
        "note": "AI Coding 专家博客（Atom源，可能需验证）",
    },
    "medium_ai": {
        "name": "Medium AI",
        "url": "https://medium.com/feed/tag/artificial-intelligence",
        "category": "blog",
        "priority": 6,
        "note": "Medium AI 文章",
    },

    # ========== AI 工具 ==========
    "product_hunt": {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "category": "tools",
        "priority": 6,
    },
    "future_tools": {
        "name": "Future Tools",
        "url": "https://www.futuretools.be/rss",
        "category": "tools",
        "priority": 7,
    },

    # ========== 行业资讯（降权） ==========
    "hacker_news_ai": {
        "name": "Hacker News AI",
        "url": "https://hnrss.org/newest?q=ai&count=30",
        "category": "news",
        "priority": 6,
        "strict_mode": True,
    },
    "techcrunch_ai": {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "news",
        "priority": 5,
    },
    "venturebeat_ai": {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/feed/",
        "category": "news",
        "priority": 5,
    },
    "wired_ai": {
        "name": "Wired AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "news",
        "priority": 5,
    },
    "mit_tech_review": {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "news",
        "priority": 5,
    },
    "ars_technica_ai": {
        "name": "Ars Technica AI",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "news",
        "priority": 5,
    },

    # ========== 游戏开发（保持高优先级） ==========
    "game_developer": {
        "name": "Game Developer",
        "url": "https://www.gamedeveloper.com/rss.xml",
        "category": "game_dev",
        "priority": 8,
    },
    "80_level": {
        "name": "80 Level",
        "url": "https://80.lv/feed/",
        "category": "game_dev",
        "priority": 8,
    },
    "gdc_vault": {
        "name": "GDC Vault",
        "url": "https://gdcvault.com/rss.xml",
        "category": "game_dev",
        "priority": 9,
    },

    # ========== Newsletter ==========
    "latent_space": {
        "name": "Latent Space",
        "url": "https://latent.space/feed",
        "category": "newsletter",
        "priority": 8,
    },
    "latent_space_podcast": {
        "name": "Latent Space Podcast",
        "url": "https://api.substack.com/feed/podcast/1084089.rss",
        "category": "newsletter",
        "priority": 8,
        "note": "AI 工程师访谈播客，含 Cursor/Claude/Google 工程师深度对话",
    },
    "the_gradient": {
        "name": "The Gradient",
        "url": "https://thegradient.pub/rss/",
        "category": "newsletter",
        "priority": 7,
    },
    "import_ai": {
        "name": "Import AI Newsletter",
        "url": "https://importai.substack.com/feed",
        "category": "newsletter",
        "priority": 7,
    },

    # ========== Reddit 社区 ==========
    "reddit_localllama": {
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA.rss",
        "category": "vibe_coding",
        "priority": 7,
        "enabled": True,
        "note": "Reddit 社区（RSS 可能失效，验证中）",
    },
    "reddit_comfyui": {
        "name": "Reddit r/ComfyUI",
        "url": "https://www.reddit.com/r/ComfyUI.rss",
        "category": "game_dev",
        "priority": 7,
    },
    "reddit_gameai": {
        "name": "Reddit r/GameAI",
        "url": "https://www.reddit.com/r/GameAI.rss",
        "category": "game_dev",
        "priority": 8,
    },

    # ========== 学术来源（极低优先级） ==========
    "arxiv_cs_ai": {
        "name": "ArXiv cs.AI",
        "url": "https://arxiv.org/rss/cs.AI",
        "category": "research",
        "priority": 1,
        "strict_mode": True,
    },
    "arxiv_cs_cv": {
        "name": "ArXiv cs.CV (视觉)",
        "url": "https://arxiv.org/rss/cs.CV",
        "category": "research",
        "priority": 1,
        "strict_mode": True,
    },

    # ========== 中文 AI 媒体（中等优先级） ==========
    "jiqizhixin": {
        "name": "机器之心",
        "url": "https://jiqizhixin.com/rss",
        "category": "news",
        "priority": 7,
    },
    "liangziweizhi": {
        "name": "量子位",
        "url": "https://www.qbitai.com/rss",
        "category": "news",
        "priority": 6,
    },
    "sspaimei": {
        "name": "少数派",
        "url": "https://sspai.com/rss",
        "category": "blog",
        "priority": 7,
    },

    # ========== 已禁用的订阅源（保留配置，方便后续恢复） ==========
    "verge_ai": {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "news",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (403)",
    },
    "windsurf_blog": {
        "name": "Windsurf Blog",
        "url": "https://www.codeium.com/blog/rss.xml",
        "category": "vibe_coding",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (无内容)",
    },
    "meta_ai": {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/rss/",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (404)",
    },
    "mistral_ai": {
        "name": "Mistral AI Blog",
        "url": "https://mistral.ai/news/rss/",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (404)",
    },
    "towards_data_science": {
        "name": "Towards Data Science",
        "url": "https://towardsdatascience.com/feed",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (403)",
    },
    "minimax": {
        "name": "MiniMax",
        "url": "https://www.minimax.io/news",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "无有效 RSS",
    },
    "kimi": {
        "name": "Kimi AI",
        "url": "https://kimi.moonshot.cn/rss",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (无内容)",
    },
    "zhipuai": {
        "name": "智谱AI",
        "url": "https://www.zhipuai.cn/rss",
        "category": "blog",
        "priority": 0,
        "enabled": False,
        "note": "RSS 失效 (无内容)",
    },
}


# =============================================================================
# 来源判断函数
# =============================================================================

def is_academic_source(source_name: str) -> bool:
    """判断是否为学术来源"""
    for source in ACADEMIC_SOURCES.values():
        if source["name"] == source_name:
            return True
    return False


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
    # 从 FEED_SOURCES 中查找
    for source in FEED_SOURCES.values():
        if source.get("name") == source_name:
            return source.get("priority", 5)
    return 5
