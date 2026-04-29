"""
深度评审模块 - 抓取文章正文后让 LLM 阅读理解并评分

设计思路：
1. 后台持续运行：scheduler 每30分钟调用一次
2. 抓取正文：提取文章完整内容（不限长度，LLM 自动截断）
3. LLM 评分：阅读理解后给出6维度评分和综合评级
4. 仅后台存储：评分不暴露给前端，前端只显示 A/B/C/D 徽章
5. 过滤逻辑：只有 deep_review_done=True 的文章才进入推荐列表
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from database import Article, SessionLocal
from llm_client import get_llm_client
from prompts import (
    build_review_prompt,
    parse_review_result,
    calculate_total_score,
    grade_from_scores,
    get_source_weight_boost,
)

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 8
FETCH_TIMEOUT = 15
BODY_TIMEOUT = (CONNECT_TIMEOUT, FETCH_TIMEOUT)


def _safe_log(level, msg, *args):
    try:
        logger.log(level, msg, *args)
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass


def fetch_article_body(url: str, timeout: tuple = BODY_TIMEOUT) -> str:
    """
    抓取文章的完整正文内容。

    提取策略：
    1. 优先提取 <article> 标签内的所有段落
    2. 回退到 <main> 标签
    3. 再回退到含 class="content/post/body/entry" 的 div
    4. 最后使用最大文本块 heuristics

    返回：
        提取的文章正文（可能很长，LLM 会自动截断）
        失败时返回空字符串
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "lxml")

        # 移除 script、style、nav、footer、header、aside 等无关标签
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "noscript", "iframe", "svg"]):
            tag.decompose()

        text = ""

        # 策略1：<article> 标签
        article_tag = soup.find("article")
        if article_tag:
            paragraphs = article_tag.find_all("p")
            if paragraphs:
                text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # 策略2：<main> 标签
        if not text:
            main_tag = soup.find("main")
            if main_tag:
                paragraphs = main_tag.find_all("p")
                if paragraphs:
                    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # 策略3：content/post/body/entry 相关 class
        if not text:
            for cls in ["content", "post-content", "article-content",
                        "entry-content", "post-body", "article-body"]:
                content_div = soup.find("div", class_=lambda x: x and cls in x.lower() if x else False)
                if content_div:
                    paragraphs = content_div.find_all("p")
                    if paragraphs:
                        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        if text:
                            break

        # 策略4：最大文本块 heuristics
        if not text:
            # 找包含最多段落的 div
            best_div = None
            best_para_count = 0
            for div in soup.find_all("div"):
                div_paras = div.find_all("p")
                if len(div_paras) > best_para_count:
                    # 过滤掉导航类 div
                    parent_class = " ".join(
                        (div.get("class") or []) +
                        (div.get("id") or [])
                    ).lower()
                    if not any(n in parent_class for n in ["nav", "menu", "sidebar", "comment", "footer", "header"]):
                        best_para_count = len(div_paras)
                        best_div = div
            if best_div:
                paragraphs = best_div.find_all("p")
                text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # 清理：移除多余空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        _safe_log(logging.INFO, "Fetched article body: %d chars", len(text))
        return text.strip()

    except Exception as e:
        _safe_log(logging.WARNING, "Failed to fetch article body for %s: %s", url[:60], str(e))
        return ""


def fetch_youtube_transcript(url: str) -> str:
    """尝试从 YouTube 视频获取字幕（如果有的话）。"""
    # YouTube 字幕获取需要 yt-dlp 或 youtube-transcript-api
    # 这里做一个简单检测，如果 URL 是 youtube.com 或 youtu.be，返回空
    # 实际使用时可接入 youtube-transcript-api
    if "youtube.com" in url or "youtu.be" in url:
        _safe_log(logging.INFO, "YouTube URL detected, skipping transcript: %s", url[:60])
        return ""
    return ""


async def deep_review_single_article(article: Article, llm_client) -> dict:
    """
    对单篇文章进行深度评审。

    流程：
    1. 抓取文章正文（fetch_article_body）
    2. 构建评审提示词（将正文作为 context 传入）
    3. 调用 LLM 评分
    4. 应用来源加权
    5. 返回评审结果

    返回：
        dict: 包含 success, grade, score, verdict, error 等字段
    """
    try:
        # Step 1: 抓取正文
        body = fetch_article_body(article.url)
        if not body:
            # 正文抓取失败时，使用 YouTube 字幕作为备选
            body = fetch_youtube_transcript(article.url)

        # 如果正文为空且没有摘要，跳过
        combined_text = body if body else (article.summary or "")
        if not combined_text.strip():
            return {
                "success": False,
                "error": "No content to review (no body, no summary)",
            }

        # Step 2: 构建提示词（正文 + 摘要一起给 LLM）
        review_text = combined_text
        # 限制正文长度，避免 token 爆炸（LLM 本身也会截断，但提前裁剪节省资源）
        if len(review_text) > 8000:
            review_text = review_text[:8000]

        prompts = build_review_prompt(
            title=article.title,
            summary=review_text,
            source=article.source_name,
        )

        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ]

        # Step 3: 调用 LLM
        response = await llm_client.chat(messages, json_mode=True)
        parsed = parse_review_result(response)

        if not parsed or "scores" not in parsed:
            return {
                "success": False,
                "error": f"Failed to parse LLM response: {response[:200]}",
            }

        scores = parsed.get("scores", {})

        # Step 4: 计算加权分
        total_score = calculate_total_score(scores)

        # Step 5: 应用来源加权
        source_boost = get_source_weight_boost(article.source_name)
        boosted_total = total_score + source_boost

        # 根据来源调整 practicality 分数（用于评级判断）
        boosted_scores = scores.copy()
        if source_boost != 0:
            boosted_scores["practicality"] = min(
                10, scores.get("practicality", 5) + source_boost
            )

        # Step 6: 重新计算评级
        grade = parsed.get("grade") or grade_from_scores(boosted_scores)

        return {
            "success": True,
            "grade": grade,
            "score": int(total_score * 10),  # 0-78 -> 0-780 (存储为整数)
            "scores": scores,
            "verdict": parsed.get("verdict", ""),
            "raw_response": response[:500],
            "body_length": len(combined_text),
            "used_body": bool(body),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def batch_deep_review(limit: int = 30, delay: float = 1.0) -> dict:
    """
    批量深度评审：优先处理未完成深度评审的文章。

    优先级排序：
    1. 先处理 deep_review_done=False 的文章（从未评审过的）
    2. 在这些文章中，按发布时间倒序（越新越优先）

    参数：
        limit: 每次最多处理多少篇
        delay: 每篇之间等待秒数（避免请求过快）

    返回：
        dict: 包含 success_count, fail_count, skip_count, grade_stats 等统计
    """
    _safe_log(logging.INFO, "[DeepReview] Starting batch deep review (limit=%d)", limit)

    llm_client = get_llm_client()
    if not llm_client.is_available():
        _safe_log(logging.ERROR, "[DeepReview] LLM not available, skipping")
        return {"success_count": 0, "fail_count": 0, "skip_count": 0, "error": "LLM not available"}

    db = SessionLocal()
    try:
        # 优先获取从未做过深度评审的文章
        articles = (
            db.query(Article)
            .filter(Article.deep_review_done == False)
            .order_by(Article.published_at.desc().nullslast())
            .limit(limit)
            .all()
        )

        if not articles:
            _safe_log(logging.INFO, "[DeepReview] No pending articles for deep review")
            return {"success_count": 0, "fail_count": 0, "skip_count": 0}

        _safe_log(logging.INFO, "[DeepReview] Found %d articles to deep review", len(articles))

        success_count = 0
        fail_count = 0
        skip_count = 0
        grade_stats = {"A": 0, "B": 0, "C": 0, "D": 0}

        start_time = time.time()

        for i, article in enumerate(articles, 1):
            _safe_log(logging.INFO,
                "[DeepReview] [%d/%d] Processing: %s",
                i, len(articles), article.title[:50]
            )

            result = await deep_review_single_article(article, llm_client)

            if result["success"]:
                # 保存评审结果
                article.review_grade = result["grade"]
                article.review_score = result["score"]
                article.review_result = {
                    "scores": result["scores"],
                    "verdict": result["verdict"],
                    "raw_response": result.get("raw_response", ""),
                    "body_length": result.get("body_length", 0),
                    "used_body": result.get("used_body", False),
                    "review_type": "deep",  # 标记为深度评审
                    "reviewed_at": datetime.utcnow().isoformat(),
                }
                article.review_verdict = result["verdict"]
                article.reviewed_at = datetime.utcnow()
                article.deep_review_done = True
                article.deep_review_body = result.get("body_length", 0) > 0

                db.commit()
                success_count += 1
                if result["grade"] in grade_stats:
                    grade_stats[result["grade"]] += 1

                _safe_log(logging.INFO,
                    "[DeepReview]   -> Grade: %s | Scores: %s",
                    result["grade"],
                    {k: v for k, v in result["scores"].items()}
                )
            else:
                db.rollback()
                fail_count += 1
                _safe_log(logging.WARNING,
                    "[DeepReview]   -> FAILED: %s", result.get("error", "Unknown error")
                )

            # 速率控制
            if i < len(articles):
                await asyncio.sleep(delay)

        elapsed = time.time() - start_time
        _safe_log(logging.INFO,
            "[DeepReview] Completed: %d success, %d failed, %d skip | "
            "Grades: %s | Elapsed: %.1fs",
            success_count, fail_count, skip_count, grade_stats, elapsed
        )

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "skip_count": skip_count,
            "grade_stats": grade_stats,
            "elapsed": elapsed,
        }

    finally:
        db.close()


def run_deep_review_sync(limit: int = 30, delay: float = 1.0) -> dict:
    """
    同步入口：供 scheduler 调用（在后台线程中运行异步代码）。
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(batch_deep_review(limit, delay))
    finally:
        loop.close()
