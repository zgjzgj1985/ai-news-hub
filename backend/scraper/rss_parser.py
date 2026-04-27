"""RSS parser for fetching and parsing feed entries with quality filtering."""

import asyncio
import hashlib
import logging
import re
import time
import chardet
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from database import Article, FeedSource, SessionLocal
from scraper.classifier import classify, is_academic_content
from scraper.sources import is_academic_source, requires_code
from review_committee import get_committee

logger = logging.getLogger(__name__)

# 最大重试次数
MAX_RETRIES = 3
# 重试间隔（秒）
RETRY_DELAY = 2
# 请求超时（秒）
FETCH_TIMEOUT = 30
# 连接超时（秒）
CONNECT_TIMEOUT = 10

# 需要从原网页抓取摘要的来源列表（这些源的 RSS 不提供摘要）
SOURCES_NEED_PAGE_FETCH = [
    "Hugging Face Blog",
    "OpenAI Blog",
    "Anthropic Blog",
    "Google DeepMind Blog",
    "Meta AI Blog",
    "Mistral AI Blog",
    "Stability AI Blog",
    "Windsurf Blog",
    "GitHub Blog",
    "Cursor Blog (社区RSS)",
]


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


# ============ 常量定义 ============

# 来源特定的质量阈值
SOURCE_QUALITY_THRESHOLDS = {
    "Hacker News AI": 30,
    "Reddit r/LocalLLaMA": 20,
    "Reddit r/StableDiffusion": 20,
    "AI Stack Exchange": 5,
}

# 每个源每天最多抓取的文章数
SOURCE_DAILY_LIMITS = {
    # 高质量博客
    "Hugging Face Blog": 30,
    "OpenAI Blog": 30,
    "Anthropic Blog": 30,
    "Google DeepMind Blog": 20,
    "Meta AI Blog": 20,
    "Stability AI Blog": 20,
    "Mistral AI Blog": 20,
    "机器之心": 30,
    "量子位": 30,
    # 新闻/社区
    "Hacker News AI": 20,
    "MIT Technology Review": 20,
    "The Verge AI": 20,
    "Game Developer": 20,
    "AI Stack Exchange": 20,
    # 学术来源
    "ArXiv cs.AI": 20,
    "ArXiv cs.CV (视觉)": 20,
    "Papers with Code": 15,
    # Reddit
    "r/LocalLLaMA": 15,
    "r/StableDiffusion": 10,
    "r/ComfyUI": 15,
    "r/GameAI": 15,
    # Vibe Coding
    "Windsurf Blog": 20,
    "GitHub Blog": 25,
    "Cursor Blog (社区RSS)": 25,
    # 默认
    "_default": 20,
}

# 中文AI媒体的RSS源
CHINESE_AI_FEEDS = ["机器之心", "量子位", "36氪", "雷锋网", "爱范儿"]

# 高质量来源列表
HIGH_QUALITY_SOURCES = [
    "OpenAI Blog", "Hugging Face Blog", "Anthropic Blog", "Google DeepMind Blog",
    "Meta AI Blog", "Mistral AI Blog", "Stability AI Blog",
    "The Batch", "Import AI",
    "机器之心", "量子位",
    "AI Stack Exchange", "Data Stack Exchange",
    "Windsurf Blog", "GitHub Blog", "Cursor Blog (社区RSS)",
]

# 无意义标题模式
MEANINGLESS_TITLE_PATTERNS = [
    r"^close\??$",
    r"^question\??$",
    r"^help\??$",
    r"^\[?deleted\]?$",
    r"^\[?removed\]?$",
    r"^快讯：",
    r"^今日热词：",
    r"^今日要闻：",
]

# Hacker News AI 关键词
HN_AI_KEYWORDS = [
    "ai", "ml", "machine learning", "deep learning", "neural", "llm", "gpt", "claude", "gemini",
    "transformer", "diffusion", "stable diffusion", "openai", "anthropic", "hugging face",
    "langchain", "rag", "embedding", "fine-tuning", "rlhf", "agent", "copilot", "cursor",
    "midjourney", "sora", "dall-e", "flux", "comfyui", "lora", "controlnet",
    "github", "open source", "framework", "library", "api", "sdk", "cli",
    "python", "javascript", "typescript", "rust", "golang",
    "cursor", "windsurf", "copilot", "codeium", "tabnine",
    "v0", "bolt", "lovable", "replit", "perplexity",
]


# ============ 辅助函数 ============

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
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000]


def is_reddit_template_text(text: str) -> bool:
    """检测是否为Reddit的模板文本"""
    if not text:
        return True
    reddit_patterns = [
        r"submitted by\s*/?u/\w+",
        r"\[link\]\s*\[comments\]",
        r"View more community posts",
        r"^[\s\n]*$",
    ]
    text_lower = text.lower()
    for pattern in reddit_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    if len(text.strip()) < 30:
        return True
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
    """从RSS条目中提取热度评分"""
    score = None
    if hasattr(entry, 'score'):
        score = entry.get('score')
    elif 'score' in entry:
        score = entry.get('score')
    if hasattr(entry, 'reddit_score'):
        score = entry.get('reddit_score')
    if score is not None:
        if isinstance(score, str):
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

    # 检查无意义标题
    for pattern in MEANINGLESS_TITLE_PATTERNS:
        if re.match(pattern, title_lower, re.IGNORECASE):
            return False

    # 标题太短
    if len(title.strip()) < 5:
        return False

    # 学术来源必须代码/实战
    if is_academic_source(source_name):
        code_indicators = [
            "github", "code", "implementation",
            "tutorial", "example", "demo",
            "实战", "案例", "case study", "how to",
            "notebook", "colab", "jupyter",
        ]
        has_code = any(indicator in combined_text for indicator in code_indicators)
        if not has_code:
            return False

    # 高质量来源直接收录
    if source_name in HIGH_QUALITY_SOURCES:
        return True

    # Hacker News AI 必须包含AI相关关键词
    if source_name == "Hacker News AI":
        has_ai_keyword = any(kw in combined_text for kw in HN_AI_KEYWORDS)
        if not has_ai_keyword:
            return False
        if score is not None and score < 15:
            return False

    # Reddit 需要高分数或有实质性摘要
    if "reddit" in title_lower or "/r/" in title:
        if score is not None and score < 15:
            return False
        if is_reddit_template_text(summary):
            return False

    # 一般来源检查内容长度
    if len(combined_text.strip()) < 30:
        return False

    # 检查推广/垃圾内容
    spam_patterns = [
        "sponsored by",
        "[promoted]",
        "[sponsor]",
        "buy now",
        "click here",
        "casino",
    ]
    for pattern in spam_patterns:
        if pattern in title_lower:
            return False

    return True


def _is_feed_url_valid(url: str) -> tuple[bool, str]:
    """
    检查 feed URL 是否有效。

    返回: (是否有效, 错误信息)
    """
    if not url:
        return False, "URL为空"

    # 检查 URL 格式
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, f"无效的URL格式: {url}"
    except Exception as e:
        return False, f"URL解析失败: {str(e)}"

    # 检查是否是支持的协议
    if result.scheme not in ('http', 'https'):
        return False, f"不支持的协议: {result.scheme}"

    return True, ""


def _fetch_page_summary(url: str) -> str:
    """
    从原网页抓取摘要。

    适用于 RSS 不提供摘要的来源（如 Hugging Face Blog、OpenAI Blog 等）。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    }

    try:
        response = requests.get(url, headers=headers, timeout=(CONNECT_TIMEOUT, FETCH_TIMEOUT))
        response.raise_for_status()

        # 解析 HTML
        soup = BeautifulSoup(response.content, "lxml")

        # 尝试提取 meta 描述
        meta_desc = None

        # Open Graph 描述
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            meta_desc = og_desc.get("content", "")

        # Twitter 描述
        if not meta_desc:
            twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
            if twitter_desc:
                meta_desc = twitter_desc.get("content", "")

        # 标准 meta 描述
        if not meta_desc:
            meta_desc_tag = soup.find("meta", attrs={"name": "description"})
            if meta_desc_tag:
                meta_desc = meta_desc_tag.get("content", "")

        if meta_desc:
            return meta_desc.strip()[:500]

        # 尝试提取文章正文的前几段
        article = soup.find("article") or soup.find("main") or soup.find("div", class_=lambda x: x and "content" in x.lower() if x else False)

        if article:
            paragraphs = article.find_all("p")
            if paragraphs:
                text_parts = []
                for p in paragraphs[:5]:
                    text = p.get_text(strip=True)
                    if len(text) > 50:
                        text_parts.append(text)
                    if sum(len(t) for t in text_parts) > 300:
                        break
                if text_parts:
                    return " ".join(text_parts)[:500]

        return ""

    except Exception as e:
        _safe_log(logging.WARNING, "Failed to fetch page summary for %s: %s", url[:50], str(e))
        return ""


def _fetch_with_retry(source: FeedSource) -> Optional[str]:
    """
    带重试的 feed 获取。
    
    参数:
        source: FeedSource 对象
        
    返回:
        feed 内容字符串，失败返回 None
    """
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
    
    last_error = ""
    
    for attempt in range(MAX_RETRIES):
        try:
            # 使用 session 支持连接复用
            response = requests.get(
                source.url, 
                headers=headers, 
                timeout=(CONNECT_TIMEOUT, FETCH_TIMEOUT),
                allow_redirects=True,
                stream=False
            )
            
            # 检查 HTTP 状态码
            if response.status_code == 404:
                last_error = f"404 Not Found"
                # 404 不重试
                break
                
            if response.status_code >= 500:
                last_error = f"Server Error: {response.status_code}"
                # 服务器错误，短暂等待后重试
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                continue
                
            if response.status_code >= 400:
                last_error = f"Client Error: {response.status_code}"
                # 客户端错误，不重试
                break
                
            response.raise_for_status()
            
            # 使用智能解码处理编码问题
            content = _safe_decode(response.content)
            return content
            
        except requests.exceptions.Timeout:
            last_error = f"请求超时 (尝试 {attempt + 1}/{MAX_RETRIES})"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                
        except requests.exceptions.ConnectionError as e:
            last_error = f"连接错误: {str(e)[:50]}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                
        except requests.exceptions.RequestException as e:
            last_error = f"请求异常: {str(e)[:50]}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                
        except Exception as e:
            last_error = f"未知错误: {str(e)[:50]}"
            break
    
    _safe_log(logging.ERROR, "Failed to fetch %s after %d attempts: %s", source.name, MAX_RETRIES, last_error)
    return None


def fetch_feed(source: FeedSource, max_articles: int = 50) -> list[Article]:
    """
    获取单个订阅源的文章列表。

    改进点：
    1. 提取并记录热度分数
    2. 基于质量阈值过滤
    3. 每个源限制每日抓取数量
    4. 容错处理：重试机制、超时处理、编码问题
    """
    articles = []
    fetched_count = 0

    # 获取当天的文章数量限制
    daily_limit = SOURCE_DAILY_LIMITS.get(source.name, SOURCE_DAILY_LIMITS.get("_default", 20))

    # 检查 URL 有效性
    is_valid, error_msg = _is_feed_url_valid(source.url)
    if not is_valid:
        _safe_log(logging.WARNING, "[%s] Invalid feed URL: %s", source.name, error_msg)
        return []

    # 加载已存在的文章（用于去重）
    db = SessionLocal()
    try:
        existing_hashes = {
            row[0]
            for row in db.query(Article.content_hash).filter(Article.content_hash.isnot(None)).all()
        }
        existing_urls = {row[0] for row in db.query(Article.url).all()}
    except Exception as e:
        _safe_log(logging.WARNING, "[%s] Failed to load existing articles: %s", source.name, str(e))
        existing_hashes = set()
        existing_urls = set()
    finally:
        db.close()

    # 带重试的 feed 获取
    content = _fetch_with_retry(source)
    
    if content is None:
        _safe_log(logging.WARNING, "No content from %s (after retries)", source.name)
        return []

    try:
        feed = feedparser.parse(content)
    except Exception as e:
        _safe_log(logging.ERROR, "Failed to parse feed %s: %s", source.name, str(e))
        return []

    if not feed.entries:
        # 检查是否是解析问题
        if feed.bozo:
            _safe_log(logging.WARNING, "[%s] Feed has issues (bozo), but may still have entries", source.name)
        else:
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

        # 5. 如果仍然没有摘要，且来源需要从网页抓取
        if not summary and source.name in SOURCES_NEED_PAGE_FETCH:
            article_url = url.strip()
            summary = _fetch_page_summary(article_url)
            if summary:
                _safe_log(logging.INFO, "[%s] Fetched summary from page for: %s", source.name, title[:40])
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
    """
    获取所有启用的订阅源。
    
    容错处理：
    1. 单个源失败不影响其他源
    2. 跳过无效 URL
    3. 详细记录错误
    """
    db = SessionLocal()
    try:
        sources = (
            db.query(FeedSource)
            .filter(FeedSource.enabled == True)
            .order_by(FeedSource.priority.desc())
            .all()
        )
    except Exception as e:
        _safe_log(logging.ERROR, "Failed to load feed sources: %s", str(e))
        db.close()
        return {
            "total_added": 0,
            "total_seen": 0,
            "sources_count": 0,
            "errors": [f"数据库错误: {str(e)}"],
        }
    finally:
        # 注意：这里会在 return 之前执行
        pass
    
    total_added = 0
    total_seen = 0
    total_skipped = 0
    errors = []
    skipped_reasons = []
    
    # 按优先级分组，先处理高质量源
    high_priority = [s for s in sources if s.priority >= 5]
    normal_priority = [s for s in sources if s.priority < 5]
    
    all_sources = high_priority + normal_priority
    
    for source in all_sources:
        # 跳过无效 URL
        is_valid, error_msg = _is_feed_url_valid(source.url)
        if not is_valid:
            total_skipped += 1
            skipped_reasons.append(f"{source.name}: {error_msg}")
            _safe_log(logging.WARNING, "[SKIP] %s - %s", source.name, error_msg)
            continue
        
        try:
            articles = fetch_feed(source)
            total_seen += len(articles)
            
            if articles:
                db = SessionLocal()
                try:
                    db.add_all(articles)
                    db.commit()
                    total_added += len(articles)
                    _safe_log(logging.INFO, "[OK] [%s] Added %d articles", source.name, len(articles))
                except Exception as e:
                    db.rollback()
                    error = f"{source.name}: 数据库保存失败 - {str(e)[:50]}"
                    errors.append(error)
                    _safe_log(logging.ERROR, "[ERROR] %s", error)
                finally:
                    db.close()
            else:
                _safe_log(logging.INFO, "[EMPTY] [%s] No new articles", source.name)
                
        except Exception as e:
            error = f"{source.name}: {str(e)[:100]}"
            errors.append(error)
            _safe_log(logging.ERROR, "[ERROR] Fetch failed for %s: %s", source.name, str(e))

        # 请求间隔
        time.sleep(0.5)

    db.close()
    
    result = {
        "total_added": total_added,
        "total_seen": total_seen,
        "sources_count": len(sources),
        "sources_skipped": total_skipped,
        "errors": errors,
    }
    
    if skipped_reasons:
        result["skipped_reasons"] = skipped_reasons
    
    return result
