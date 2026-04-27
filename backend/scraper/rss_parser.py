"""RSS parser for fetching and parsing feed entries with quality filtering."""

import asyncio
import hashlib
import logging
import re
import time
import chardet
from datetime import datetime
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from database import Article, FeedSource, SessionLocal
from scraper.classifier import classify, is_academic_content
from scraper.sources import is_academic_source, requires_code
from review_committee import get_committee

logger = logging.getLogger(__name__)


def _safe_decode(raw_bytes: bytes) -> str:
    """
    智能解码原始字节流，尝试多种编码方式以解决乱码问题。
    
    优先级：检测到的编码 > UTF-8 > GBK > GB2312 > Latin-1
    """
    if not raw_bytes:
        return ""
    
    # 尝试检测编码
    detected = chardet.detect(raw_bytes)
    encoding = detected.get("encoding", "")
    confidence = detected.get("confidence", 0)
    
    # 如果检测置信度高，使用检测到的编码
    if confidence > 0.7 and encoding:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            pass
    
    # 尝试常见编码
    encodings_to_try = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "latin-1", "iso-8859-1", "cp1252"]
    
    for enc in encodings_to_try:
        try:
            decoded = raw_bytes.decode(enc)
            # 如果解码后没有乱码标记（如 ?），则使用
            if "?" not in decoded or decoded.count("?") < len(decoded) * 0.05:
                return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 最后手段：忽略错误解码
    return raw_bytes.decode("utf-8", errors="replace")


def _safe_log(level, msg, *args):
    """日志记录函数，确保在 Windows 上不会因编码问题崩溃。"""
    try:
        if args:
            msg = str(msg) % tuple(str(a) for a in args)
        msg_str = str(msg)
        safe_msg = msg_str.encode("ascii", errors="replace").decode("ascii")
        logger.log(level, safe_msg)
    except Exception:
        pass


FETCH_TIMEOUT = 30

# 来源特定的质量阈值
# HN: 超过30分才入库 (HN分数本身已经过社区筛选)
# Reddit: 超过20赞才入库
# 一般源: 不设限
SOURCE_QUALITY_THRESHOLDS = {
    "Hacker News AI": 30,      # HN 自带评分
    "Reddit r/LocalLLaMA": 20,  # Reddit 点赞
    "Reddit r/StableDiffusion": 20,
    "Reddit r/LocalLLaMA": 20,
    "AI Stack Exchange": 5,     # StackExchange vote
    # 默认无限制
}

# 每个源每天最多抓取的文章数 (防止噪音源淹没优质内容)
# 高质量博客类来源可以多抓，RSS 新闻源适当控制
SOURCE_DAILY_LIMITS = {
    # 高质量博客 - 可以多抓
    "Hugging Face Blog": 30,
    "OpenAI Blog": 30,       # 提高（包含AI编程内容）
    "Anthropic Blog": 30,     # 提高（包含Claude代码相关）
    "Google DeepMind Blog": 20,
    "Meta AI Blog": 20,
    "Stability AI Blog": 20,
    "Mistral AI Blog": 20,
    "机器之心": 30,
    "量子位": 30,
    # 新闻/社区 - 适度抓取
    "Hacker News AI": 20,
    "MIT Technology Review": 20,
    "The Verge AI": 20,
    "Game Developer": 20,
    "AI Stack Exchange": 20,
    # 学术来源
    "ArXiv cs.AI": 20,
    "ArXiv cs.CV (视觉)": 20,
    "Papers with Code": 15,
    # Reddit - 限制抓取（内容质量参差不齐）
    "r/LocalLLaMA": 15,      # 提高（包含本地AI编程）
    "r/StableDiffusion": 10,
    "r/ComfyUI": 15,         # 提高（包含AI工作流）
    "r/GameAI": 15,          # 提高（游戏AI）
    # Vibe Coding 来源 - 提高限制
    "Windsurf Blog": 20,      # 核心Vibe Coding来源
    "GitHub Blog": 25,        # 提高（包含AI工具发布）
    "Cursor Blog (社区RSS)": 25,  # Cursor 官方博客（社区维护版）
    # 默认 20
    "_default": 20,
}

# Reddit帖子需要更高质量才收录
REDDIT_MIN_SCORE = 10  # 至少10个 upvotes

# 中文AI媒体的RSS源（用于识别中文内容）
CHINESE_AI_FEEDS = ["机器之心", "量子位", "36氪", "雷锋网", "爱范儿"]

# 高质量来源列表 - 来自这些源的文章可以更宽松
HIGH_QUALITY_SOURCES = [
    # AI 公司博客
    "OpenAI Blog", "Hugging Face Blog", "Anthropic Blog", "Google DeepMind Blog",
    "Meta AI Blog", "Mistral AI Blog", "Stability AI Blog",
    # 学术与社区
    "The Batch", "Import AI",
    "机器之心", "量子位",
    "AI Stack Exchange", "Data Stack Exchange",
    # Vibe Coding 核心来源
    "Windsurf Blog", "GitHub Blog", "Cursor Blog (社区RSS)",
]

# 无意义标题模式
MEANINGLESS_TITLE_PATTERNS = [
    r"^close\??$",           # "Close?" 这种无意义标题
    r"^question\??$",
    r"^help\??$",
    r"^\[?deleted\]?$",
    r"^\[?removed\]?$",
    r"^快讯：",               # 太短的新闻标题
    r"^今日热词：",
    r"^今日要闻：",
]

# Hacker News AI 关键词 - 文章必须包含至少一个这些关键词
HN_AI_KEYWORDS = [
    # AI/ML 相关
    "ai", "ml", "machine learning", "deep learning", "neural", "llm", "gpt", "claude", "gemini",
    "transformer", "diffusion", "stable diffusion", "openai", "anthropic", "hugging face",
    "langchain", "rag", "embedding", "fine-tuning", "rlhf", "agent", "copilot", "cursor",
    "midjourney", "sora", "dall-e", "flux", "comfyui", "lora", "controlnet",
    # 工具/框架
    "github", "open source", "framework", "library", "api", "sdk", "cli",
    "python", "javascript", "typescript", "rust", "golang",
    # 开发者工具
    "cursor", "windsurf", "copilot", "codeium", "tabnine",
    "v0", "bolt", "lovable", "replit", "perplexity",
]


def compute_hash(title: str, url: str) -> str:
    return hashlib.sha256(f"{title}|{url}".encode()).hexdigest()


def estimate_read_time(text: str) -> int:
    if not text:
        return 1
    words = len(text.split())
    return max(1, round(words / 200))


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000]


def is_reddit_template_text(text: str) -> bool:
    """
    检测是否为Reddit的模板文本（无意义摘要）。
    
    Reddit RSS经常只返回 "submitted by /u/xxx [link] [comments]" 这种模板。
    """
    if not text:
        return True
    
    # Reddit 模板模式
    reddit_patterns = [
        r"submitted by\s*/?u/\w+",
        r"\[link\]\s*\[comments\]",
        r"View more community posts",
        r"^[\s\n]*$",  # 纯空白
    ]
    
    text_lower = text.lower()
    
    for pattern in reddit_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # 太短的文本（少于30个字符）
    if len(text.strip()) < 30:
        return True
    
    # 如果文本只包含链接和用户名，没有实际内容
    words = text.split()
    if len(words) < 10:
        return True
        
    return False


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
    ]
    for fmt in formats:
        try:
            if isinstance(date_str, str):
                val = date_str.strip()
                if val.endswith("Z"):
                    val = val[:-1] + "+0000"
                return datetime.strptime(val, fmt)
        except (ValueError, OSError):
            continue
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def extract_score(entry: dict, source_name: str) -> Optional[int]:
    """
    从RSS条目中提取热度评分。

    不同来源有不同的评分机制：
    - Hacker News: "score" 或 "hn_handler"
    - Reddit: "reddit_score" 或 "score"
    - StackExchange: "score"
    """
    score = None

    # Hacker News 格式
    if hasattr(entry, 'score'):
        score = entry.get('score')
    elif 'score' in entry:
        score = entry.get('score')

    # Reddit 格式
    if hasattr(entry, 'reddit_score'):
        score = entry.get('reddit_score')

    # 处理字符串格式的分数
    if score is not None:
        if isinstance(score, str):
            # 尝试提取数字
            match = re.search(r'(\d+)', str(score))
            if match:
                score = int(match.group(1))

    return score


def should_include_article(
    source_name: str,
    score: Optional[int],
    title: str,
    summary: str
) -> bool:
    """
    基于多个维度判断文章是否值得收录。

    策略：
    - 高质量来源：标题有意义即可收录
    - HN/Reddit：需要一定分数或摘要质量
    - 一般来源：需要有基本长度和可读性
    - 学术来源：必须有GitHub代码或实战案例
    """
    title_lower = title.lower().strip()
    combined_text = (title + " " + summary).lower()

    # ========== 1. 检查无意义标题 ==========
    for pattern in MEANINGLESS_TITLE_PATTERNS:
        if re.match(pattern, title_lower, re.IGNORECASE):
            _safe_log(logging.INFO, "Article filtered by meaningless title: %s", title[:50])
            return False

    # 标题太短（少于5个字符）
    if len(title.strip()) < 5:
        _safe_log(logging.INFO, "Article filtered by short title: %s", title[:50])
        return False

    # ========== 2. 学术来源必须代码/实战 ==========
    if is_academic_source(source_name):
        # 检查是否有GitHub、代码、或实战关键词
        code_indicators = [
            "github", "code", "implementation",
            "tutorial", "example", "demo",
            "实战", "案例", "case study", "how to",
            "notebook", "colab", "jupyter",
        ]
        has_code = any(indicator in combined_text for indicator in code_indicators)
        if not has_code:
            _safe_log(logging.INFO, "Academic article filtered - no code/example: %s", title[:50])
            return False

    # ========== 3. 高质量来源：只要标题有意义就收录 ==========
    if source_name in HIGH_QUALITY_SOURCES:
        return True

    # ========== 4. Hacker News AI 必须包含AI相关关键词 ==========
    if source_name == "Hacker News AI":
        has_ai_keyword = any(kw in combined_text for kw in HN_AI_KEYWORDS)
        if not has_ai_keyword:
            _safe_log(logging.INFO, "HN AI filtered - no AI keyword: %s", title[:50])
            return False
        # HN AI 也需要一定分数
        if score is not None and score < 15:
            _safe_log(logging.INFO, "HN AI filtered - low score (%d): %s", score, title[:50])
            return False

    # ========== 5. Reddit（通过URL识别）==========
    if "reddit" in title_lower or "/r/" in title:
        # Reddit 需要高分数
        if score is not None and score < 15:
            _safe_log(logging.INFO, "Article filtered by Reddit low score: %s (score: %d)", title[:50], score)
            return False
        # 或者需要有实质性摘要
        if is_reddit_template_text(summary):
            _safe_log(logging.INFO, "Article filtered by Reddit no summary: %s", title[:50])
            return False

    # ========== 6. 一般来源：检查内容质量 ==========
    # 标题 + 摘要的总长度需要有一定长度
    if len(combined_text.strip()) < 30:
        _safe_log(logging.INFO, "Article filtered by short content: %s", title[:50])
        return False

    # ========== 7. 检查推广/垃圾内容 ==========
    spam_patterns = [
        "sponsored by",
        "[promoted]",
        "[sponsor]",
        "buy now",
        "click here",
        "casino",
        "成人内容",
    ]
    for pattern in spam_patterns:
        if pattern in title_lower:
            _safe_log(logging.INFO, "Article filtered by spam pattern: %s", title[:50])
            return False

    return True


def fetch_feed(source: FeedSource, max_articles: int = 50) -> list[Article]:
    """
    获取单个订阅源的文章列表。

    改进点：
    1. 提取并记录热度分数
    2. 基于质量阈值过滤
    3. 每个源限制每日抓取数量
    """
    articles = []
    fetched_count = 0

    # 获取当天的文章数量限制
    daily_limit = SOURCE_DAILY_LIMITS.get(source.name, SOURCE_DAILY_LIMITS.get("_default", 20))

    db = SessionLocal()
    try:
        existing_hashes = {
            row[0]
            for row in db.query(Article.content_hash).filter(Article.content_hash.isnot(None)).all()
        }
        existing_urls = {row[0] for row in db.query(Article.url).all()}
    finally:
        db.close()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    try:
        response = requests.get(source.url, headers=headers, timeout=FETCH_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        # 使用智能解码处理编码问题
        content = _safe_decode(response.content)
        feed = feedparser.parse(content)
    except Exception as e:
        _safe_log(logging.ERROR, "Failed to fetch %s: %s", source.name, str(e))
        return []

    if not feed.entries:
        _safe_log(logging.WARNING, "No entries found: %s", source.name)
        return []

    for entry in feed.entries:
        # 检查是否达到抓取上限
        if fetched_count >= daily_limit:
            _safe_log(logging.INFO, "[%s] Reached daily limit (%d), stopping", source.name, daily_limit)
            break

        title = entry.get("title", "").strip()
        url = entry.get("link") or entry.get("id", "")
        if not title or not url:
            continue

        url = url.strip()
        if url in existing_urls:
            continue

        content_hash = compute_hash(title, url)
        if content_hash in existing_hashes:
            continue

        # 提取摘要 - 优先从多个字段获取有意义的摘要
        summary = ""
        
        # 1. 尝试从 content 字段获取（通常比 summary 更丰富）
        if entry.get("content"):
            for c in entry.get("content", []):
                content_value = c.get("value", "")
                if content_value:
                    raw_summary = clean_html(content_value)
                    if not is_reddit_template_text(raw_summary):
                        summary = raw_summary
                        break
        
        # 2. 如果 content 不可用，尝试从 summary 获取
        if not summary and entry.get("summary"):
            raw_summary = clean_html(entry["summary"])
            if not is_reddit_template_text(raw_summary):
                summary = raw_summary
        
        # 3. Reddit帖子没有好摘要时，尝试从 description 或 media_content 获取
        if not summary and "description" in entry:
            raw_summary = clean_html(entry.get("description", ""))
            if not is_reddit_template_text(raw_summary):
                summary = raw_summary
        
        # 4. 尝试从 media_content 或 enclosure 获取额外信息
        if not summary:
            media_content = entry.get("media_content", [])
            if media_content and len(media_content) > 0:
                # 尝试获取媒体描述
                for mc in media_content:
                    if mc.get("description"):
                        summary = clean_html(mc["description"])
                        break
        
        # 5. Reddit帖子且没有好摘要时，尝试提取第一段正文
        if not summary and ("reddit" in source.name.lower() or "r/" in url):
            # 尝试从 title 中提取信息作为伪摘要
            # 跳过，因为 Reddit 标题通常已经包含了问题/内容
            pass

        # 提取热度分数
        score = extract_score(entry, source.name)

        # 质量过滤
        if not should_include_article(source.name, score, title, summary):
            continue

        published = parse_date(entry.get("published") or entry.get("updated") or "")

        # 使用升级后的分类器（传递title以提高准确性）
        tags = classify(summary, source.name, title)

        # 创建文章对象
        article = Article(
            title=title,
            url=url,
            summary=summary[:2000] if summary else "",
            source_name=source.name,
            source_url=source.url,
            author=entry.get("author", "").strip() or None,
            published_at=published,
            fetched_at=datetime.utcnow(),
            tags=tags,
            content_hash=content_hash,
            read_time_minutes=estimate_read_time(summary),
            score=score,
        )

        # 评审委员会自动评审
        # 高质量来源：如果摘要为空，传递标题作为评审依据
        try:
            committee = get_committee()
            # 高质量来源即使摘要为空也值得推荐
            review_text = summary if summary else title
            review_result = committee.review(
                article_id=None,
                title=title,
                text=review_text,
                source_name=source.name,
                published_at=published,
                url=url
            )

            # 高质量来源 + 摘要为空的情况：如果是 D 改成 C
            grade = review_result.grade
            if grade == 'D' and source.name in HIGH_QUALITY_SOURCES and not summary:
                grade = 'C'  # 降级处理但不直接过滤

            article.review_grade = grade
            article.review_score = int(review_result.total_score)
            article.review_result = review_result.to_dict()
            article.review_verdict = review_result.verdict
            article.reviewed_at = review_result.reviewed_at
        except Exception as e:
            # 评审失败不影响文章保存
            _safe_log(logging.WARNING, "Review failed for %s: %s", title[:30], str(e))

        articles.append(article)
        fetched_count += 1

        # 达到最大抓取数也停止
        if fetched_count >= max_articles:
            break

    db = SessionLocal()
    try:
        source.last_fetched = datetime.utcnow()
        db.commit()
    finally:
        db.close()

    return articles


def fetch_all_feeds() -> dict:
    """获取所有启用的订阅源。"""
    db = SessionLocal()
    try:
        sources = (
            db.query(FeedSource)
            .filter(FeedSource.enabled == True)
            .order_by(FeedSource.priority.desc())
            .all()
        )
    finally:
        db.close()

    total_added = 0
    total_seen = 0
    total_filtered = 0
    errors = []

    for source in sources:
        try:
            articles = fetch_feed(source)
            total_seen += len(articles)
            if articles:
                db = SessionLocal()
                try:
                    db.add_all(articles)
                    db.commit()
                    total_added += len(articles)
                    _safe_log(logging.INFO, "[%s] Added %d new articles", source.name, len(articles))
                except Exception as e:
                    db.rollback()
                    _safe_log(logging.ERROR, "DB error saving from %s: %s", source.name, str(e))
                finally:
                    db.close()
            else:
                _safe_log(logging.INFO, "[%s] No new articles (or all filtered)", source.name)
        except Exception as e:
            errors.append(f"{source.name}: {str(e)}")
            _safe_log(logging.ERROR, "Error fetching %s: %s", source.name, str(e))

        time.sleep(1)  # 避免请求过快

    return {
        "total_added": total_added,
        "total_seen": total_seen,
        "sources_count": len(sources),
        "errors": errors,
    }
