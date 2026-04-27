"""Bookmarks API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Bookmark, SessionLocal, ArticleRead

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_bookmarks(db: Session = Depends(get_db)):
    bookmarks = db.query(Bookmark).order_by(Bookmark.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "article_id": b.article_id,
            "created_at": b.created_at.isoformat(),
            "article": ArticleRead.from_orm(b.article) if b.article else None,
        }
        for b in bookmarks
    ]


@router.delete("/{article_id}")
def delete_bookmark(article_id: int, db: Session = Depends(get_db)):
    bookmark = db.query(Bookmark).filter(Bookmark.article_id == article_id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"status": "deleted", "article_id": article_id}
