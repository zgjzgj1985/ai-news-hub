"""评审Prompt管理 - 定义LLM评审标准和提示词"""

from typing import Dict, Any


# =============================================================================
# 来源分类
# =============================================================================

# 学术来源 - 需要严格评审，必须有代码或实战
ACADEMIC_SOURCES = [
    "ArXiv cs.AI",
    "ArXiv cs.CV (视觉)",
    "Papers with Code",
    "MIT Technology Review",
]

# 游戏开发重点来源 - 放宽评审标准
GAME_DEV_SOURCES = [
    "Game Developer",
    "GDC Vault",
    "80 Level",
    "r/ComfyUI",
    "r/GameAI",
    "Cursor Blog",
    "Windsurf Blog",
    "Hugging Face Blog",
    "机器之心",
    "少数派",
]

# Vibe Coding 重点来源
VIBE_CODING_SOURCES = [
    "Cursor Blog",
    "Hugging Face Blog",
    "r/LocalLLaMA",
    "Hacker News AI",
]

# =============================================================================
# 来源加权系数 - 高质量来源的文章自动加分
# =============================================================================

SOURCE_WEIGHT_BOOST = {
    # Vibe Coding 核心来源 +0.5
    "Cursor Blog": 0.5,
    "GitHub Blog": 0.5,
    "DEV.to Cursor": 0.5,
    "DEV.to AI Coding": 0.5,
    "Simon Willison": 0.5,
    # 高质量技术博客 +0.3
    "Hugging Face Blog": 0.3,
    "OpenAI Blog": 0.3,
    "Google DeepMind Blog": 0.3,
    # 开发者社区 +0.3
    "DEV.to LLM": 0.3,
    "DEV.to AI": 0.3,
    "GitHub Trending All": 0.3,
}

# 学术来源降权系数
SOURCE_WEIGHT_PENALTY = {
    "ArXiv cs.AI": -0.3,
    "ArXiv cs.CV (视觉)": -0.3,
    "ArXiv cs.LG": -0.3,
    "Papers with Code": -0.2,
    "MIT Technology Review": -0.2,
}


def get_source_weight_boost(source_name: str) -> float:
    """
    获取来源加权系数

    参数:
        source_name: 来源名称

    返回:
        float: 加权系数（正数加分，负数降分）
    """
    return SOURCE_WEIGHT_BOOST.get(source_name, 0.0)


def get_source_weight_penalty(source_name: str) -> float:
    """
    获取来源降权系数

    参数:
        source_name: 来源名称

    返回:
        float: 降权系数
    """
    return SOURCE_WEIGHT_PENALTY.get(source_name, 0.0)

# =============================================================================
# 系统提示词 - 游戏开发者专用评审标准
# =============================================================================

SYSTEM_PROMPT = """你是AI内容评审委员会，专注于推荐：
1. AI 编程工具和 Vibe Coding 最佳实践
2. 最新 AI 模型动态和实用工具
3. 开发者友好的 AI 应用案例

【评审维度 - 加权评分】

| 维度 | 权重 | 说明 |
|------|------|------|
| 实用性 | 2.5 | 是否有可直接使用的工具/代码/教程？ |
| AI相关度 | 1.5 | 与 AI 开发/编程的相关程度 |
| 受众价值 | 1.0 | 是否适合开发者阅读 |
| 技术深度 | 0.8 | 是否有实质性技术内容 |
| 新颖性 | 1.2 | 是否介绍新模型/工具/方法 |
| 生产价值 | 0.8 | 是否有可复用的代码/案例 |

【评分公式】
加权总分 = (实用性*2.5 + AI相关度*1.5 + 受众价值*1.0 + 技术深度*0.8 + 新颖性*1.2 + 生产价值*0.8) / 7.8

【评级标准】
- A级（强烈推荐）：加权>=6.5 且 实用性>=6
- B级（推荐）：加权>=5.0 且 实用性>=5
- C级（一般）：加权>=3.5
- D级（过滤）：仅过滤垃圾内容

【加分规则】
- Cursor/Windsurf/Copilot 使用技巧 → 实用性+1
- 有完整代码示例 → 生产价值+1
- 新模型发布（Deepseek/GPT/Claude）→ 新颖性+2
- 来自 Cursor Blog/GitHub Blog → 实用性+0.5

【降分规则】
- 纯新闻报道（无技术分析）→ 新颖性-1, 实用性-1
- 学术论文（无代码/无实战）→ 实用性-2
- 与AI/编程无关 → AI相关度-2

【输出格式 - 只输出JSON】
{
  "grade": "A/B/C/D",
  "scores": {
    "practicality": 数字,
    "game_relevance": 数字,
    "audience_value": 数字,
    "tech_depth": 数字,
    "novelty": 数字,
    "production_value": 数字
  },
  "verdict": "简短裁决（20字以内）"
}
"""

# =============================================================================
# 用户提示词模板
# =============================================================================

REVIEW_PROMPT_TEMPLATE = """【待评审内容】

标题：{title}
来源：{source}
摘要：{summary}

请严格按照评审标准进行评判，输出JSON格式结果。
"""

# =============================================================================
# 快速评审Prompt（用于批量处理）
# =============================================================================

QUICK_REVIEW_PROMPT = """判断以下内容是否值得推荐给AI工具开发者，只输出JSON：

标题：{title}
摘要：{summary}

JSON格式：
{{"worthy": true/false, "reason": "原因"}}
"""

# =============================================================================
# 批量评审Prompt
# =============================================================================

BATCH_REVIEW_PROMPT = """你是评审委员会，请评审以下多篇文章，每篇输出一个JSON：

{articles}

输出格式（JSON数组）：
[
  {{"index": 0, "grade": "A/B/C/D", "scores": {{...}}, "verdict": "..."}},
  ...
]
"""


# =============================================================================
# Prompt构建函数
# =============================================================================

def build_review_prompt(
    title: str,
    summary: str,
    source: str,
    include_system: bool = True
) -> Dict[str, str]:
    """
    构建评审提示词

    参数:
        title: 文章标题
        summary: 文章摘要/正文
        source: 来源名称
        include_system: 是否包含系统提示

    返回:
        Dict: 包含system和user消息的字典
    """
    user_content = REVIEW_PROMPT_TEMPLATE.format(
        title=title or "无标题",
        source=source or "未知来源",
        summary=summary or "无摘要"
    )

    if include_system:
        return {
            "system": SYSTEM_PROMPT,
            "user": user_content
        }
    else:
        return {
            "user": user_content
        }


def build_quick_review_prompt(title: str, summary: str) -> str:
    """
    构建快速评审提示词

    参数:
        title: 文章标题
        summary: 文章摘要

    返回:
        str: 格式化后的提示词
    """
    return QUICK_REVIEW_PROMPT.format(title=title, summary=summary)


def build_batch_review_prompt(articles: list) -> str:
    """
    构建批量评审提示词

    参数:
        articles: 文章列表，每项包含 title, summary, source

    返回:
        str: 格式化后的批量评审提示词
    """
    articles_text = "\n\n".join([
        f"【文章{i}】\n标题：{a.get('title', '无标题')}\n来源：{a.get('source', '未知')}\n摘要：{a.get('summary', '无')}"
        for i, a in enumerate(articles)
    ])

    return BATCH_REVIEW_PROMPT.format(articles=articles_text)


# =============================================================================
# 评分权重配置 - 游戏开发者专用
# =============================================================================

# 评审维度权重
SCORE_WEIGHTS = {
    "practicality": 2.5,       # 实用性 - 最重要
    "game_relevance": 1.5,     # 游戏相关度 - 新增
    "audience_value": 1.0,     # 目标受众 - 降低权重
    "novelty": 1.2,           # 新颖性 - AI模型动态优先
    "tech_depth": 0.8,         # 技术深度
    "production_value": 0.8,   # 生产价值
}

# 加权总分满分
MAX_WEIGHTED_SCORE = sum(SCORE_WEIGHTS.values())  # 7.8


# =============================================================================
# 结果解析函数
# =============================================================================

def parse_review_result(raw_response: str) -> Dict[str, Any]:
    """
    解析LLM评审结果

    参数:
        raw_response: LLM原始响应

    返回:
        Dict: 解析后的评审结果，包含默认值防止解析失败
    """
    import json
    import re

    # 默认值 - 偏向游戏开发者实用性
    default_result = {
        "grade": "B",  # 默认给B级，不要默认给C
        "scores": {
            "practicality": 6,   # 默认提高实用性分数
            "game_relevance": 5, # 默认游戏相关度
            "audience_value": 5,
            "tech_depth": 5,
            "novelty": 6,       # 默认提高新颖性分数
            "production_value": 5
        },
        "weighted_score": 5.5,
        "verdict": "评审结果解析完成",
        "strengths": [],
        "weaknesses": [],
        "recommendation": "内容可推荐",
        "raw_response": raw_response[:500]
    }

    # 尝试直接解析
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    # 尝试提取markdown代码块
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_response)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # 尝试提取花括号包裹的JSON
    brace_match = re.search(r'\{[\s\S]*\}', raw_response)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return default_result


def calculate_weighted_score(scores: Dict[str, float]) -> float:
    """
    计算加权评审总分

    参数:
        scores: 各维度分数

    返回:
        float: 加权总分（满分约6.3）
    """
    weighted_sum = 0.0
    for dimension, weight in SCORE_WEIGHTS.items():
        score = scores.get(dimension, 5.0)  # 默认5分
        weighted_sum += score * weight

    return round(weighted_sum / MAX_WEIGHTED_SCORE, 2)


def calculate_total_score(scores: Dict[str, float]) -> float:
    """
    计算评审总分（兼容旧接口）

    参数:
        scores: 各维度分数

    返回:
        float: 总分
    """
    return calculate_weighted_score(scores)


def grade_from_scores(scores: Dict[str, float]) -> str:
    """
    根据加权分数确定评级（与 SYSTEM_PROMPT 中的阈值保持一致）

    参数:
        scores: 各维度分数

    返回:
        str: 评级 A/B/C/D
    """
    weighted = calculate_weighted_score(scores)
    practicality = scores.get("practicality", 5)

    # 与 SYSTEM_PROMPT 中的阈值保持一致（第120-123行）
    if weighted >= 6.5 and practicality >= 6:
        return "A"
    elif weighted >= 5.0 and practicality >= 5:
        return "B"
    elif weighted >= 3.5:  # 删除 game_relevance 条件，与 prompt 一致
        return "C"
    else:
        return "D"
