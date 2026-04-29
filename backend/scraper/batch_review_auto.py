"""
LLM批量评审脚本 - 自动执行版本

直接运行，不等待确认
"""

import asyncio
import sys
import time
from datetime import datetime
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

    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        available = response.status_code == 200
    except:
        available = False

    if available:
        print(f"[OK] LLM Service: Connected")
        print(f"     Model: qwen3.5:9b (configured)")
        print(f"     URL: http://localhost:11434")
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        print(f"     Installed models: {', '.join(models) if models else 'None'}")
        return True
    else:
        print(f"[FAIL] LLM Service: Unavailable")
        return False


def get_stats():
    """获取统计"""
    db = SessionLocal()
    try:
        total = db.query(Article).count()
        reviewed = db.query(Article).filter(Article.review_grade.isnot(None)).count()
        pending = db.query(Article).filter(Article.review_grade.is_(None)).count()

        grade_stats = {}
        for grade in ['A', 'B', 'C', 'D']:
            count = db.query(Article).filter(Article.review_grade == grade).count()
            grade_stats[grade] = count

        return {"total": total, "reviewed": reviewed, "pending": pending, "grade_stats": grade_stats}
    finally:
        db.close()


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


async def batch_review_all(batch_size: int = 10, delay: float = 0.5):
    """批量评审所有未评审的文章"""
    print("\n" + "=" * 60)
    print("Start Batch Review")
    print("=" * 60)

    committee = get_committee()
    db = SessionLocal()

    try:
        articles = db.query(Article).filter(
            Article.review_grade.is_(None)
        ).order_by(Article.fetched_at.desc()).all()

        total = len(articles)
        print(f"Articles to review: {total}")
        print(f"Batch size: {batch_size}")
        print(f"Delay between articles: {delay}s")
        print("-" * 60)

        if total == 0:
            print("\n[OK] No pending articles!")
            return

        success_count = 0
        fail_count = 0
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        start_time = time.time()

        for i, article in enumerate(articles, 1):
            print(f"[{i}/{total}] {article.title[:45]}...", end=" ", flush=True)

            result = await review_article(committee, article)

            if result["success"]:
                article.review_grade = result["grade"]
                article.review_score = result["score"]
                article.review_verdict = f"[LLM] Grade {result['grade']}"
                article.reviewed_at = datetime.utcnow()
                db.commit()

                success_count += 1
                if result["grade"] in grade_counts:
                    grade_counts[result["grade"]] += 1

                print(f"[OK] {result['grade']} ({result['score']})")
            else:
                db.rollback()
                fail_count += 1
                print(f"[FAIL] {result['error'][:40]}")

            if i < total:
                await asyncio.sleep(delay)

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Batch Review Completed")
        print("=" * 60)
        print(f"Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"Success: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"\nGrade distribution:")
        print(f"  A (Highly Recommended): {grade_counts['A']}")
        print(f"  B (Recommended):        {grade_counts['B']}")
        print(f"  C (Average):            {grade_counts['C']}")
        print(f"  D (Filtered):           {grade_counts['D']}")

        if success_count > 0:
            pass_rate = (grade_counts['A'] + grade_counts['B']) / success_count * 100
            print(f"\nPass rate (A+B): {pass_rate:.1f}%")

    finally:
        db.close()


def main():
    print("\n" + "=" * 60)
    print("AI Info Station - LLM Batch Review")
    print("=" * 60)

    if not check_llm_status():
        print("\n[FAIL] LLM unavailable, cannot review")
        sys.exit(1)

    stats = get_stats()
    print("\nCurrent Stats:")
    print(f"  Total: {stats['total']}")
    print(f"  Already reviewed: {stats['reviewed']}")
    print(f"  Pending: {stats['pending']}")

    if stats["pending"] == 0:
        print("\n[OK] All articles reviewed!")
        return

    print(f"\nStarting review of {stats['pending']} articles...")
    asyncio.run(batch_review_all(batch_size=10, delay=0.5))


if __name__ == "__main__":
    main()
