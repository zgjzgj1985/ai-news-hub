"""订阅源管理 API 端点。"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import FeedSource, SessionLocal, FeedSourceCreate, FeedSourceRead, FeedSourceUpdate

router = APIRouter(prefix="/api/sources", tags=["sources"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[FeedSourceRead])
def list_sources(db: Session = Depends(get_db)):
    """获取所有订阅源列表，按优先级降序排列。"""
    sources = db.query(FeedSource).order_by(FeedSource.priority.desc()).all()
    return [FeedSourceRead.model_validate(s) for s in sources]


@router.get("/{source_id}", response_model=FeedSourceRead)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """获取指定订阅源的详情。"""
    source = db.query(FeedSource).filter(FeedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="订阅源不存在")
    return FeedSourceRead.model_validate(source)


@router.post("", response_model=FeedSourceRead, status_code=201)
def create_source(source_data: FeedSourceCreate, db: Session = Depends(get_db)):
    """创建新的订阅源。"""
    existing = db.query(FeedSource).filter(FeedSource.url == source_data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="该URL的订阅源已存在")

    source = FeedSource(**source_data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return FeedSourceRead.model_validate(source)


@router.patch("/{source_id}", response_model=FeedSourceRead)
def update_source(source_id: int, update_data: FeedSourceUpdate, db: Session = Depends(get_db)):
    """更新订阅源配置。"""
    source = db.query(FeedSource).filter(FeedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="订阅源不存在")

    update_dict = update_data.model_dump(exclude_unset=True)

    # 如果更新URL，检查是否与现有订阅源冲突
    if "url" in update_dict:
        existing = db.query(FeedSource).filter(
            FeedSource.url == update_dict["url"],
            FeedSource.id != source_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该URL的订阅源已存在")

    for key, value in update_dict.items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return FeedSourceRead.model_validate(source)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除订阅源。"""
    source = db.query(FeedSource).filter(FeedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="订阅源不存在")

    db.delete(source)
    db.commit()
    return None
