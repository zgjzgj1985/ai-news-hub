"""Stats and feed source management endpoints."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import Article, Bookmark, FeedSource, SessionLocal, StatsResponse

router = APIRouter(prefix="/api", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    grade: Optional[str] = Query(None, description="Filter by review grade: A/B/C/D or combined like 'AB'"),
):
    # 只统计通过评审的内容（A/B/C 级），D 级是垃圾信息不计入
    base_filter = Article.review_grade != 'D'

    if grade:
        grades = list(grade.upper())
        base_filter = base_filter & Article.review_grade.in_(grades)

    total_articles = db.query(Article).filter(base_filter).count()
    total_bookmarks = db.query(Bookmark).count()
    total_sources = db.query(FeedSource).count()

    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    articles_last_24h = db.query(Article).filter(
        Article.fetched_at >= last_24h, base_filter
    ).count()
    articles_last_7d = db.query(Article).filter(
        Article.fetched_at >= last_7d, base_filter
    ).count()

    from sqlalchemy import text
    tag_counts: dict[str, int] = {}
    # 只统计通过评审的内容的标签
    grade_filter_sql = ""
    if grade:
        grade_list = "('" + "','".join(list(grade.upper())) + "')"
        grade_filter_sql = f" AND articles.review_grade IN {grade_list}"
    result = db.execute(text(
        "SELECT json_each.value, COUNT(*) FROM articles, json_each(articles.tags) "
        "WHERE articles.review_grade != 'D'" + grade_filter_sql +
        " GROUP BY json_each.value"
    ))
    for tag_name, count in result.fetchall():
        tag_counts[tag_name] = count

    return StatsResponse(
        total_articles=total_articles,
        total_bookmarks=total_bookmarks,
        total_sources=total_sources,
        tag_counts=tag_counts,
        articles_last_24h=articles_last_24h,
        articles_last_7d=articles_last_7d,
    )


@router.get("/stats/review")
def get_review_stats(db: Session = Depends(get_db)):
    """获取评审统计信息"""
    # 统计各评级数量
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

    # 计算通过率（A、B为通过）
    pass_rate = 0.0
    if total_reviewed > 0:
        pass_rate = round((grade_counts.get("A", 0) + grade_counts.get("B", 0)) / total_reviewed * 100, 1)

    # 评级分布（用于前端展示）
    grade_distribution = {
        "A": {"count": grade_counts.get("A", 0), "label": "强烈推荐", "color": "#10b981"},
        "B": {"count": grade_counts.get("B", 0), "label": "推荐", "color": "#3b82f6"},
        "C": {"count": grade_counts.get("C", 0), "label": "待定", "color": "#f59e0b"},
        "D": {"count": grade_counts.get("D", 0), "label": "过滤", "color": "#6b7280"},
    }

    return {
        "total_reviewed": total_reviewed,
        "total_pending": total_pending,
        "pass_rate": pass_rate,
        "grade_counts": grade_counts,
        "grade_distribution": grade_distribution,
        "committee_status": "active",
    }


# ---- Feed Sources CRUD ----

@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(FeedSource).order_by(FeedSource.priority.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "category": s.category,
            "enabled": s.enabled,
            "priority": s.priority,
            "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in sources
    ]


@router.post("/sources")
def create_source(data: dict, db: Session = Depends(get_db)):
    existing = db.query(FeedSource).filter(FeedSource.url == data.get("url")).first()
    if existing:
        raise HTTPException(status_code=409, detail="Feed source already exists")

    source = FeedSource(
        name=data.get("name"),
        url=data.get("url"),
        category=data.get("category", "general"),
        enabled=data.get("enabled", True),
        priority=data.get("priority", 0),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "category": source.category,
        "enabled": source.enabled,
        "priority": source.priority,
        "last_fetched": None,
        "created_at": source.created_at.isoformat(),
    }


@router.patch("/sources/{source_id}")
def update_source(source_id: int, data: dict, db: Session = Depends(get_db)):
    source = db.query(FeedSource).filter(FeedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Feed source not found")

    if "name" in data:
        source.name = data["name"]
    if "url" in data:
        source.url = data["url"]
    if "category" in data:
        source.category = data["category"]
    if "enabled" in data:
        source.enabled = data["enabled"]
    if "priority" in data:
        source.priority = data["priority"]

    db.commit()
    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "category": source.category,
        "enabled": source.enabled,
        "priority": source.priority,
        "last_fetched": source.last_fetched.isoformat() if source.last_fetched else None,
        "created_at": source.created_at.isoformat(),
    }


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(FeedSource).filter(FeedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Feed source not found")
    db.delete(source)
    db.commit()
    return {"status": "deleted", "id": source_id}
