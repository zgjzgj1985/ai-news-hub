"""Articles API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from database import Article, Bookmark, SessionLocal, ArticleRead, PaginatedArticles

router = APIRouter(prefix="/api/articles", tags=["articles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PaginatedArticles)
def list_articles(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    keyword: Optional[str] = Query(None, description="Search in title/summary"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    grade: Optional[str] = Query(None, description="Filter by review grade: A/B/C/D or combined like 'AB'"),
    min_score: Optional[int] = Query(None, ge=0, le=780, description="Minimum review score (0-780)"),
    sort: str = Query("newest", regex="^(newest|oldest)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Article)

    # 核心过滤：只有完成深度评审的文章才展示（无评分内容不上线）
    q = q.filter(Article.deep_review_done == True)

    # 默认过滤：D 级内容不返回（垃圾信息不进列表）
    q = q.filter(Article.review_grade != 'D')

    if tag:
        tag_subq = text(
            "SELECT articles.id FROM articles, json_each(articles.tags) "
            "WHERE json_each.value = :tag"
        ).bindparams(tag=tag)
        q = q.filter(Article.id.in_(tag_subq))

    if keyword:
        q = q.filter(
            (Article.title.ilike(f"%{keyword}%")) | (Article.summary.ilike(f"%{keyword}%"))
        )

    if source:
        q = q.filter(Article.source_name == source)

    if grade:
        grades = list(grade.upper())
        q = q.filter(Article.review_grade.in_(grades))

    if min_score is not None:
        q = q.filter(Article.review_score >= min_score)

    total = q.count()

    q = q.order_by(desc(Article.published_at) if sort == "newest" else Article.published_at)
    q = q.offset((page - 1) * limit).limit(limit)

    articles = q.all()
    items = [ArticleRead.from_orm(a) for a in articles]
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedArticles(items=items, total=total, page=page, limit=limit, pages=pages)


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deep_review_done == True,
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleRead.from_orm(article)


@router.post("/{article_id}/bookmark")
def toggle_bookmark(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    existing = db.query(Bookmark).filter(Bookmark.article_id == article_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed", "article_id": article_id}

    bookmark = Bookmark(article_id=article_id)
    db.add(bookmark)
    db.commit()
    return {"status": "added", "article_id": article_id}


@router.get("/{article_id}/bookmark")
def get_bookmark_status(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    existing = db.query(Bookmark).filter(Bookmark.article_id == article_id).first()
    return {"is_bookmarked": existing is not None}
