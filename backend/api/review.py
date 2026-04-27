"""评审委员会 API 端点 - 对文章进行严格评审"""

import asyncio
import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import Article, SessionLocal, ArticleRead, PaginatedArticles
from review_committee import get_committee, ReviewCommittee
from llm_client import get_llm_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["review"])

# 批量评审状态追踪
batch_status = {
    "running": False,
    "started_at": None,
    "total": 0,
    "processed": 0,
    "success": 0,
    "failed": 0,
    "current_article_id": None,
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChineseJSONResponse(JSONResponse):
    """支持中文不转义的JSON响应"""
    def __init__(self, content, **kwargs):
        import json
        kwargs.setdefault('media_type', 'application/json')
        super().__init__(content, **kwargs)

    def render(self, content) -> bytes:
        import json
        return json.dumps(content, ensure_ascii=False).encode('utf-8')


@router.get("/batch-status")
def get_batch_status():
    """
    获取批量评审进度状态

    返回当前批量评审任务的执行进度
    """
    progress = 0.0
    if batch_status["running"] and batch_status["total"] > 0:
        progress = round(batch_status["processed"] / batch_status["total"] * 100, 1)

    elapsed = 0
    if batch_status["started_at"]:
        elapsed = round(time.time() - batch_status["started_at"])

    return {
        "running": batch_status["running"],
        "progress": progress,
        "total": batch_status["total"],
        "processed": batch_status["processed"],
        "success": batch_status["success"],
        "failed": batch_status["failed"],
        "elapsed_seconds": elapsed,
        "current_article_id": batch_status["current_article_id"],
    }


@router.get("/llm-status")
def llm_status():
    """
    检查LLM服务状态

    返回LLM连接状态和可用模型列表
    """
    committee = get_committee()
    llm_client = get_llm_client()

    is_available = llm_client.is_available()
    models = []

    if is_available:
        try:
            models = llm_client.list_models()
        except Exception as e:
            logger.warning(f"获取模型列表失败: {e}")

    return {
        "llm_enabled": committee._use_llm,
        "llm_available": is_available,
        "model": llm_client.model,
        "base_url": llm_client.base_url,
        "installed_models": models,
        "status": "connected" if is_available else "disconnected"
    }


@router.post("/article/{article_id}")
async def review_article(article_id: int, db: Session = Depends(get_db)):
    """
    对指定文章进行评审（支持LLM异步评审）

    返回文章的详细评审结果
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    committee = get_committee()

    result = await committee.areview(
        article_id=article.id,
        title=article.title,
        text=article.summary or "",
        source_name=article.source_name,
        published_at=article.published_at,
        url=article.url
    )

    article.review_grade = result.grade
    article.review_score = int(result.total_score)
    article.review_result = result.to_dict()
    article.review_verdict = result.verdict
    article.reviewed_at = result.reviewed_at
    db.commit()

    return result.to_dict()


@router.post("/article/{article_id}/llm-review")
async def llm_review_article(article_id: int, db: Session = Depends(get_db)):
    """
    强制使用LLM评审指定文章

    忽略LLM_ENABLED设置，强制调用LLM
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    llm_client = get_llm_client()

    if not llm_client.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用")

    try:
        from prompts import build_review_prompt, parse_review_result

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

        return {
            "article_id": article_id,
            "raw_response": response[:500],
            "parsed_result": parsed,
            "llm_available": True
        }

    except Exception as e:
        logger.error(f"LLM评审失败: {e}")
        raise HTTPException(status_code=500, detail=f"LLM评审失败: {str(e)}")


@router.post("/batch")
def batch_review(
    background_tasks: BackgroundTasks,
    grade_filter: str = Query(
        None,
        description="按评级筛选要评审的文章: A/B/C/D 或组合如 'ABC'（留空则评审所有未评审的文章）"
    ),
    db: Session = Depends(get_db)
):
    """
    批量评审文章（后台执行）

    - grade_filter: 可选，按评级筛选（如 "AB" 表示 A 和 B）
    """
    query = db.query(Article).filter(Article.review_grade.is_(None))
    pending_count = query.count()

    if pending_count == 0:
        return {"status": "no_pending", "message": "没有待评审的文章"}

    # 如果已有任务在运行，不启动新任务
    if batch_status["running"]:
        return {
            "status": "already_running",
            "message": "批量评审任务已在运行中",
            "current": batch_status["processed"],
            "total": batch_status["total"]
        }

    # 设置运行状态
    batch_status["running"] = True
    batch_status["started_at"] = time.time()
    batch_status["total"] = pending_count
    batch_status["processed"] = 0
    batch_status["success"] = 0
    batch_status["failed"] = 0

    background_tasks.add_task(_batch_review_task)

    return {
        "status": "started",
        "pending_count": pending_count,
        "message": f"开始批量评审 {pending_count} 篇文章"
    }


@router.post("/llm-batch")
async def llm_batch_review(
    limit: int = Query(10, ge=1, le=50, description="每次批量评审的文章数量"),
    db: Session = Depends(get_db)
):
    """
    使用LLM批量评审文章

    每次评审指定数量的文章，适合在LLM服务可用时使用
    """
    llm_client = get_llm_client()

    if not llm_client.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用")

    articles = db.query(Article).filter(
        Article.review_grade.is_(None)
    ).limit(limit).all()

    if not articles:
        return {"status": "no_pending", "message": "没有待评审的文章"}

    from prompts import build_review_prompt, parse_review_result, calculate_total_score, grade_from_scores
    from datetime import datetime

    results = []

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

            scores = parsed.get("scores", {})
            total_score = calculate_total_score(scores)
            grade = parsed.get("grade") or grade_from_scores(scores)

            article.review_grade = grade
            article.review_score = int(total_score)
            article.review_result = parsed
            article.review_verdict = parsed.get("verdict", "")
            article.reviewed_at = datetime.utcnow()

            db.commit()

            results.append({
                "article_id": article.id,
                "title": article.title[:50],
                "grade": grade,
                "score": total_score,
                "verdict": parsed.get("verdict", "")
            })

        except Exception as e:
            logger.error(f"LLM评审文章 {article.id} 失败: {e}")
            results.append({
                "article_id": article.id,
                "title": article.title[:50] if article.title else "未知",
                "error": str(e)
            })

    return {
        "status": "completed",
        "reviewed_count": len([r for r in results if "error" not in r]),
        "failed_count": len([r for r in results if "error" in r]),
        "results": results
    }


@router.post("/batch-backlog")
async def review_batch_backlog(
    limit: int = Query(50, ge=1, le=100, description="每次批量评审的文章数量"),
    db: Session = Depends(get_db)
):
    """
    批量评审未评审的历史文章

    用于将数据库中已有的未评审文章全部评审
    """
    llm_client = get_llm_client()

    if not llm_client.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用")

    # 查询未评审的文章
    articles = db.query(Article).filter(
        Article.review_grade.is_(None)
    ).limit(limit).all()

    if not articles:
        return {
            "status": "no_pending",
            "message": "没有待评审的文章",
            "remaining": 0
        }

    from prompts import build_review_prompt, parse_review_result, calculate_total_score, grade_from_scores
    from datetime import datetime

    results = []
    success_count = 0
    fail_count = 0

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

            results.append({
                "article_id": article.id,
                "title": article.title[:50] if article.title else "未知",
                "grade": grade,
                "score": int(total_score),
                "verdict": parsed.get("verdict", "")[:100] if parsed.get("verdict") else ""
            })

        except Exception as e:
            db.rollback()
            fail_count += 1
            logger.error(f"评审文章 {article.id} 失败: {e}")
            results.append({
                "article_id": article.id,
                "title": article.title[:50] if article.title else "未知",
                "error": str(e)
            })

    # 计算剩余待评审数量
    remaining = db.query(Article).filter(Article.review_grade.is_(None)).count()

    return ChineseJSONResponse(content={
        "status": "completed",
        "reviewed": success_count,
        "failed": fail_count,
        "remaining": remaining,
        "results": results
    })


async def _batch_review_task():
    """后台批量评审任务（异步）"""
    global batch_status

    db = SessionLocal()
    try:
        committee = get_committee()

        articles = db.query(Article).filter(
            Article.review_grade.is_(None)
        ).all()

        # 更新状态
        batch_status["total"] = len(articles)
        batch_status["processed"] = 0
        batch_status["success"] = 0
        batch_status["failed"] = 0

        for article in articles:
            batch_status["current_article_id"] = article.id
            try:
                result = await committee.areview(
                    article_id=article.id,
                    title=article.title,
                    text=article.summary or "",
                    source_name=article.source_name,
                    published_at=article.published_at,
                    url=article.url
                )

                article.review_grade = result.grade
                article.review_score = int(result.total_score)
                article.review_result = result.to_dict()
                article.review_verdict = result.verdict
                article.reviewed_at = result.reviewed_at
                db.commit()
                batch_status["success"] += 1

            except Exception as e:
                db.rollback()
                batch_status["failed"] += 1
                logger.error(f"评审文章 {article.id} 失败: {e}")

            batch_status["processed"] += 1

    finally:
        db.close()
        batch_status["running"] = False
        batch_status["current_article_id"] = None


@router.get("/stats")
def review_stats(db: Session = Depends(get_db)):
    """
    获取评审统计信息

    返回各评级分布、通过率等统计数据
    """
    grade_stats = db.query(
        Article.review_grade,
        func.count(Article.id).label("count")
    ).filter(
        Article.review_grade.isnot(None)
    ).group_by(Article.review_grade).all()

    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for grade, count in grade_stats:
        if grade in grade_counts:
            grade_counts[grade] = count

    total_reviewed = sum(grade_counts.values())
    total_pending = db.query(Article).filter(Article.review_grade.is_(None)).count()

    pass_rate = 0.0
    if total_reviewed > 0:
        pass_rate = round(
            (grade_counts.get("A", 0) + grade_counts.get("B", 0)) / total_reviewed * 100, 1
        )

    llm_available = False
    try:
        llm_client = get_llm_client()
        llm_available = llm_client.is_available()
    except:
        pass

    grade_distribution = {
        "A": {"count": grade_counts.get("A", 0), "label": "强烈推荐", "color": "#10b981"},
        "B": {"count": grade_counts.get("B", 0), "label": "推荐", "color": "#3b82f6"},
        "C": {"count": grade_counts.get("C", 0), "label": "待定", "color": "#f59e0b"},
        "D": {"count": grade_counts.get("D", 0), "label": "过滤", "color": "#6b7280"},
    }

    return ChineseJSONResponse(content={
        "total_reviewed": total_reviewed,
        "total_pending": total_pending,
        "pass_rate": pass_rate,
        "grade_counts": grade_counts,
        "grade_distribution": grade_distribution,
        "committee_status": "active",
        "llm_available": llm_available,
    })


@router.get("/articles")
def list_articles_by_grade(
    grade: Optional[str] = Query(
        None,
        description="按评级筛选: A/B/C/D（留空则返回所有已评审的文章）"
    ),
    min_score: Optional[int] = Query(
        None,
        ge=0,
        le=50,
        description="最低综合分数"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    按评级或分数筛选文章

    可用于：
    - 查看只显示优质内容（A+B）
    - 查看被过滤的内容（D）
    - 按分数排序
    """
    query = db.query(Article).filter(Article.review_grade.isnot(None))

    if grade:
        grades = list(grade.upper())
        query = query.filter(Article.review_grade.in_(grades))

    if min_score is not None:
        query = query.filter(Article.review_score >= min_score)

    total = query.count()

    query = query.order_by(desc(Article.review_score))
    query = query.offset((page - 1) * limit).limit(limit)

    articles = query.all()
    items = [ArticleRead.from_orm(a) for a in articles]
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedArticles(items=items, total=total, page=page, limit=limit, pages=pages)


@router.post("/article/{article_id}/re-review")
async def re_review_article(article_id: int, db: Session = Depends(get_db)):
    """
    重新评审文章（清除旧结果后重新评审）
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.review_grade = None
    article.review_score = None
    article.review_result = None
    article.review_verdict = None
    article.reviewed_at = None
    db.commit()

    return await review_article(article_id, db)


@router.post("/filter")
def filter_articles(
    min_grade: str = Query("B", description="最低显示评级: A/B/C/D，默认B表示只显示A和B"),
    db: Session = Depends(get_db)
):
    """
    获取通过评审的文章列表（便捷接口）

    等同于 list_articles_by_grade(grade=min_grade)
    """
    grade_map = {"A": "AB", "B": "AB", "C": "ABC", "D": "ABCD"}
    grade = grade_map.get(min_grade.upper(), "AB")

    query = db.query(Article).filter(Article.review_grade.in_(list(grade)))
    total = query.count()

    query = query.order_by(desc(Article.review_score)).limit(100)
    articles = query.all()

    return {
        "min_grade": min_grade.upper(),
        "grade_filter": grade,
        "total": total,
        "articles": [ArticleRead.from_orm(a) for a in articles[:20]]
    }
