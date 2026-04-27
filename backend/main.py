"""FastAPI application entry point."""

import logging
import os
import sys

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from scraper.rss_parser import fetch_all_feeds
from scheduler import init_scheduler, shutdown_scheduler
from api.articles import router as articles_router
from api.bookmarks import router as bookmarks_router
from api.stats import router as stats_router
from api.review import router as review_router
from api.sources import router as sources_router
from api.translate import router as translate_router

load_dotenv()

# Use a UTF-8 StreamHandler on Windows to avoid ASCII encoding errors in logs
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self):
        try:
            import io
            super().__init__(stream=sys.stderr)
        except Exception:
            super().__init__()
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Last resort: encode message and replace unrepresentable chars
            msg = self.format(record)
            safe = msg.encode("utf-8", errors="replace").decode("utf-8")
            print(safe, file=sys.stderr, flush=True)


_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
for h in _root_logger.handlers[:]:
    _root_logger.removeHandler(h)
_root_logger.addHandler(UTF8StreamHandler())
_root_logger.info("Logger initialized.")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting scheduler...")
    init_scheduler()
    # 直接在后台线程运行初始抓取，不阻塞
    import threading
    def background_fetch():
        import time
        time.sleep(1)  # 等待服务器完全启动
        logger.info("Starting initial feed fetch in background...")
        try:
            result = fetch_all_feeds()
            logger.info("Initial fetch complete: %s", result)
        except Exception as e:
            logger.error("Initial fetch failed: %s", e)
    threading.Thread(target=background_fetch, daemon=True).start()
    yield
    logger.info("Shutting down scheduler...")
    shutdown_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="AI情报站 API",
    description="AI资讯聚合与推送后端服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(bookmarks_router)
app.include_router(stats_router)
app.include_router(review_router)
app.include_router(sources_router)
app.include_router(translate_router)

# API路由（必须在通配符路由之前）
@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/admin/refresh")
def trigger_refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_all_feeds)
    return {"status": "triggered", "message": "Feed refresh started in background"}

# favicon 处理
@app.get("/favicon.ico")
async def favicon():
    dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    favicon_path = os.path.join(dist_path, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    return {"error": "not found"}

# 静态文件服务
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

# 前端入口
@app.get("/")
def root():
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "AI情报站 API",
        "version": "0.1.0",
        "status": "running",
    }

# 通配符路由 - 必须放在最后
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # 静态文件已由 /assets 路由处理
    # 只需返回 index.html 让前端路由处理
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not built."}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
