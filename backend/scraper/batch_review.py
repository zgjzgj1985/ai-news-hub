"""
批量评审脚本 - 使用LLM对历史文章进行评审

使用方法：
    python -m scraper.batch_review

注意：
    - 需要 Ollama 服务运行中
    - 需要已安装 qwen3:8b 模型
    - 会批量评审所有未评审的文章
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows 控制台编码设置
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from database import Article, SessionLocal
from review_committee import get_committee
from llm_client import get_llm_client


def check_llm_status():
    """检查LLM服务状态"""
    print("=" * 60)
    print("LLM Status Check")
    print("=" * 60)

    llm_client = get_llm_client()
    available = llm_client.is_available()

    if available:
        print(f"[OK] LLM Service: Connected")
        print(f"     Model: {llm_client.model}")
        print(f"     URL: {llm_client.base_url}")

        models = llm_client.list_models()
        print(f"     Installed models: {', '.join(models) if models else 'None'}")
    else:
        print(f"[FAIL] LLM Service: Unavailable")
        print(f"       Please ensure:")
        print(f"       1. Ollama is running (http://localhost:11434)")
        print(f"       2. Model qwen3:8b is installed: ollama pull qwen3:8b")
        print(f"       3. LLM_ENABLED=true in .env")
        return False

    return True


def get_review_stats():
    """获取评审统计"""
    db = SessionLocal()
    try:
        total = db.query(Article).count()
        reviewed = db.query(Article).filter(Article.review_grade.isnot(None)).count()
        pending = db.query(Article).filter(Article.review_grade.is_(None)).count()

        # 各评级统计
        grade_stats = {}
        for grade in ['A', 'B', 'C', 'D']:
            count = db.query(Article).filter(Article.review_grade == grade).count()
            grade_stats[grade] = count

        return {
            "total": total,
            "reviewed": reviewed,
            "pending": pending,
            "grade_stats": grade_stats
        }
    finally:
        db.close()


def print_stats(stats: dict):
    """打印统计信息"""
    print("\n" + "=" * 60)
    print("Review Statistics")
    print("=" * 60)
    print(f"Total articles:    {stats['total']}")
    print(f"Already reviewed: {stats['reviewed']}")
    print(f"Pending review:    {stats['pending']}")
    print(f"\nGrade distribution:")
    print(f"  A (Highly Recommended): {stats['grade_stats']['A']}")
    print(f"  B (Recommended):        {stats['grade_stats']['B']}")
    print(f"  C (Average):             {stats['grade_stats']['C']}")
    print(f"  D (Filtered):            {stats['grade_stats']['D']}")

    if stats['reviewed'] > 0:
        pass_rate = (stats['grade_stats']['A'] + stats['grade_stats']['B']) / stats['reviewed'] * 100
        print(f"\nPass rate (A+B): {pass_rate:.1f}%")


async def review_article(committee, article: Article) -> dict:
    """评审单篇文章"""
    try:
        result = await committee.areview(
            article_id=article.id,
            title=article.title,
            text=article.summary or "",
            source_name=article.source_name,
            published_at=article.published_at,
            url=article.url
        )
        return {
            "id": article.id,
            "title": article.title[:50],
            "grade": result.grade,
            "score": int(result.total_score),
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "id": article.id,
            "title": article.title[:50],
            "grade": None,
            "score": 0,
            "success": False,
            "error": str(e)
        }


async def batch_review_all(batch_size: int = 10, delay: float = 1.0):
    """
    批量评审所有未评审的文章

    参数:
        batch_size: 每批评审的文章数量
        delay: 每篇文章评审间隔（秒）
    """
    print("\n" + "=" * 60)
    print("Start Batch Review")
    print("=" * 60)

    committee = get_committee()
    db = SessionLocal()

    try:
        # 获取所有未评审的文章
        articles = db.query(Article).filter(
            Article.review_grade.is_(None)
        ).order_by(Article.fetched_at.desc()).all()

        total = len(articles)
        print(f"Articles to review: {total}")
        print(f"Batch size: {batch_size}")
        print(f"Delay between articles: {delay}s")

        if total == 0:
            print("\n[OK] No pending articles!")
            return

        # 统计
        success_count = 0
        fail_count = 0
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        start_time = time.time()
        results = []

        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{total}] Reviewing: {article.title[:40]}...", end=" ", flush=True)

            result = await review_article(committee, article)

            if result["success"]:
                # 更新数据库
                article.review_grade = result["grade"]
                article.review_score = result["score"]
                article.review_verdict = f"[LLM Review] Grade {result['grade']}"
                article.reviewed_at = time.strftime("%Y-%m-%d %H:%M:%S")
                db.commit()

                success_count += 1
                if result["grade"] in grade_counts:
                    grade_counts[result["grade"]] += 1

                print(f"[OK] {result['grade']} ({result['score']} pts)")
            else:
                db.rollback()
                fail_count += 1
                print(f"[FAIL] {result['error'][:50]}")

            # 添加间隔，避免请求过快
            if i < total:
                await asyncio.sleep(delay)

        # 打印结果
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Batch Review Completed")
        print("=" * 60)
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Success: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"\nGrade distribution:")
        print(f"  A (Highly Recommended): {grade_counts['A']}")
        print(f"  B (Recommended):        {grade_counts['B']}")
        print(f"  C (Average):             {grade_counts['C']}")
        print(f"  D (Filtered):            {grade_counts['D']}")

        if success_count > 0:
            pass_rate = (grade_counts['A'] + grade_counts['B']) / success_count * 100
            print(f"\nPass rate (A+B): {pass_rate:.1f}%")

    finally:
        db.close()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI Info Station - LLM Batch Review Script")
    print("=" * 60)

    # 检查LLM状态
    if not check_llm_status():
        print("\n[FAIL] LLM service unavailable, cannot review")
        sys.exit(1)

    # 打印当前统计
    stats = get_review_stats()
    print_stats(stats)

    if stats["pending"] == 0:
        print("\n[OK] All articles have been reviewed!")
        return

    # 开始批量评审
    print("\n")
    response = input(f"Start reviewing {stats['pending']} pending articles? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # 运行批量评审
    asyncio.run(batch_review_all(batch_size=10, delay=0.5))


if __name__ == "__main__":
    main()
