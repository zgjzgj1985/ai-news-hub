"""测试 LLM 评审功能"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import get_llm_client
from review_committee import ReviewCommittee
from prompts import build_review_prompt, parse_review_result


def test_llm_connection():
    """测试LLM连接"""
    print("=" * 60)
    print("测试 1: LLM连接")
    print("=" * 60)

    client = get_llm_client()

    if client.is_available():
        print(f"✓ LLM服务可用")
        print(f"  - 模型: {client.model}")
        print(f"  - 地址: {client.base_url}")

        models = client.list_models()
        print(f"  - 已安装模型: {models}")
    else:
        print("✗ LLM服务不可用")
        print("  请确保 Ollama 服务正在运行")
        return False

    return True


async def test_llm_chat():
    """测试LLM对话"""
    print("\n" + "=" * 60)
    print("测试 2: LLM对话")
    print("=" * 60)

    client = get_llm_client()

    try:
        messages = [
            {"role": "user", "content": "请用一句话介绍自己"}
        ]
        response = await client.chat(messages, json_mode=False)
        print(f"✓ LLM响应: {response[:200]}...")
        return True
    except Exception as e:
        print(f"✗ LLM对话失败: {e}")
        return False


async def test_review_prompt():
    """测试评审提示词构建"""
    print("\n" + "=" * 60)
    print("测试 3: 评审提示词")
    print("=" * 60)

    title = "Qwen3: 最强大的开源大语言模型发布"
    summary = "阿里巴巴发布Qwen3系列模型，支持128K上下文，在多项基准测试中超越GPT-4..."
    source = "Hugging Face"

    prompts = build_review_prompt(title, summary, source)

    print(f"✓ 系统提示词长度: {len(prompts['system'])} 字符")
    print(f"✓ 用户提示词预览:")
    print(f"  {prompts['user'][:200]}...")

    return True


async def test_llm_review():
    """测试LLM评审"""
    print("\n" + "=" * 60)
    print("测试 4: LLM评审")
    print("=" * 60)

    client = get_llm_client()

    title = "Cursor AI: 下一代代码编辑器实战指南"
    summary = """
    本文详细介绍如何使用Cursor AI提升开发效率。

    主要内容：
    1. Cursor基础配置
    2. AI代码补全技巧
    3. 自然语言编程实战
    4. Git集成与团队协作

    包含完整示例代码和最佳实践。
    """
    source = "Dev.to"

    try:
        prompts = build_review_prompt(title, summary, source)

        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]}
        ]

        print("正在调用LLM评审...")
        response = await client.chat(messages, json_mode=True)

        print(f"\n原始响应:\n{response[:500]}...")

        parsed = parse_review_result(response)

        print(f"\n解析结果:")
        print(f"  - 评级: {parsed.get('grade')}")
        print(f"  - 分数: {parsed.get('scores')}")
        print(f"  - 裁决: {parsed.get('verdict')}")
        print(f"  - 推荐: {parsed.get('recommendation')}")

        return True

    except Exception as e:
        print(f"✗ LLM评审失败: {e}")
        return False


async def test_review_committee():
    """测试评审委员会"""
    print("\n" + "=" * 60)
    print("测试 5: 评审委员会")
    print("=" * 60)

    committee = ReviewCommittee()

    print(f"LLM启用: {committee._use_llm}")
    print(f"LLM可用: {committee.is_llm_available()}")

    article = type('Article', (), {
        'id': 1,
        'title': 'Stable Diffusion 3 发布：革命性的图像生成模型',
        'summary': 'Stability AI 发布 SD3，采用新的架构设计...',
        'source_name': 'Stability AI Blog',
        'published_at': None,
        'url': 'https://stability.ai/sd3'
    })

    try:
        result = await committee.areview(
            article_id=article.id,
            title=article.title,
            text=article.summary,
            source_name=article.source_name,
            published_at=article.published_at,
            url=article.url
        )

        print(f"\n评审结果:")
        print(f"  - 评级: {result.grade}")
        print(f"  - 总分: {result.total_score}")
        print(f"  - LLM评审: {result.llm_reviewed}")
        print(f"  - 裁决: {result.verdict}")

        if result.llm_scores:
            print(f"  - LLM分数: {result.llm_scores}")

        return True

    except Exception as e:
        print(f"✗ 评审失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LLM评审委员会测试")
    print("=" * 60 + "\n")

    results = []

    # 测试1: LLM连接
    if test_llm_connection():
        results.append(("LLM连接", True))

        # 如果连接成功，继续其他测试
        results.append(("LLM对话", await test_llm_chat()))
        results.append(("评审提示词", await test_review_prompt()))
        results.append(("LLM评审", await test_llm_review()))
        results.append(("评审委员会", await test_review_committee()))
    else:
        print("\n由于LLM不可用，跳过后续测试")
        results.append(("LLM连接", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠ 部分测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
