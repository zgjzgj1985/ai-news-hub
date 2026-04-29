"""评审Prompt管理模块"""

from .review_prompts import (
    SYSTEM_PROMPT,
    REVIEW_PROMPT_TEMPLATE,
    build_review_prompt,
    build_quick_review_prompt,
    build_batch_review_prompt,
    parse_review_result,
    calculate_total_score,
    grade_from_scores,
    get_source_weight_boost,
    SOURCE_WEIGHT_BOOST,
    SOURCE_WEIGHT_PENALTY,
)

__all__ = [
    "SYSTEM_PROMPT",
    "REVIEW_PROMPT_TEMPLATE",
    "build_review_prompt",
    "build_quick_review_prompt",
    "build_batch_review_prompt",
    "parse_review_result",
    "calculate_total_score",
    "grade_from_scores",
    "get_source_weight_boost",
    "SOURCE_WEIGHT_BOOST",
    "SOURCE_WEIGHT_PENALTY",
]
