"""
清理 D 级垃圾内容脚本

删除所有 review_grade = 'D' 的文章，这些是不符合标准的垃圾信息
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, Article, Bookmark

def cleanup_grade_d():
    db = SessionLocal()

    # 统计将要删除的数量
    d_articles = db.query(Article).filter(Article.review_grade == 'D').all()
    d_count = len(d_articles)
    print(f"发现 {d_count} 篇 D 级垃圾内容")

    if d_count == 0:
        print("没有需要清理的内容")
        db.close()
        return

    # 先删除关联的书签
    d_ids = [a.id for a in d_articles]
    bookmarks_deleted = db.query(Bookmark).filter(Bookmark.article_id.in_(d_ids)).delete(synchronize_session=False)
    print(f"删除 {bookmarks_deleted} 个关联书签")

    # 删除文章
    deleted = db.query(Article).filter(Article.review_grade == 'D').delete(synchronize_session=False)
    db.commit()

    print(f"已删除 {deleted} 篇 D 级垃圾内容")

    # 统计剩余内容
    remaining_a = db.query(Article).filter(Article.review_grade == 'A').count()
    remaining_b = db.query(Article).filter(Article.review_grade == 'B').count()
    remaining_c = db.query(Article).filter(Article.review_grade == 'C').count()
    remaining_d = db.query(Article).filter(Article.review_grade == 'D').count()
    total = db.query(Article).count()

    print(f"\n清理后统计:")
    print(f"  A级: {remaining_a} 篇")
    print(f"  B级: {remaining_b} 篇")
    print(f"  C级: {remaining_c} 篇")
    print(f"  D级: {remaining_d} 篇 (应为 0)")
    print(f"  总计: {total} 篇")

    db.close()
    print("\n清理完成!")

if __name__ == "__main__":
    cleanup_grade_d()
