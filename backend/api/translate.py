"""翻译 API 端点"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Article, SessionLocal
from scraper.translator import (
    CHINESE_SOURCES,
    batch_translate,
    detect_language,
    get_untranslated_articles,
    is_chinese_source,
    save_translation,
    translate_text,
    translate_title,
)

router = APIRouter(prefix="/api/translate", tags=["translate"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TranslateRequest(BaseModel):
    text: str


class TranslateResponse(BaseModel):
    original: str
    translated: Optional[str]
    language: str
    success: bool
    error: Optional[str] = None


class BatchTranslateRequest(BaseModel):
    article_ids: list[int]


class BatchTranslateResponse(BaseModel):
    total: int
    success: int
    failed: int
    skipped: int


class TranslateStatsResponse(BaseModel):
    total_articles: int
    translated_articles: int
    untranslated_articles: int
    chinese_sources: int
    english_articles: int


@router.post("", response_model=TranslateResponse)
async def translate_single_text(request: TranslateRequest):
    """
    翻译单段文本

    - **text**: 需要翻译的文本
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    language = detect_language(request.text)

    # 如果已经是中文，直接返回
    if language == "zh":
        return TranslateResponse(
            original=request.text,
            translated=request.text,
            language="zh",
            success=True,
        )

    translated = await translate_text(request.text)

    if translated:
        return TranslateResponse(
            original=request.text,
            translated=translated,
            language=language,
            success=True,
        )
    else:
        return TranslateResponse(
            original=request.text,
            translated=None,
            language=language,
            success=False,
            error="翻译服务不可用或翻译失败",
        )


@router.post("/article/{article_id}", response_model=TranslateResponse)
async def translate_article(article_id: int, db: Session = Depends(get_db)):
    """
    翻译指定文章的摘要

    - **article_id**: 文章 ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 如果是中文来源或已翻译
    if is_chinese_source(article.source_name):
        return TranslateResponse(
            original=article.summary or "",
            translated=article.summary or "",
            language="zh",
            success=True,
        )

    if article.is_translated and article.summary_zh:
        return TranslateResponse(
            original=article.summary or "",
            translated=article.summary_zh,
            language="en",
            success=True,
        )

    if not article.summary:
        raise HTTPException(status_code=400, detail="文章没有摘要可翻译")

    # 执行翻译
    translated = await translate_text(article.summary)

    if translated:
        # 保存翻译结果
        save_translation(article_id, translated)
        return TranslateResponse(
            original=article.summary,
            translated=translated,
            language="en",
            success=True,
        )
    else:
        return TranslateResponse(
            original=article.summary,
            translated=None,
            language="en",
            success=False,
            error="翻译服务不可用或翻译失败",
        )


@router.post("/batch", response_model=BatchTranslateResponse)
async def batch_translate_articles(request: BatchTranslateRequest, background_tasks: BackgroundTasks):
    """
    批量翻译文章

    - **article_ids**: 文章 ID 列表（最多 100 个）
    """
    if len(request.article_ids) > 100:
        raise HTTPException(status_code=400, detail="一次最多翻译 100 篇文章")

    if len(request.article_ids) == 0:
        raise HTTPException(status_code=400, detail="文章 ID 列表不能为空")

    # 在后台执行批量翻译
    background_tasks.add_task(batch_translate, request.article_ids)

    return BatchTranslateResponse(
        total=len(request.article_ids),
        success=0,
        failed=0,
        skipped=0,
    )


@router.post("/all", response_model=dict)
async def translate_all_articles(
    limit: int = Query(50, ge=1, le=200, description="每次翻译的文章数量"),
    background_tasks: BackgroundTasks = None,
):
    """
    翻译所有未翻译的文章

    - **limit**: 每次翻译的文章数量上限
    """
    db = SessionLocal()
    try:
        # 获取未翻译的文章
        articles = (
            db.query(Article)
            .filter(
                Article.is_translated == False,
                Article.summary != None,
                Article.summary != "",
            )
            .limit(limit)
            .all()
        )

        # 过滤掉中文来源
        article_ids = [
            a.id for a in articles
            if not is_chinese_source(a.source_name)
        ]

        return {
            "total": len(articles),
            "to_translate": len(article_ids),
            "skipped_chinese": len(articles) - len(article_ids),
        }

    finally:
        db.close()


@router.get("/stats", response_model=TranslateStatsResponse)
async def get_translate_stats(db: Session = Depends(get_db)):
    """
    获取翻译统计信息
    """
    total = db.query(func.count(Article.id)).scalar() or 0
    translated = db.query(func.count(Article.id)).filter(
        Article.is_translated == True
    ).scalar() or 0
    untranslated = total - translated

    # 统计中文来源
    chinese_count = db.query(func.count(Article.id)).filter(
        Article.source_name.in_(CHINESE_SOURCES)
    ).scalar() or 0

    return TranslateStatsResponse(
        total_articles=total,
        translated_articles=translated,
        untranslated_articles=untranslated,
        chinese_sources=chinese_count,
        english_articles=total - chinese_count,
    )


@router.post("/article/{article_id}/regenerate", response_model=TranslateResponse)
async def regenerate_translation(article_id: int, db: Session = Depends(get_db)):
    """
    重新翻译指定文章的摘要

    - **article_id**: 文章 ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if not article.summary:
        raise HTTPException(status_code=400, detail="文章没有摘要可翻译")

    # 强制重新翻译
    article.is_translated = False
    article.summary_zh = None
    article.translated_at = None
    db.commit()

    # 执行翻译
    translated = await translate_text(article.summary)

    if translated:
        save_translation(article_id, translated)
        return TranslateResponse(
            original=article.summary,
            translated=translated,
            language=detect_language(article.summary),
            success=True,
        )
    else:
        return TranslateResponse(
            original=article.summary,
            translated=None,
            language=detect_language(article.summary),
            success=False,
            error="翻译服务不可用或翻译失败",
        )
