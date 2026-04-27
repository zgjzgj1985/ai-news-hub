"""
批量重新评审脚本 - 使用新的游戏开发者评审标准

对数据库中的所有未评审或需要重新评审的文章进行批量评审
"""
import sys
sys.path.insert(0, '.')

import asyncio
from datetime import datetime
from database import SessionLocal, Article
from review_committee import ReviewCommittee


def regrade_all_articles():
    """重新评审所有文章"""
    db = SessionLocal()

    # 获取所有文章
    articles = db.query(Article).all()
    print(f"共有 {len(articles)} 篇文章需要重新评审")

    committee = ReviewCommittee()

    results = {"A": 0, "B": 0, "C": 0, "D": 0}
    errors = []

    for i, article in enumerate(articles):
        try:
            print(f"\n[{i+1}/{len(articles)}] 评审: {article.title[:50]}...")

            # 构建文本内容
            text = f"{article.title} {article.summary or ''}"

            # 执行评审
            result = committee.review(
                article_id=article.id,
                title=article.title,
                text=text,
                source_name=article.source_name,
                published_at=article.published_at,
                url=article.url
            )

            # 更新文章
            old_grade = article.review_grade
            article.review_grade = result.grade
            article.review_score = int(result.total_score * 10)
            article.review_result = result.to_dict()
            article.review_verdict = result.verdict
            article.reviewed_at = datetime.utcnow()

            results[result.grade] += 1
            print(f"  {old_grade or '?'} -> {result.grade} (分数: {result.total_score:.1f})")

            # 每10篇提交一次
            if (i + 1) % 10 == 0:
                db.commit()
                print(f"\n已提交 {i+1} 篇...")

        except Exception as e:
            errors.append(f"{article.title[:30]}: {str(e)}")
            print(f"  错误: {str(e)[:50]}")

    # 最终提交
    db.commit()
    db.close()

    # 输出统计
    print("\n" + "="*50)
    print("重新评审完成！")
    print("="*50)
    print(f"评审结果统计:")
    print(f"  A级 (强烈推荐): {results['A']} 篇")
    print(f"  B级 (推荐):     {results['B']} 篇")
    print(f"  C级 (一般):     {results['C']} 篇")
    print(f"  D级 (过滤):     {results['D']} 篇")
    print(f"  总计:           {sum(results.values())} 篇")

    if errors:
        print(f"\n错误数量: {len(errors)}")
        for err in errors[:5]:
            print(f"  - {err}")

    # 计算优质率
    total = sum(results.values())
    if total > 0:
        quality_rate = (results['A'] + results['B']) / total * 100
        print(f"\n优质内容率: {quality_rate:.1f}% (A+B级占比)")


if __name__ == "__main__":
    regrade_all_articles()
