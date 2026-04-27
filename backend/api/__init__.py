"""API package."""

from api.articles import router as articles_router
from api.bookmarks import router as bookmarks_router
from api.stats import router as stats_router
from api.sources import router as sources_router
from api.review import router as review_router

__all__ = ["articles_router", "bookmarks_router", "stats_router", "sources_router", "review_router"]
