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
    "Reddit r/StableDiffusion",
    "Game Developer",
    "机器之心",
    "少数派",
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
    "AI前沿": {
        "core": [
            # 最新模型发布（2024-2026）
            "gpt-5", "gpt4", "gpt-4o", "o1", "o3", "o4", "o4-mini",
            "claude 4", "claude 3.5", "claude 3", "sonnet",
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
            "concept art", "character concept", "environment concept",
            "game art", "game asset", "3d game art",
            "texture generation", "texture synthesis",
            "sprite sheet", "pixel art generation",
            "AI game art", "AI asset", "procedural game art",
            "stable diffusion game", "midjourney game", "SD game art",
            "ComfyUI game", "game workflow", "ComfyUI workflow",
            "game asset generation", "AI character", "AI creature",
            "game prop", "game weapon", "game armor",
            "tileable texture", "PBR texture", "normal map",
            # 3D资产生成
            "3D generation", "tripoSR", "tripo3d", "LRM",
            "meshy", "recraft 3D", "spline AI",
            "text-to-3D", "image-to-3D", "3D model generation",
            # 游戏动画/绑定
            "motion capture", "face capture", "performance capture",
            "character rigging", "skeletal animation",
            # 引擎集成
            "unreal engine 5", "UE5 ai", "unity ml-agents",
            "ue5 marketplace", "unreal marketplace asset",
        ],
        "important": [
            "stable diffusion", "midjourney", "dalle", "flux", "Leonardo AI",
            "LoRA game", "LoRA training", "checkpoint training",
            "ControlNet", "IP-Adapter", "C站助词",
            "DCC tool", "blender ai", "maya ai",
            "character design", "character concept art",
            "environment art", "environment design",
            "procedural texture", "procedural generation art",
            "AI illustration", "AI concept", "AI storyboard",
            # AI绘图工具
            "comfyui", "automatic1111", "forge webui", "sd webui",
            "invokeAI", " fooocus", "秋葉aaaki", "赛博nb",
            # LoRA相关
            "lora", "lycoris", "checkpoint", "vae", "embedding",
            "hypernetwork", "dreambooth", "training",
            # 游戏美术流程
            "game art pipeline", "asset pipeline", "美术工作流",
            "AI art generation", "generative art",
            "style transfer", "img2img", "图生图", "文生图",
        ],
        "general": [
            "texture", "3d", "3D", "asset", "game asset",
            "unreal engine", "unity", "blender", "maya", "houdini",
            "digital art", "digital painting", "matte painting",
            "sprite", "icon", "ui design", "游戏美术",
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
            "NPC behavior", "NPC AI", "enemy AI", "pathfinding",
            "behavior tree", "state machine", "utility AI",
            "game AI", "gameplay AI", "smart NPC",
            "conversation system", "dialogue tree", "branching narrative",
            "world building", "lore generation", "backstory generation",
            "character AI", "AI ally", "AI antagonist",
            "procedural quest", "dynamic event", "dynamic narrative",
            "story-driven", "choice system", "player agency",
            "game narrative", "interactive fiction", "visual novel",
            "AI storyteller", "AI writer", "AI editor",
            # 游戏策划工具
            "AI writing", "AI narrative", "AI storytelling",
            "procedural content generation", "PCG",
            "game prototyping", "design prototyping",
            # AI游戏相关
            "AI dungeon", "AI roguelike", "roguelike AI",
            "procedural narrative", "auto storytelling",
            "game jam AI", "Ludum Dare AI",
        ],
        "general": [
            "NPC", "quest", "dialogue", "story", "narrative",
            "gameplay", "game design", "level design",
            "游戏策划", "关卡设计", "剧情设计", "游戏玩法",
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
# 游戏开发者关注的来源权重更高
SOURCE_QUALITY_WEIGHT = {
    # AI 公司博客 - 权威来源
    "OpenAI Blog": 2.0,
    "Hugging Face Blog": 2.2,  # 提高（游戏+AI工作流丰富）
    "Stability AI Blog": 2.0,
    "Google DeepMind Blog": 2.0,
    "Cursor Blog": 2.5,  # Vibe Coding 核心来源
    "Anthropic Blog": 1.8,

    # 游戏开发社区 - 游戏开发者重点关注（权重2.5）
    "Game Developer": 2.5,
    "GDC Vault": 2.5,
    "80 Level": 2.5,
    "r/ComfyUI": 2.2,  # 游戏美术核心
    "r/StableDiffusion": 2.0,  # 游戏美术
    "r/LocalLLaMA": 1.8,  # LLM 本地部署
    "r/GameAI": 2.5,  # 游戏AI核心

    # Vibe Coding 来源 - 高权重
    "Windsurf Blog": 2.5,
    "GitHub Blog": 2.0,
    # 注: Cursor Blog RSS 已失效

    # 社区问答 - 实用技巧
    "AI Stack Exchange": 1.8,
    "Papers with Code": 1.5,  # 有代码的论文

    # 中文媒体 - 深度分析
    "机器之心": 2.0,  # 提高
    "量子位": 1.8,
    "少数派": 1.8,  # 工具使用技巧

    # 通用新闻源 - 降权（内容杂，权重0.5）
    "Hacker News AI": 0.5,
    "MIT Technology Review": 0.5,
    "The Verge AI": 0.5,
    "TechCrunch AI": 0.5,
    "Wired AI": 0.5,
    "ArXiv cs.AI": 0.3,
    "ArXiv cs.CV": 0.3,
    "ArXiv cs.LG": 0.3,
    "Import AI": 1.0,
    "Last Week in AI": 1.0,
    "The Batch": 1.0,

    # AI 工具资讯 - 中等权重
    "Product Hunt": 1.8,
    "There's an AI for That": 1.5,
    "Future Tools": 1.5,
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

    tag_scores = {}

    for tag in TAG_RULES.keys():
        score = _calculate_tag_score(tag, text_lower, title_lower)

        # 来源质量加权
        source_weight = SOURCE_QUALITY_WEIGHT.get(source_name, 1.0)

        # 学术来源降权
        if is_academic and tag == "AI前沿":
            source_weight *= 0.5
        # 实用来源加权
        elif source_name in PRACTICAL_SOURCES and tag in ["使用技巧", "工具推荐", "生产落地"]:
            source_weight *= 1.5

        score *= source_weight

        if score > 0:
            tag_scores[tag] = score

    # 学术内容强制添加生产落地标签检查（如果没匹配则降级）
    if is_academic and "生产落地" not in tag_scores:
        # 检查是否有生产落地相关关键词
        production_keywords = ["github", "code", "tutorial", "towards", "实战", "案例", "production"]
        if not any(kw in combined_lower for kw in production_keywords):
            # 纯学术内容降级处理
            pass  # 不做额外处理，让评审阶段过滤

    # 至少有2分以上才打标签
    MIN_SCORE = 2.0

    matched_tags = [tag for tag, score in tag_scores.items() if score >= MIN_SCORE]

    # 如果没有任何标签命中，但来源是AI专业源，默认打AI前沿
    if not matched_tags and source_name in [
        "OpenAI Blog", "Hugging Face Blog", "Stability AI Blog",
        "Google DeepMind Blog", "AI Stack Exchange", "ArXiv cs.AI",
        "ArXiv cs.CV", "ArXiv cs.LG", "机器之心", "量子位",
        "Import AI", "Last Week in AI", "The Batch",
    ]:
        matched_tags = ["AI前沿"]

    return sorted(matched_tags) if matched_tags else ["AI前沿"]
