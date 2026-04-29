"""APScheduler-based task scheduler for periodic feed fetching."""

import logging
import os
from datetime import datetime
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def _log(level, msg, *args):
    try:
        logger.log(level, msg, *args)
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

scheduler = BackgroundScheduler()


def fetch_job():
    from scraper.rss_parser import fetch_all_feeds
    _log(logging.INFO, "[Scheduler] Starting scheduled feed fetch at %s", datetime.utcnow())
    try:
        result = fetch_all_feeds()
        _log(logging.INFO, "[Scheduler] Feed fetch complete: %s", result)
    except Exception as e:
        _log(logging.ERROR, "[Scheduler] Feed fetch failed: %s", str(e))


def deep_review_job():
    """后台深度评审：抓取文章正文后让 LLM 阅读理解并评分。"""
    _log(logging.INFO, "[DeepReview] Starting deep review job at %s", datetime.utcnow())
    try:
        from scraper.deep_reviewer import run_deep_review_sync
        result = run_deep_review_sync(limit=20, delay=1.5)
        _log(logging.INFO, "[DeepReview] Deep review completed: %s", result)
    except Exception as e:
        _log(logging.ERROR, "[DeepReview] Deep review failed: %s", str(e))


def review_backlog_job():
    """兜底评审：仅基于 RSS 摘要评分（正文抓取失败时使用）。"""
    _log(logging.INFO, "[ReviewBacklog] Starting backlog review at %s", datetime.utcnow())
    try:
        # 在新线程中运行异步评审任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_review_backlog_async())
        finally:
            loop.close()
    except Exception as e:
        _log(logging.ERROR, "[ReviewBacklog] Backlog review failed: %s", str(e))


def translate_backlog_job():
    """后台批量翻译未翻译的历史文章摘要"""
    _log(logging.INFO, "[TranslateBacklog] Starting backlog translation at %s", datetime.utcnow())
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_translate_backlog_async())
        finally:
            loop.close()
    except Exception as e:
        _log(logging.ERROR, "[TranslateBacklog] Backlog translation failed: %s", str(e))


async def _translate_backlog_async(limit: int = 30):
    """异步批量翻译任务"""
    from database import Article, SessionLocal
    from scraper.translator import CHINESE_SOURCES, detect_language, translate_text, save_translation

    db = SessionLocal()
    try:
        # 获取未翻译的文章（排除中文来源）
        articles = (
            db.query(Article)
            .filter(
                Article.is_translated == False,
                Article.summary != None,
                Article.summary != ""
            )
            .filter(~Article.source_name.in_(CHINESE_SOURCES))
            .limit(limit)
            .all()
        )

        if not articles:
            _log(logging.INFO, "[TranslateBacklog] No pending articles to translate")
            return

        success_count = 0
        for article in articles:
            try:
                text = article.summary
                if not text:
                    continue

                # 检测语言
                lang = detect_language(text)
                if lang == "zh":
                    # 已经是中文，标记为已翻译
                    article.summary_zh = text
                    article.is_translated = True
                    article.translated_at = datetime.utcnow()
                    db.commit()
                    success_count += 1
                    continue

                # 执行翻译
                translated = await translate_text(text)
                if translated:
                    save_translation(article.id, translated)
                    success_count += 1
                    _log(logging.INFO, "[TranslateBacklog] Translated article %d", article.id)
                else:
                    _log(logging.WARNING, "[TranslateBacklog] Failed to translate article %d", article.id)

            except Exception as e:
                db.rollback()
                _log(logging.ERROR, "[TranslateBacklog] Failed to translate article %d: %s", article.id, str(e))

        _log(logging.INFO, "[TranslateBacklog] Completed: %d/%d articles translated", success_count, len(articles))

    finally:
        db.close()


async def _review_backlog_async(limit: int = 50):
    """异步批量评审任务"""
    from database import Article, SessionLocal
    from llm_client import get_llm_client
    from prompts import build_review_prompt, parse_review_result, calculate_total_score, grade_from_scores

    llm_client = get_llm_client()
    if not llm_client.is_available():
        _log(logging.WARNING, "[ReviewBacklog] LLM not available, skipping")
        return

    db = SessionLocal()
    try:
        articles = db.query(Article).filter(
            Article.review_grade.is_(None)
        ).limit(limit).all()

        if not articles:
            _log(logging.INFO, "[ReviewBacklog] No pending articles to review")
            return

        success_count = 0
        for article in articles:
            try:
                prompts = build_review_prompt(
                    article.title,
                    article.summary or "",
                    article.source_name
                )

                messages = [
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ]

                response = await llm_client.chat(messages, json_mode=True)
                parsed = parse_review_result(response)

                if parsed:
                    scores = parsed.get("scores", {})
                    total_score = calculate_total_score(scores)
                    grade = parsed.get("grade") or grade_from_scores(scores)

                    article.review_grade = grade
                    article.review_score = int(total_score)
                    article.review_result = parsed
                    article.review_verdict = parsed.get("verdict", "")
                    article.reviewed_at = datetime.utcnow()

                    db.commit()
                    success_count += 1
                else:
                    _log(logging.WARNING, "[ReviewBacklog] Failed to parse LLM response for article %d", article.id)

            except Exception as e:
                db.rollback()
                _log(logging.ERROR, "[ReviewBacklog] Failed to review article %d: %s", article.id, str(e))

        _log(logging.INFO, "[ReviewBacklog] Completed: %d/%d articles reviewed", success_count, len(articles))

    finally:
        db.close()


def init_scheduler():
    hour = int(os.getenv("SCHEDULE_HOUR", "9"))
    minute = int(os.getenv("SCHEDULE_MINUTE", "30"))

    scheduler.add_job(
        fetch_job,
        CronTrigger(hour=hour, minute=minute),
        id="daily_fetch",
        name="Daily RSS Feed Fetch",
        replace_existing=True,
    )

    # 深度评审后台任务（每30分钟处理20篇，抓取正文后 LLM 评分）
    # 优先级：先处理 deep_review_done=False 的文章
    scheduler.add_job(
        deep_review_job,
        IntervalTrigger(minutes=30),
        id="deep_review",
        name="Deep Review Articles (Fetch Body + LLM)",
        replace_existing=True,
    )

    # 翻译后台任务（每45分钟翻译30篇）
    scheduler.add_job(
        translate_backlog_job,
        IntervalTrigger(minutes=45),
        id="translate_backlog",
        name="Translate Backlog Articles",
        replace_existing=True,
    )

    scheduler.start()
    _log(logging.INFO, "[Scheduler] Started. Next fetch at %02d:%02d", hour, minute)
    return scheduler


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        _log(logging.INFO, "[Scheduler] Shut down.")
