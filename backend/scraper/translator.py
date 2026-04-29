"""翻译服务 - 使用本地 LLM 将英文翻译为中文"""

import logging
from datetime import datetime
from typing import Optional

from database import Article, SessionLocal
from llm_client import get_llm_client

logger = logging.getLogger(__name__)

# 中文 AI 媒体来源 - 这些来源的文章已经是中文，不需要翻译
CHINESE_SOURCES = [
    "机器之心",
    "量子位",
    "36氪",
    "雷锋网",
    "爱范儿",
    "少数派",
    "InfoQ",
]

# 需要翻译的语言（识别到这些语言时进行翻译）
TRANSLATABLE_LANGUAGES = ["en", "english", "英文", "English"]


def is_chinese_source(source_name: str) -> bool:
    """判断来源是否是中文媒体"""
    return source_name in CHINESE_SOURCES


def detect_language(text: str) -> str:
    """
    简单语言检测 - 基于常见中文字符占比

    返回: 'zh' 表示中文，'en' 表示英文或其他
    """
    if not text:
        return "en"

    # 计算中文字符占比
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text.strip())

    if total_chars == 0:
        return "en"

    chinese_ratio = chinese_chars / total_chars

    # 如果中文字符占比超过 30%，认为是中文内容
    if chinese_ratio > 0.3:
        return "zh"

    return "en"


TRANSLATION_PROMPT = """将以下英文翻译为简体中文（简洁准确）：

{text}

中文："""


async def translate_text(text: str, max_length: int = 2000) -> Optional[str]:
    """
    使用 LLM 翻译文本为中文

    参数:
        text: 需要翻译的文本
        max_length: 最大输入长度

    返回:
        翻译后的中文文本，失败返回 None
    """
    if not text or not text.strip():
        return None

    # 检测语言，如果已经是中文则不翻译
    lang = detect_language(text)
    if lang == "zh":
        return text

    try:
        client = get_llm_client()

        if not client.is_available():
            logger.warning("LLM 服务不可用，无法翻译")
            return None

        # 截断过长的文本
        input_text = text.strip()[:max_length]

        prompt = TRANSLATION_PROMPT.format(text=input_text)
        result = await client.generate(
            prompt=prompt,
            system="你是一个专业的技术文章翻译助手。",
            temperature=0.1,
            json_mode=False
        )

        # 清理翻译结果
        translated = result.strip()

        # 移除可能的引号包裹
        if translated.startswith('"') and translated.endswith('"'):
            translated = translated[1:-1]
        if translated.startswith("'") and translated.endswith("'"):
            translated = translated[1:-1]

        return translated if translated else None

    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return None


async def translate_title(title: str) -> Optional[str]:
    """
    翻译文章标题为中文

    参数:
        title: 需要翻译的英文标题

    返回:
        翻译后的中文标题，失败返回 None
    """
    if not title or not title.strip():
        return None

    # 检测语言，如果已经是中文则不翻译
    lang = detect_language(title)
    if lang == "zh":
        return title

    try:
        client = get_llm_client()

        if not client.is_available():
            logger.warning("LLM 服务不可用，无法翻译标题")
            return None

        # 标题翻译提示 - 强调简洁
        prompt = f"翻译为中文（简洁）：{title.strip()}\n中文："

        result = await client.generate(
            prompt=prompt,
            system="你是一个专业的技术文章翻译助手，擅长翻译英文标题为简洁的中文。",
            temperature=0.1,
            json_mode=False
        )

        # 清理翻译结果
        translated = result.strip()

        # 移除可能的引号包裹
        if translated.startswith('"') and translated.endswith('"'):
            translated = translated[1:-1]
        if translated.startswith("'") and translated.endswith("'"):
            translated = translated[1:-1]

        return translated if translated else None

    except Exception as e:
        logger.error(f"标题翻译失败: {e}")
        return None


def translate_article(article_id: int) -> bool:
    """
    翻译单篇文章的摘要（同步版本）

    参数:
        article_id: 文章 ID

    返回:
        翻译是否成功
    """
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return False

        # 中文来源不需要翻译
        if is_chinese_source(article.source_name):
            article.is_translated = True
            article.summary_zh = article.summary
            article.translated_at = datetime.utcnow()
            db.commit()
            return True

        # 如果没有摘要，跳过
        if not article.summary:
            return False

        # 如果已经翻译过，跳过
        if article.is_translated and article.summary_zh:
            return True

        return False  # 需要异步调用翻译

    finally:
        db.close()


def save_translation(article_id: int, translated_summary: str, translated_title: str = None) -> bool:
    """
    保存翻译结果到数据库

    参数:
        article_id: 文章 ID
        translated_summary: 翻译后的摘要
        translated_title: 翻译后的标题（可选）

    返回:
        保存是否成功
    """
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return False

        article.summary_zh = translated_summary
        if translated_title:
            article.title_zh = translated_title
        article.is_translated = True
        article.translated_at = datetime.utcnow()
        db.commit()
        return True

    except Exception as e:
        logger.error(f"保存翻译失败: {e}")
        db.rollback()
        return False

    finally:
        db.close()


def get_untranslated_articles(limit: int = 50) -> list:
    """
    获取未翻译的文章列表

    参数:
        limit: 最大返回数量

    返回:
        未翻译的文章列表
    """
    db = SessionLocal()
    try:
        # 获取没有翻译过的英文文章
        from sqlalchemy import not_
        articles = (
            db.query(Article)
            .filter(
                Article.is_translated == False,
                Article.summary != None,
                Article.summary != "",
                not_(Article.source_name.in_(CHINESE_SOURCES))
            )
            .limit(limit)
            .all()
        )
        return articles

    finally:
        db.close()


def batch_translate(article_ids: list[int]) -> dict:
    """
    批量翻译文章（标题 + 摘要）

    参数:
        article_ids: 文章 ID 列表

    返回:
        翻译结果统计
    """
    import asyncio

    results = {
        "total": len(article_ids),
        "success": 0,
        "failed": 0,
        "skipped": 0,
    }

    async def translate_one(article_id: int):
        db = SessionLocal()
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                return "failed"

            # 中文来源或已有翻译
            if is_chinese_source(article.source_name) or article.is_translated:
                results["skipped"] += 1
                return "skipped"

            translated_summary = None
            translated_title = None

            # 翻译摘要
            if article.summary:
                translated_summary = await translate_text(article.summary)

            # 翻译标题
            if article.title:
                translated_title = await translate_title(article.title)

            # 只要翻译了摘要或标题就保存
            if translated_summary or translated_title:
                article.summary_zh = translated_summary
                if translated_title:
                    article.title_zh = translated_title
                article.is_translated = True
                article.translated_at = datetime.utcnow()
                db.commit()
                results["success"] += 1
                return "success"
            else:
                results["failed"] += 1
                return "failed"

        except Exception as e:
            logger.error(f"翻译文章 {article_id} 失败: {e}")
            db.rollback()
            results["failed"] += 1
            return "failed"

        finally:
            db.close()

    async def run_all():
        tasks = [translate_one(aid) for aid in article_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run(run_all())
    return results
