"""
清理数据库中的乱码数据。

运行方式：python clean_corrupted_data.py
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Article
from datetime import datetime

# 乱码模式检测
CORRUPTION_PATTERNS = [
    r'\?{2,}',           # 多个连续问号
    r'[\ufffd]{2,}',     # Unicode替换字符
    r'\xa0+',            # 不间断空格
    r'[\x00-\x08\x0b\x0c\x0e-\x1f]',  # 控制字符
]


def contains_corruption(text: str) -> bool:
    """检测文本是否包含乱码字符。"""
    if not text:
        return False
    
    # 检查是否有大量无法识别的字符
    unknown_count = sum(1 for c in text if ord(c) > 0xFFFD)
    if unknown_count > len(text) * 0.1:  # 超过10%的乱码字符
        return True
    
    # 检查是否包含控制字符（排除常见的换行和回车）
    control_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    if control_pattern.search(text):
        return True
    
    return False


def fix_encoding(text: str) -> str:
    """尝试修复编码问题。"""
    if not text:
        return text
    
    # 替换常见的乱码字符
    text = text.replace('\ufffd', '')  # Unicode替换字符
    text = text.replace('\xa0', ' ')    # 不间断空格
    text = re.sub(r'\s+', ' ', text)   # 规范化空白
    
    return text.strip()


def clean_articles():
    """清理数据库中的乱码数据。"""
    db = SessionLocal()
    
    try:
        # 获取所有文章
        articles = db.query(Article).all()
        
        cleaned_count = 0
        deleted_count = 0
        skipped_count = 0
        
        for article in articles:
            needs_update = False
            fields_to_check = [
                ('title', '标题'),
                ('summary', '摘要'),
                ('author', '作者'),
                ('source_name', '来源名称'),
            ]
            
            for field, field_name in fields_to_check:
                value = getattr(article, field, None)
                if value and contains_corruption(value):
                    fixed = fix_encoding(value)
                    if fixed != value:
                        setattr(article, field, fixed)
                        needs_update = True
            
            # 检查标题是否太短（可能是乱码导致的）
            if article.title and len(article.title.strip()) < 5:
                # 删除标题太短的文章
                db.delete(article)
                deleted_count += 1
                continue
            
            # 检查标签是否包含乱码
            if article.tags:
                cleaned_tags = []
                for tag in article.tags:
                    if tag and not contains_corruption(tag):
                        cleaned_tags.append(tag)
                    else:
                        cleaned_tags.append("AI前沿")  # 默认标签
                
                if cleaned_tags != article.tags:
                    article.tags = cleaned_tags
                    needs_update = True
            
            if needs_update:
                cleaned_count += 1
        
        db.commit()
        
        print(f"\n{'='*50}")
        print(f"数据清理完成！")
        print(f"  - 修复的文章: {cleaned_count}")
        print(f"  - 删除的文章: {deleted_count}")
        print(f"  - 跳过的文章: {skipped_count}")
        print(f"{'='*50}")
        
    except Exception as e:
        db.rollback()
        print(f"清理失败: {e}")
        raise
    finally:
        db.close()


def show_stats():
    """显示数据统计。"""
    db = SessionLocal()
    
    try:
        total = db.query(Article).count()
        corrupted_titles = 0
        corrupted_summaries = 0
        empty_summaries = 0
        
        for article in db.query(Article).all():
            if article.title and contains_corruption(article.title):
                corrupted_titles += 1
            if article.summary:
                if contains_corruption(article.summary):
                    corrupted_summaries += 1
                if len(article.summary.strip()) < 20:
                    empty_summaries += 1
            elif not article.summary:
                empty_summaries += 1
        
        print(f"\n{'='*50}")
        print(f"数据库统计：")
        print(f"  - 总文章数: {total}")
        print(f"  - 标题乱码: {corrupted_titles}")
        print(f"  - 摘要乱码: {corrupted_summaries}")
        print(f"  - 空/短摘要: {empty_summaries}")
        print(f"{'='*50}\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n开始数据清理...\n")
    show_stats()
    clean_articles()
    show_stats()
