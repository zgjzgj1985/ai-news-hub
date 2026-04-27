import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text,
    create_engine, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
db_url = os.getenv("DATABASE_URL", "sqlite:///../data/articles.db")
if db_url.startswith("sqlite:///"):
    rel_path = db_url.replace("sqlite:///", "")
    db_path = (BASE_DIR / rel_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
# 使用绝对路径确保中文路径正确处理
db_url = f"sqlite:///{db_path.as_posix()}"

# 创建引擎时启用UTF-8支持
engine = create_engine(
    db_url,
    echo=False,
    connect_args={
        "check_same_thread": False,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    title_zh = Column(String(500), nullable=True)  # 翻译后的中文标题
    url = Column(String(1000), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    summary_zh = Column(Text, nullable=True)  # 翻译后的中文摘要
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(1000), nullable=True)
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON, default=list)
    content_hash = Column(String(64), nullable=True)
    read_time_minutes = Column(Integer, default=3)
    # 热度分数：来自 HN/Reddit/StackExchange 的评分
    score = Column(Integer, nullable=True, default=None)
    # 翻译状态
    is_translated = Column(Boolean, default=False)  # 是否已翻译
    translated_at = Column(DateTime, nullable=True)  # 翻译时间

    # 评审委员会字段
    review_grade = Column(String(1), nullable=True, default=None)  # A/B/C/D
    review_score = Column(Integer, nullable=True, default=None)     # 0-50 综合分数
    review_result = Column(JSON, nullable=True, default=None)       # 详细评审结果
    review_verdict = Column(Text, nullable=True, default=None)      # 最终裁决理由
    reviewed_at = Column(DateTime, nullable=True)                   # 评审时间

    bookmark = relationship("Bookmark", back_populates="article", uselist=False)

    __table_args__ = (
        Index("ix_articles_published", "published_at"),
        Index("ix_articles_source", "source_name"),
        Index("ix_articles_hash", "content_hash"),
        Index("ix_articles_score", "score"),
        Index("ix_articles_review_grade", "review_grade"),
        Index("ix_articles_translated", "is_translated"),
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="bookmark")


class FeedSource(Base):
    __tablename__ = "feed_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    category = Column(String(50), default="general")
    enabled = Column(Boolean, default=True)
    last_fetched = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_feed_sources_enabled", "enabled"),
    )


# ---- Pydantic schemas ----

class ArticleBase(BaseModel):
    title: str
    title_zh: Optional[str] = None  # 翻译后的中文标题
    url: str
    summary: Optional[str] = None
    summary_zh: Optional[str] = None  # 翻译后的中文摘要
    source_name: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    tags: list[str] = []
    read_time_minutes: int = 3
    score: Optional[int] = None
    review_grade: Optional[str] = None  # A/B/C/D
    review_score: Optional[int] = None  # 0-50 综合分数
    review_verdict: Optional[str] = None  # 最终裁决理由
    is_translated: bool = False  # 是否已翻译


class ArticleCreate(ArticleBase):
    content_hash: Optional[str] = None


class ArticleRead(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fetched_at: datetime
    is_bookmarked: bool = False
    review_result: Optional[dict] = None  # 详细评审结果
    translated_at: Optional[datetime] = None  # 翻译时间

    @classmethod
    def from_orm(cls, article: Article) -> "ArticleRead":
        return cls(
            id=article.id,
            title=article.title,
            title_zh=article.title_zh,
            url=article.url,
            summary=article.summary,
            summary_zh=article.summary_zh,
            source_name=article.source_name,
            source_url=article.source_url,
            author=article.author,
            published_at=article.published_at,
            fetched_at=article.fetched_at,
            tags=article.tags or [],
            read_time_minutes=article.read_time_minutes,
            score=article.score,
            is_bookmarked=article.bookmark is not None,
            review_grade=article.review_grade,
            review_score=article.review_score,
            review_verdict=article.review_verdict,
            review_result=article.review_result,
            is_translated=article.is_translated,
            translated_at=article.translated_at,
        )


class BookmarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    created_at: datetime
    article: Optional[ArticleRead] = None


class FeedSourceBase(BaseModel):
    name: str
    url: str
    category: str = "general"
    enabled: bool = True
    priority: int = 0


class FeedSourceCreate(FeedSourceBase):
    pass


class FeedSourceRead(FeedSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_fetched: Optional[datetime] = None
    created_at: datetime


class FeedSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class StatsResponse(BaseModel):
    total_articles: int
    total_bookmarks: int
    total_sources: int
    tag_counts: dict[str, int]
    articles_last_24h: int
    articles_last_7d: int


class PaginatedArticles(BaseModel):
    items: list[ArticleRead]
    total: int
    page: int
    limit: int
    pages: int


# ---- Database helpers ----

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (订阅源由 update_sources.py 管理，不在这里创建默认源)。"""
    Base.metadata.create_all(bind=engine)
