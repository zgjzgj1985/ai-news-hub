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
    "r/StableDiffusion",
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
# 系统提示词 - 游戏开发者专用评审标准
# =============================================================================

SYSTEM_PROMPT = """你是一个专为游戏开发者服务的AI内容评审委员会，专注于推荐：
1. AI + 游戏设计/工作流
2. 最新 AI 模型动态 (Deepseek V4、GPT-5 等)
3. Vibe Coding 最佳实践
4. 实用的 AI 工具/工作流

【评审身份 - 5位专家】
1. 游戏美术总监：评估AI绘图、资产生成、工作流
2. 游戏策划主管：评估AI NPC、程序化生成、对话系统
3. 技术美术：评估技术落地可行性、引擎集成
4. 工具猎手：评估AI编程工具、Vibe Coding体验
5. 质量守门员：确保内容实用、不过时

【核心评审标准 - 加权评分】

1. 实用性 (practicality)：0-10分，权重2.5 【最重要】
   - 是否有可直接用于游戏项目的工具/工作流？
   - 是否有可操作的教程、Prompt、LoRA？
   - 是否有完整的工作流示例（ComfyUI、SD等）？
   - 能否帮助解决游戏开发中的实际问题？

2. 游戏相关度 (game_relevance)：0-10分，权重1.5 【新增维度】
   - 是否与游戏开发直接相关？
   - AI游戏美术（资产生成、LoRA、ComfyUI工作流）→ +2分
   - AI游戏策划（NPC、对话、程序化生成）→ +2分
   - Vibe Coding / AI辅助编程 → +1分
   - 通用AI新闻（非游戏）→ -2分

3. 目标受众 (audience_value)：0-10分，权重1.0 【降低权重】
   - 是否适合游戏开发者（美术/策划/程序）？
   - 游戏相关内容加2分

4. 技术深度 (tech_depth)：0-10分，权重0.8
   - 是否有实质性技术内容？
   - 允许有深度的游戏AI设计分析

5. 新颖性 (novelty)：0-10分，权重1.2
   - 是否介绍新模型/新工具/新方法？
   - Deepseek、Qwen、GPT-5等新模型发布加2分
   - 新游戏AI技术/工具加1分

6. 生产价值 (production_value)：0-10分，权重0.8
   - 是否有真实项目案例？
   - 是否有可复用的代码/资源？

【特别规则 - 游戏开发者优先】

【A】游戏内容加分规则：
   - AI + 游戏美术（资产生成、LoRA、ComfyUI工作流）→ game_relevance加2分
   - AI + 游戏策划（NPC、对话、程序化生成）→ game_relevance加2分
   - 有完整工作流截图/视频 → practicality加1分

【B】AI模型动态优先规则：
   - Deepseek V4/V3、GPT-5、Claude 4等新模型发布 → novelty加2分
   - 有实际测试/对比 → novelty加1分
   - 只要不是纯新闻报道，都应该给到B级以上

【C】Vibe Coding 加分规则：
   - Cursor、Windsurf、Copilot使用技巧 → practicality加1分
   - 有实际项目案例 → production_value加1分
   - AI辅助编程最佳实践 → practicality加2分

【D】新闻报道宽容规则：
   - 来自权威来源（机器之心、Hugging Face官方博客）→ 至少给B级
   - 包含技术分析不是纯新闻 → 至少给B级
   - 只有标题没有内容 → 降到C级

【E】通用AI内容降级规则：【新增】
   - 非游戏相关的模型发布/新闻 → audience_value降1分，game_relevance降2分
   - 纯新闻报道（无技术分析/无实际应用）→ novelty降1分，practicality降1分
   - 学术论文（无代码/无实战案例）→ practicality降2分，production_value降1分

【评级标准 - 加权平均】（游戏开发者优先版）
加权总分 = (practicality*2.5 + game_relevance*1.5 + audience_value*1.0 + novelty*1.2 + tech_depth*0.8 + production_value*0.8) / 7.8

- A级（强烈推荐）：加权总分>=6.5，且practicality>=6
- B级（推荐）：加权总分>=5.0，且practicality>=5
- C级（一般）：加权总分>=3.5（降低阈值，让更多内容通过）
- D级（过滤）：仅过滤明显垃圾内容

【放宽后的过滤标准 - 只过滤以下情况】
仅以下情况才给D级：
- 纯广告/推广内容
- 明显无效链接/资源已失效
- 与AI和游戏开发完全无关（如纯币圈、纯股票预测）
- 过时超过6个月的技术内容

【输出格式 - 必须JSON】
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
  "weighted_score": 数字,
  "verdict": "简短裁决理由（20字以内）",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["劣势1", "劣势2"],
  "recommendation": "是否推荐及理由（50字以内）"
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
    根据加权分数确定评级

    参数:
        scores: 各维度分数

    返回:
        str: 评级 A/B/C/D
    """
    weighted = calculate_weighted_score(scores)
    practicality = scores.get("practicality", 5)
    game_relevance = scores.get("game_relevance", 5)

    if weighted >= 7.0 and practicality >= 6:
        return "A"
    elif weighted >= 5.5 and practicality >= 5:
        return "B"
    elif weighted >= 4 and game_relevance >= 4:
        return "C"
    else:
        return "D"
