"""Content classification based on keywords and source intelligence."""

import re

# ============================================================
# 来源分类配置
# ============================================================

# 学术来源 - 需要严格评审
ACADEMIC_SOURCES = [
    "ArXiv cs.AI",
    "ArXiv cs.CV (视觉)",
    "Papers with Code",
    "MIT Technology Review",
]

# 实用型来源 - 优先推荐
PRACTICAL_SOURCES = [
    "OpenAI Blog",
    "Hugging Face Blog",
    "Stability AI Blog",
    "Anthropic Blog",
    "Google DeepMind Blog",
    "AI Stack Exchange",
    "Reddit r/LocalLLaMA",
    "Reddit r/ComfyUI",
    "Game Developer",
    "机器之心",
    "少数派",
]

# 游戏开发来源 - 启用宽松模式匹配
GAME_DEV_SOURCES = [
    "80 Level",
    "Game Developer",
    "r/GameAI",
    "r/gamedev",
    "r/StableDiffusion",
    "r/ComfyUI",
    "r/blender",
    "r/unity3d",
    "r/unrealengine",
    "r/godot",
    "Gamasutra",
    "GDC",
    "Unity Blog",
    "Unreal Engine Blog",
]

# 宽松模式关键词 - 用于游戏开发来源
# 这些关键词在游戏开发来源中会直接加分（不需要 game 上下文）
GAME_ART_RELAXED_KEYWORDS = [
    "pixel art", "splash art", "concept art", "character art", "environment art",
    "sprite", "3D art", "2D art", "digital art", "matte painting",
    "character design", "environment design", "level art", "prop art",
    "texturing", "modeling", "rigging", "animation",
    "game art", "game asset", "game character", "game environment",
    "texture", "PBR", "normal map", "UV mapping",
    "blender", "maya", "zbrush", "substance", "marmoset",
    "game engine", "game engine", "ue5", "ue4", "unity3d",
    "rendering", "render engine", "octane", "cycles",
    "illustration", "painting", "drawing", "sketch",
]

GAME_PLAN_RELAXED_KEYWORDS = [
    "game design", "gameplay", "game mechanic", "level design",
    "NPC", "quest", "dialogue", "story", "narrative",
    "AI NPC", "AI game", "procedural", "PCG",
    "game balancing", "difficulty", "progression",
    "RPG", "roguelike", "metroidvania", "MMO",
    "game jam", "game dev", "indie game",
]

# 学术论文特征 - 包含这些的文章会被降权
ACADEMIC_PATTERNS = [
    r"arxiv:\d+\.\d+",
    r"paper:",
    r"conference:",
    r"journal:",
    r"\d+ pages",
    r"abstract",
    r"introduction",
    r"related work",
    r"methodology",
    r"experiment",
    r"conclusion",
    r"doi:",
    r"citation",
    r"peer-reviewed",
]


# Tag definitions with keywords and weights
# weight: 1=普通关键词, 2=重要关键词, 3=核心关键词
TAG_RULES = {
    "vibe_coding": {
        "core": [
            # Vibe Coding 核心理念
            "vibe coding", "vibe-coding", "vibe engineer",
            "prompt to code", "natural language to code",
            "ai coding workflow", "ai coding assistant",
            "claude code", "cursor composer", "windsurf cascade",
            "copilot workspace", "github copilot update",
            "cursor best practice", "cursor tips", "cursor workflow",
            "windsurf best practice", "windsurf tips", "windsurf workflow",
            "aider", "continue dev", "devin", "replit agent",
            "v0 dev", "bolt new", "lovable dev",
            # AI Coding 具体实践
            "building with ai", "ship with ai", "code with ai",
            "claude for code", "github copilot",
            "codeium windsurf", "tabnine",
            "AI agent coding", "agentic coding workflow",
            "pair programming with ai", "ai pair programmer",
            # 具体使用技巧
            "best cursor settings", "best copilot settings",
            "cursor keyboard shortcuts", "copilot shortcuts",
            "AI coding tips", "AI coding tricks",
            "how I built with AI", "what I learned using AI to code",
            # 开发者实践
            "forrest chang", "andrej karpathy skills",
            "awesome vibe coding", "cursor resources",
        ],
        "important": [
            # AI 编程工具
            "cursor", "windsurf", "copilot", "codeium", "tabnine",
            "aider", "continue", "devin", "replit",
            "v0", "bolt", "lovable", "framer dev",
            # 编程实践
            "LLM coding", "GPT coding", "AI pair programmer",
            "AI code review", "AI refactoring",
            "building with llm", "llm app development",
            "RAG implementation", "AI agent",
            # 开发工作流
            "cursor rule", "cursor config", "cursor mcp",
            "copilot chat", "copilot inline",
            # 社区讨论
            "HN: built with", "HN: ask: AI coding",
            "my experience with AI coding",
        ],
        "general": [
            "AI coding", "ai-assisted development",
            "vibe engineering", "vibe dev",
            "智能编码", "AI 开发助手",
            "AI 软件开发", "人工智能编程",
        ]
    },
    "AI前沿": {
        "core": [
            # 最新模型发布（2024-2026）
            "gpt-5", "gpt4", "gpt-4o", "o1", "o3", "o4", "o4-mini",
            "claude opus", "claude 4", "claude 3.5", "claude 3", "sonnet",
            "gemini 2", "gemini 1.5", "gemini ultra",
            "llama 4", "llama 3.3", "llama 3.1", "llama 3", "llama-3",
            "mistral large", "mistral 3", "mixtral", "pixtral",
            "grok 2", "grok-1", "grok-2", "xai",
            "deepseek v4", "deepseek v3", "deepseek-r1", "deepseek-coder",
            "qwen 3", "qwen 2.5", "qwen-max", "qwen2",
            "yi lightning", "yi 34b", "yi-tech",
            "openai release", "anthropic release", "google release",
            "meta release", "mistral release", "xai release",
            "new model", "model launch", "model release",
            "breakthrough", "state-of-the-art", "sota",
            "open source llm", "open-source model",
            # Vibe Coding 核心
            "vibe coding", "vibe-coding", "agentic coding",
            "claude code", "cursor composer", "windsurf cascade",
            "copilot workspace", "github copilot update",
            "cursor best practice", "cursor workflow",
            "ai coding workflow", "ai coding assistant",
        ],
        "important": [
            "llm", "lstm", "transformer architecture",
            "diffusion model", "diffusion transformer",
            "sora", "sora 2", "text-to-video", "video generation",
            "stable diffusion 3", "stable diffusion xl", "sdxl",
            "flux model", "flux 1", "image generation", "text-to-image", "image-to-image",
            "embedding", "vector model", "reranker",
            "fine-tuning", "rlhf", "dpo", "pre-training",
            "context window", "1m context", "100k context",
            "api release", "github release",
            "local llm", "ollama", "llama.cpp", "llamafile",
            "vibe engineering", "ai-assisted development",
            # Vibe Coding 工具
            "cursor ai", "windsurf ai", "claude for code",
            "github copilot", "copilot x", "tabnine",
            "aider", "continue dev", "devin",
            "vibe engineer", "prompt to code", "natural language to code",
            # 国产模型
            "baichuan", "yi model", "internlm", "GLM model",
            "智谱", "百川", "通义千问", "文心一言",
        ],
        "general": [
            "gpt", "claude", "gemini", "llama",
            "ai model", "language model", "neural network",
            "artificial intelligence", "machine learning", "deep learning",
            "ai release", "ai update", "model update",
        ]
    },
    "游戏美术": {
        "core": [
            # 游戏资产生成
            # 游戏资产生成 - 必须有明确的游戏上下文
            "game art", "game asset", "game character", "game environment",
            "game prop", "game weapon", "game armor", "game icon",
            "sprite sheet", "sprite generation", "pixel art game",
            "AI game art", "AI game asset", "AI game character",
            "stable diffusion for games", "midjourney for games",
            "ComfyUI game", "game workflow", "ComfyUI workflow game",
            "game asset generation", "AI creature game",
            "tileable texture game", "PBR texture game",
            # 3D游戏资产生成
            "3D game asset", "game 3D", "text-to-3D game",
            "tripoSR game", "tripo3d game", "meshy game",
            "recraft 3D game", "spline AI game",
            # 游戏动画/绑定
            "game motion capture", "game animation", "game rigging",
            # 引擎集成
            "unreal engine game", "UE5 game", "unity game asset",
            "ue5 marketplace", "unreal marketplace asset",
        ],
        "important": [
            # 游戏美术专用的AI工具关键词
            "game LoRA", "LoRA training game",
            "ControlNet game", "IP-Adapter game",
            "DCC tool game", "blender game", "maya game",
            "game art pipeline", "game asset pipeline", "美术工作流",
        ],
        "general": [
            # 仅保留强游戏上下文的通用词汇
            "game art", "game asset", "game sprite", "game icon", "game ui",
            "unreal engine", "unity 3d", "blender game", "游戏美术",
        ]
    },
    "游戏策划": {
        "core": [
            # AI NPC 与对话
            "AI NPC", "AI companion", "AI character", "AI enemy",
            "AI game jam", "AI dungeon", "AI dungeon master",
            "procedural dungeon", "procedural world", "procedural generation",
            "PCG", "procedural content generation",
            "AI game master", "AI dungeon master",
            "narrative generation", "story generation", "plot generation",
            "dialogue system", "conversation AI", "voice NPC",
            "NPC dialogue", "character dialogue", "dialogue generation",
            "AI quest", "quest generation", "mission generation",
            "gameplay generation", "level design AI", "AI level design",
            "game design AI", "game balancing AI", "difficulty scaling",
            "procedural game", "roguelike generation",
            # AI 游戏引擎
            "game engine ai", "engine integration", "unity openai",
            "unreal metahuman", "npc dialogue ai",
        ],
        "important": [
            # 游戏策划专用的AI NPC和游戏系统关键词
            "NPC behavior", "NPC AI", "enemy AI", "pathfinding",
            "behavior tree", "state machine", "utility AI",
            "game AI", "smart NPC",
            "conversation system", "dialogue tree", "branching narrative",
            "world building", "lore generation", "backstory generation",
            "character AI", "AI ally", "AI antagonist",
            "procedural quest", "dynamic event", "dynamic narrative",
            "story-driven", "choice system", "player agency",
            "game narrative", "interactive fiction", "visual novel",
            "AI storyteller", "AI editor",
            # 游戏策划工具
            "AI writing", "AI narrative", "AI storytelling",
            "procedural content generation", "PCG",
            "game prototyping", "design prototyping",
            # AI游戏相关
            "AI dungeon", "AI roguelike", "roguelike AI",
            "procedural narrative", "auto storytelling",
            "game jam AI", "Ludum Dare AI",
            # 以下为高风险误匹配词，已移除：
            # conversation AI, dialogue generation (太通用，AI模型发布/技术文章也会匹配)
            # AI writer (太通用)
            # game gameplay AI (gameplay 太通用)
        ],
        "general": [
            # 仅保留游戏策划专用的通用词汇
            "NPC", "quest",
            "game design", "level design", "游戏策划", "关卡设计", "剧情设计", "游戏玩法",
            # 以下为高风险误匹配词，已移除：
            # dialogue, story, narrative, gameplay (太通用，AI模型发布/技术文章也会匹配)
        ]
    },
    "使用技巧": {
        "core": [
            # Vibe Coding 教程
            "prompt engineering", "prompt tutorial", "prompt guide",
            "best practice", "best practices", "tutorial",
            "step by step", "getting started", "beginner guide",
            "advanced tips", "advanced techniques",
            "ComfyUI tutorial", "ComfyUI workflow", "ComfyUI guide",
            "stable diffusion tutorial", "SD tutorial",
            "midjourney parameters", "MJ settings",
            "chatgpt prompt", "claude prompt", "gemini prompt",
            # Vibe Coding 实践
            "cursor tutorial", "windsurf tutorial", "claude code guide",
            "vibe coding guide", "ai coding workflow",
            "copilot tutorial", "github copilot guide",
            # 本地部署
            "ollama tutorial", "llama.cpp tutorial", "local llm guide",
        ],
        "important": [
            "how to", "guide", "tips", "tricks", "cheat sheet",
            "prompt", "mastery", "learning",
            "negative prompt", "positive prompt", "prompt structure",
            "workflow", "pipeline", "process",
            "optimize", "optimization", "speed up", "faster",
            "quality improvement", "better results", "enhance",
            "ControlNet settings", "LoRA combine", "model merge",
            # 开发技巧
            "api key setup", "api configuration", "环境配置",
            "model deployment", "inference optimization",
            "RAG tutorial", "知识库构建", "向量数据库",
        ],
        "general": [
            "learn", "learning", "study", "practice",
            "教程", "指南", "技巧", "心得", "经验",
        ]
    },
    "工具推荐": {
        "core": [
            # Vibe Coding 工具
            "cursor", "windsurf", "claude code", "copilot",
            "Perplexity", "NotebookLM", "Gamma AI",
            "v0", "bolt", "lovable", "Replit Agent",
            "new tool", "new app", "launch", "released",
            "product launch", "app release", "official release",
            "open source", "open-source", "github",
            "best AI tools", "top AI tools", "AI tools list",
            # 游戏制作工具
            "comfyui release", "forge release", "automatic1111 update",
            "unity muse", "unreal gauss",
            "ideogram", "flux dev", "midjourney v7",
        ],
        "important": [
            "tool release", "tool launch", "framework release",
            "library release", "SDK release", "API release",
            "product update", "major update", "new feature",
            "alternative", "replacement", "better than",
            "best of", "collection", "curated list",
            # 开发工具
            "vscode extension", "jetbrains plugin", "ide plugin",
            "chrome extension", "vscode theme", "开发工具",
        ],
        "general": [
            "tool", "app", "software", "platform",
            "framework", "library", "API", "SDK",
            "工具", "软件", "应用", "产品",
        ]
    },

    # ============================================================
    # 新增：生产落地标签 - 区分学术和实用内容
    # ============================================================
    "生产落地": {
        "core": [
            "production", "production-ready", "in production",
            "case study", "how we built", "lessons learned",
            "real-world", "真实案例", "落地实践",
            "at scale", "architecture at scale", "系统架构",
            "deployment", "scaling", "production system",
            "实战", "生产环境", "上线", "部署",
            "GitHub", "github.com", "open source",
            "code example", "代码示例", "示例代码",
            "tutorial", "教程", "上手指南", "getting started",
        ],
        "important": [
            "step by step", "implementation", "实现",
            "workshop", "bootcamp", "hands-on",
            "integrate", "integration", "集成",
            "setup", "installation", "安装配置",
            "best practice", "最佳实践", "经验总结",
            "workflow", "pipeline", "工作流",
            "prompt template", "提示词模板",
            "architecture design", "架构设计",
        ],
        "general": [
            "learn", "learning", "study", "practice",
            "build", "creating", "开发", "制作",
        ]
    },
}

# 排除词 - 包含这些词的文章通常不是目标内容
EXCLUDE_PATTERNS = [
    "cryptocurrency", "crypto", "bitcoin", "ethereum", "NFT", "web3",
    "ICO", "token sale", "blockchain gaming", "move-to-earn",
    "sports score", "sports prediction", "stock prediction",
    "only fans", "adult content", "18+",
]

# 来源质量权重 - 某些来源的内容质量更高
SOURCE_QUALITY_WEIGHT = {
    # AI 公司博客 - 权威来源
    "OpenAI Blog": 2.5,
    "Hugging Face Blog": 2.5,
    "Stability AI Blog": 2.0,
    "Google DeepMind Blog": 2.5,

    # Vibe Coding 核心来源 - 最高权重
    "Cursor Blog (社区RSS)": 3.0,
    "GitHub Blog": 2.5,
    "GitHub Trending": 2.0,
    "Simon Willison": 1.0,  # AI Coding 专家，但对 vibe coding 持批评态度

    # DEV.to 开发者社区 - Vibe Coding 内容丰富
    "DEV.to": 2.5,
    "DEV.to Cursor": 3.0,
    "DEV.to AI Coding": 3.0,
    "DEV.to LLM": 2.5,
    "DEV.to AI": 2.5,

    # 游戏开发社区
    "Game Developer": 2.5,
    "GDC Vault": 2.5,
    "80 Level": 2.5,
    "Reddit r/ComfyUI": 2.2,
    "Reddit r/LocalLLaMA": 1.8,
    "Reddit r/GameAI": 2.5,

    # Newsletter
    "Latent Space": 2.5,
    "The Gradient": 2.0,
    "Import AI Newsletter": 2.0,

    # AI 工具平台
    "Product Hunt": 2.0,
    "Future Tools": 2.0,

    # 技术博客
    "Supabase Blog": 2.2,
    "Medium AI": 1.5,

    # 中文媒体
    "机器之心": 2.2,
    "量子位": 2.0,
    "少数派": 2.2,

    # 通用新闻源 - 降权
    "Hacker News AI": 0.5,
    "MIT Technology Review": 0.6,
    "TechCrunch AI": 0.6,
    "VentureBeat AI": 0.5,
    "Wired AI": 0.5,
    "Ars Technica AI": 0.5,

    # 学术来源 - 大幅降权
    "ArXiv cs.AI": 0.2,
    "ArXiv cs.CV (视觉)": 0.2,
    "ArXiv cs.LG": 0.2,
}


def _calculate_tag_score(tag: str, text_lower: str, title_lower: str = "") -> float:
    """计算某个标签的匹配分数"""
    rules = TAG_RULES.get(tag, {})
    score = 0.0

    # 核心关键词匹配 (权重3)
    for kw in rules.get("core", []):
        if kw.lower() in title_lower:
            score += 3.0  # 标题命中权重更高
        elif kw.lower() in text_lower:
            score += 2.5

    # 重要关键词匹配 (权重2)
    for kw in rules.get("important", []):
        if kw.lower() in title_lower:
            score += 1.5
        elif kw.lower() in text_lower:
            score += 1.0

    # 一般关键词匹配 (权重1)
    for kw in rules.get("general", []):
        if kw.lower() in text_lower:
            score += 0.5

    return score


def is_academic_content(text: str, source_name: str = "") -> bool:
    """
    检测内容是否为学术论文

    判断依据：
    1. 来源是学术源
    2. 包含学术论文特征模式
    """
    # 来源检测
    if source_name in ACADEMIC_SOURCES:
        return True

    # 模式检测
    for pattern in ACADEMIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def classify(text: str, source_name: str = "", title: str = "") -> list[str]:
    """
    基于关键词权重的内容分类。

    改进点：
    1. 标题匹配优先于正文匹配
    2. 核心关键词权重更高
    3. 来源质量影响最终分类
    4. 排除词机制过滤噪音
    5. 学术来源降权，实用来源加权
    6. 新增生产落地标签识别
    7. Vibe Coding 来源优先匹配 vibe_coding 标签
    8. 游戏开发来源启用宽松模式匹配
    """
    text_lower = text.lower()
    title_lower = (title or "").lower()
    combined_lower = title_lower + " " + text_lower

    # 排除词过滤
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in combined_lower:
            return ["AI前沿"]

    # 检测是否为学术内容
    is_academic = is_academic_content(combined_lower, source_name)

    # Vibe Coding 核心来源列表
    # 优先级降低：Simon Willison 持批评态度，降低权重
    VIBE_CODING_CORE_SOURCES = [
        # AI Coding 工具 - 最高优先级
        "Cursor Blog", "Cursor Blog (社区RSS)", "Cursor Changelog",
        "GitHub Blog", "GitHub Trending",
        # DEV.to 开发者社区 - 高质量教程
        "DEV.to", "DEV.to Cursor", "DEV.to AI Coding", "DEV.to LLM", "DEV.to AI",
        # Newsletter - 仅高质量内容
        "Latent Space",
    ]

    # Vibe Coding 降权来源 - 这些来源内容参差不齐
    VIBE_CODING_WEAK_SOURCES = [
        "Simon Willison",  # 对 Vibe Coding 持批评态度
        "Latent Space Podcast",  # 播客转文字，质量较低
        "Import AI Newsletter",  # 新闻性质为主
        "The Gradient",  # 学术性质为主
    ]

    tag_scores = {}

    for tag in TAG_RULES.keys():
        score = _calculate_tag_score(tag, text_lower, title_lower)

        # 来源质量加权
        source_weight = SOURCE_QUALITY_WEIGHT.get(source_name, 1.0)

        # 学术来源降权
        if is_academic and tag in ["AI前沿", "工具推荐", "使用技巧"]:
            source_weight *= 0.3  # 大幅降低学术来源权重

        # 实用来源加权
        elif source_name in PRACTICAL_SOURCES and tag in ["使用技巧", "工具推荐", "生产落地"]:
            source_weight *= 1.5

        # Vibe Coding 来源加权
        if source_name in VIBE_CODING_CORE_SOURCES and tag == "vibe_coding":
            source_weight *= 2.5  # 核心来源大幅加权

        # Vibe Coding 降权来源 - 降低权重
        if source_name in VIBE_CODING_WEAK_SOURCES and tag == "vibe_coding":
            source_weight *= 0.3  # 降权至 30%

        score *= source_weight

        if score > 0:
            tag_scores[tag] = score

        # 游戏开发来源启用宽松模式匹配
    is_game_dev_source = source_name in GAME_DEV_SOURCES
    if is_game_dev_source:
        # 游戏美术宽松模式加分
        art_relaxed_score = 0.0
        for kw in GAME_ART_RELAXED_KEYWORDS:
            if kw.lower() in title_lower:
                art_relaxed_score += 2.0
            elif kw.lower() in text_lower:
                art_relaxed_score += 1.0

        # 游戏策划宽松模式加分
        plan_relaxed_score = 0.0
        for kw in GAME_PLAN_RELAXED_KEYWORDS:
            if kw.lower() in title_lower:
                plan_relaxed_score += 2.0
            elif kw.lower() in text_lower:
                plan_relaxed_score += 1.0

        # 应用宽松模式分数
        if "游戏美术" in tag_scores:
            tag_scores["游戏美术"] += art_relaxed_score
        elif art_relaxed_score >= 2.0:  # 标题中1个关键词即可触发
            tag_scores["游戏美术"] = 5.0  # 直接设置为通过阈值

        if "游戏策划" in tag_scores:
            tag_scores["游戏策划"] += plan_relaxed_score
        elif plan_relaxed_score >= 2.0:
            tag_scores["游戏策划"] = 5.0  # 直接设置为通过阈值

    # 学术内容强制添加生产落地标签检查（如果没匹配则降级）
    if is_academic and "生产落地" not in tag_scores:
        # 检查是否有生产落地相关关键词
        production_keywords = ["github", "code", "tutorial", "towards", "实战", "案例", "production"]
        if not any(kw in combined_lower for kw in production_keywords):
            # 纯学术内容降级处理
            pass  # 不做额外处理，让评审阶段过滤

    # 至少5分以上才打标签（提高阈值避免单关键词误匹配）
    MIN_SCORE = 5.0

    matched_tags = [tag for tag, score in tag_scores.items() if score >= MIN_SCORE]

    # Vibe Coding 核心来源的文章，即使分数不够也优先打 vibe_coding 标签
    if source_name in VIBE_CODING_CORE_SOURCES and "vibe_coding" not in matched_tags:
        vibe_score = _calculate_tag_score("vibe_coding", text_lower, title_lower)
        if vibe_score >= 3.0:  # 提高阈值至 3 分
            matched_tags.append("vibe_coding")

    # Vibe Coding 降权来源 - 只有高质量内容才打标签
    if source_name in VIBE_CODING_WEAK_SOURCES and "vibe_coding" not in matched_tags:
        vibe_score = _calculate_tag_score("vibe_coding", text_lower, title_lower)
        if vibe_score >= 5.0:  # 降权来源需要 5 分以上
            matched_tags.append("vibe_coding")

    # 如果没有任何标签命中，但来源是AI专业源，默认打AI前沿
    if not matched_tags and source_name in [
        "OpenAI Blog", "Hugging Face Blog", "Stability AI Blog",
        "Google DeepMind Blog", "AI Stack Exchange", "机器之心", "量子位",
        "Import AI", "Last Week in AI", "The Batch",
    ]:
        matched_tags = ["AI前沿"]

    # ArXiv 默认不自动打标签，让评审阶段过滤
    if not matched_tags and is_academic:
        return []  # 返回空列表，不自动打任何标签

    return sorted(matched_tags) if matched_tags else ["AI前沿"]
