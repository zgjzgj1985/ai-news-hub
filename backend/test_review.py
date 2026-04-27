"""评审委员会测试脚本 - 验证评审功能是否正常工作"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from review_committee import ReviewCommittee, ReviewResult

# 测试用例
test_cases = [
    {
        "name": "高质量AI工具发布",
        "title": "Cursor AI 推出新版代码生成功能，支持多文件编辑",
        "text": """
        Cursor 宣布推出全新的 AI 编程助手功能。

        主要特性：
        1. 支持同时编辑多个文件
        2. 智能代码补全
        3. GitHub 集成
        4. 支持自定义工作流

        安装方式：pip install cursor-ai
        GitHub 地址：https://github.com/cursor-ai/cursor

        教程：https://cursor.com/docs/tutorial
        """,
        "source": "Cursor Official",
        "age_days": 3
    },
    {
        "name": "游戏美术工具",
        "title": "Stable Diffusion 游戏角色 LoRA 模型分享",
        "text": """
        分享一个我训练的游戏角色 LoRA 模型。

        模型下载：https://civitai.com/models/game-character-lora
        配置文件：config.yaml

        使用方法：
        1. 下载模型文件
        2. 放入 models/Lora 目录
        3. 使用提示词调用

        prompt 示例：[game character:1.2], detailed, high quality
        """,
        "source": "CivitAI",
        "age_days": 7
    },
    {
        "name": "过时的AI新闻",
        "title": "GPT-4 终于发布！全新功能抢先看",
        "text": "OpenAI 发布了 GPT-4 模型，支持多模态功能。这是一个重大更新...",
        "source": "机器之心",
        "age_days": 180  # 6个月前
    },
    {
        "name": "低质量搬运内容",
        "title": "原标题：Amazing AI Tool - Must See!",
        "text": """
        点击这里订阅我们的频道！
        Buy now for only $9.99!

        Follow us on Instagram: @ai_news
        """,
        "source": "Random Blog",
        "age_days": 5
    },
    {
        "name": "AI相关但无实用价值",
        "title": "AI 会取代程序员吗？",
        "text": """
        最近很多人都在讨论 AI 是否会取代程序员。

        有人认为 AI 会取代程序员，也有人认为不会。

        你觉得呢？欢迎在评论区留言！
        """,
        "source": "科技媒体",
        "age_days": 2
    }
]


def run_tests():
    print("=" * 60)
    print("评审委员会测试")
    print("=" * 60)

    committee = ReviewCommittee()

    for i, case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】{case['name']}")
        print(f"标题：{case['title'][:50]}...")
        print(f"来源：{case['source']} | 发布时间：{case['age_days']}天前")
        print("-" * 40)

        # 计算发布时间
        from datetime import datetime, timedelta
        published_at = datetime.utcnow() - timedelta(days=case['age_days'])

        result = committee.review(
            article_id=None,
            title=case['title'],
            text=case['text'],
            source_name=case['source'],
            published_at=published_at,
            url=""
        )

        print(f"【最终评级】{result.grade}")
        print(f"【综合分数】{result.total_score:.1f}/50")
        print(f"【裁决】{result.verdict}")
        print()
        print("各评委投票：")

        for vote_attr in ['relevance_vote', 'practicality_vote', 'timeliness_vote',
                          'depth_vote', 'originality_vote']:
            vote = getattr(result, vote_attr)
            if vote:
                emoji = {
                    'approve': '✅',
                    'weak': '⚠️',
                    'reject': '❌'
                }.get(vote.result.value, '❓')
                print(f"  {emoji} {vote.judge_alias}: {vote.score:.1f}分 - {vote.reason[:40]}...")

        print("-" * 40)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
