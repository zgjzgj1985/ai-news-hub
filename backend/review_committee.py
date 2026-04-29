"""犀利的评审委员会 - LLM驱动的多维度内容质量评审系统"""

import asyncio
import os
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from llm_client import LLMClient, get_llm_client
from prompts import (
    SYSTEM_PROMPT,
    build_review_prompt,
    parse_review_result,
    calculate_total_score,
    grade_from_scores,
    get_source_weight_boost,
)

logger = logging.getLogger(__name__)


class VoteResult(Enum):
    """投票结果枚举"""
    APPROVE = "approve"      # 赞成通过
    WEAK_APPROVE = "weak"    # 勉强通过
    REJECT = "reject"        # 否决


@dataclass
class ReviewVote:
    """单个评审专家的投票"""
    judge_name: str
    judge_alias: str
    result: VoteResult
    score: float      # 0-10分
    reason: str


@dataclass
class ReviewResult:
    """评审委员会最终裁决"""
    article_id: Optional[int] = None
    url: str = ""

    # 各维度投票（LLM评审模式）
    relevance_vote: Optional[ReviewVote] = None
    practicality_vote: Optional[ReviewVote] = None
    timeliness_vote: Optional[ReviewVote] = None
    depth_vote: Optional[ReviewVote] = None
    originality_vote: Optional[ReviewVote] = None

    # LLM评审分数
    llm_scores: Dict[str, float] = field(default_factory=dict)

    # 综合评级 A/B/C/D
    grade: str = "D"

    # 通过的评委数量
    approve_count: int = 0
    weak_count: int = 0
    reject_count: int = 0

    # 综合分数
    total_score: float = 0.0

    # 最终裁决理由
    verdict: str = ""

    # LLM原始评审结果
    llm_verdict: str = ""
    llm_strengths: List[str] = field(default_factory=list)
    llm_weaknesses: List[str] = field(default_factory=list)
    llm_recommendation: str = ""

    # 评审时间
    reviewed_at: Optional[datetime] = None

    # 是否使用LLM评审
    llm_reviewed: bool = False

    def to_dict(self) -> dict:
        """转换为字典格式"""
        votes = []
        vote_attrs = [
            'relevance_vote', 'practicality_vote', 'timeliness_vote',
            'depth_vote', 'originality_vote'
        ]

        for attr_name in vote_attrs:
            vote = getattr(self, attr_name)
            if vote:
                votes.append({
                    "judge": vote.judge_alias,
                    "result": vote.result.value,
                    "score": vote.score,
                    "reason": vote.reason
                })

        return {
            "article_id": self.article_id,
            "url": self.url,
            "grade": self.grade,
            "approve_count": self.approve_count,
            "weak_count": self.weak_count,
            "reject_count": self.reject_count,
            "total_score": round(self.total_score, 2),
            "verdict": self.verdict,
            "votes": votes,
            "llm_scores": self.llm_scores,
            "llm_verdict": self.llm_verdict,
            "llm_strengths": self.llm_strengths,
            "llm_weaknesses": self.llm_weaknesses,
            "llm_recommendation": self.llm_recommendation,
            "llm_reviewed": self.llm_reviewed,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }


class ReviewCommittee:
    """
    评审委员会 - LLM驱动的严格评审系统

    支持两种评审模式：
    1. LLM模式（优先）：使用Qwen3.5 9B进行语义理解评审
    2. 规则模式（回退）：使用正则和关键词规则评审
    """

    def __init__(self):
        self._use_llm = os.getenv("LLM_ENABLED", "false").lower() == "true"
        self._llm_client: Optional[LLMClient] = None

        # 时效性阈值：30天内
        self.TIMELINESS_THRESHOLD_DAYS = 30
        # 相关性阈值：60%关键词命中率
        self.RELEVANCE_THRESHOLD = 0.6
        # 深度阈值：至少500字或包含完整资源
        self.DEPTH_MIN_CHARS = 500

        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        # 实用性指标
        self.practical_patterns = [
            r'github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+',
            r'https?://[^\s]*\.(py|js|ts|json|yaml|yml|cfg|ini)\b',
            r'pip install|npm install|brew install|cargo install',
            r'git clone|wget|curl.*download',
            r'Colab|Jupyter notebook|\.ipynb\b',
            r'开源|open source|open-source',
            r'API|SDK|CLI|tool',
            r'教程|tutorial|guide|how to',
        ]

        # 广告特征
        self.ad_patterns = [
            r'buy now|order now|limited time',
            r'click here to|sign up for free',
            r'subscribe.*newsletter|email.*course',
            r'promo code|discount.*code',
            r'earn money|make money online',
            r'patreon|ko-fi|buymeacoffee',
        ]

        # 高质量来源
        self.quality_sources = {
            'openai', 'anthropic', 'google deepmind', 'hugging face',
            'stability ai', 'mistral ai', 'midjourney', 'stable diffusion',
            'arxiv', 'github', 'npm', 'pypi',
        }

        self.compiled_practical = [re.compile(p, re.IGNORECASE) for p in self.practical_patterns]
        self.compiled_ads = [re.compile(p, re.IGNORECASE) for p in self.ad_patterns]

    @property
    def llm_client(self) -> Optional[LLMClient]:
        """懒加载LLM客户端"""
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    def review(
        self,
        article_id: Optional[int],
        title: str,
        text: str,
        source_name: str,
        published_at: Optional[datetime] = None,
        url: str = ""
    ) -> ReviewResult:
        """
        同步评审接口 - 强制使用本地LLM

        不再使用规则引擎回退，必须配置并启用LLM。

        参数:
            article_id: 文章ID
            title: 文章标题
            text: 文章正文/摘要
            source_name: 来源名称
            published_at: 发布时间
            url: 文章链接

        返回:
            ReviewResult: 评审结果
        """
        result = ReviewResult(
            article_id=article_id,
            url=url,
            reviewed_at=datetime.utcnow()
        )

        # 必须使用LLM评审
        if not self.is_llm_available():
            raise RuntimeError(
                "LLM服务不可用！请确保：\n"
                "1. Ollama服务正在运行 (http://localhost:11434)\n"
                "2. 已安装 qwen3.5:9b 模型\n"
                "3. .env 中 LLM_ENABLED=true"
            )

        # 检查是否已有事件循环在运行
        try:
            loop = asyncio.get_running_loop()
            # 在已有循环中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    self._sync_llm_review,
                    result, title, text, source_name
                )
                future.result(timeout=120)  # 120秒超时
        except RuntimeError:
            # 没有运行中的循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._llm_review(result, title, text, source_name))
            finally:
                loop.close()

        return result

    def is_llm_available(self) -> bool:
        """检查LLM是否可用"""
        if not self._use_llm:
            return False
        try:
            import requests
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM服务检查失败: {e}")
            return False

    async def areview(
        self,
        article_id: Optional[int],
        title: str,
        text: str,
        source_name: str,
        published_at: Optional[datetime] = None,
        url: str = ""
    ) -> ReviewResult:
        """
        异步LLM评审 - 强制使用本地LLM

        不再使用规则引擎回退。

        参数:
            article_id: 文章ID
            title: 文章标题
            text: 文章正文/摘要
            source_name: 来源名称
            published_at: 发布时间
            url: 文章链接

        返回:
            ReviewResult: 评审结果
        """
        result = ReviewResult(
            article_id=article_id,
            url=url,
            reviewed_at=datetime.utcnow()
        )

        # 必须使用LLM评审
        if not self.is_llm_available():
            raise RuntimeError(
                "LLM服务不可用！请确保：\n"
                "1. Ollama服务正在运行 (http://localhost:11434)\n"
                "2. 已安装 qwen3.5:9b 模型\n"
                "3. .env 中 LLM_ENABLED=true"
            )

        await self._llm_review(result, title, text, source_name)
        return result

    def _sync_llm_review(
        self,
        result: ReviewResult,
        title: str,
        text: str,
        source_name: str
    ):
        """在线程中运行的LLM评审（同步版本）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._llm_review(result, title, text, source_name))
        finally:
            loop.close()

    async def _llm_review(
        self,
        result: ReviewResult,
        title: str,
        text: str,
        source_name: str
    ):
        """使用LLM进行评审"""
        # 构建提示词
        prompts = build_review_prompt(title, text, source_name)

        # 调用LLM
        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]}
        ]

        response = await self.llm_client.chat(messages, json_mode=True)

        # 解析结果
        parsed = parse_review_result(response)

        # 更新结果
        result.llm_reviewed = True
        result.llm_scores = parsed.get("scores", {})
        result.llm_verdict = parsed.get("verdict", "")
        result.llm_strengths = parsed.get("strengths", [])
        result.llm_weaknesses = parsed.get("weaknesses", [])
        result.llm_recommendation = parsed.get("recommendation", "")

        # 计算总分和评级
        scores = result.llm_scores
        result.total_score = calculate_total_score(scores)

        # 应用来源加权系数
        source_boost = get_source_weight_boost(source_name)
        boosted_score = result.total_score + source_boost

        # 使用加权后的分数重新计算评级
        boosted_scores = scores.copy()
        if source_boost != 0:
            # 根据来源调整 practicality 分数
            boosted_scores["practicality"] = min(10, scores.get("practicality", 5) + source_boost)
            result.grade = parsed.get("grade") or grade_from_scores(boosted_scores)
        else:
            result.grade = parsed.get("grade") or grade_from_scores(scores)

        # 生成裁决
        grade = result.grade
        if grade == "A":
            result.verdict = f"强烈推荐！{result.llm_verdict}"
            result.approve_count = 5
        elif grade == "B":
            result.verdict = f"推荐。{result.llm_verdict}"
            result.approve_count = 3
            result.weak_count = 2
        elif grade == "C":
            result.verdict = f"一般。{result.llm_verdict}"
            result.weak_count = 2
            result.reject_count = 3
        else:
            result.verdict = f"过滤。{result.llm_verdict}"
            result.reject_count = 5

        # 创建统一的投票记录
        result.relevance_vote = ReviewVote(
            judge_name="llm_cto",
            judge_alias="CTO",
            result=VoteResult.APPROVE if scores.get("tech_depth", 5) >= 5 else VoteResult.WEAK_APPROVE,
            score=scores.get("tech_depth", 5),
            reason=f"技术深度评分: {scores.get('tech_depth', 5)}"
        )

        result.practicality_vote = ReviewVote(
            judge_name="llm_architect",
            judge_alias="架构师",
            result=VoteResult.APPROVE if scores.get("practicality", 5) >= 5 else VoteResult.WEAK_APPROVE,
            score=scores.get("practicality", 5),
            reason=f"实用性评分: {scores.get('practicality', 5)}"
        )

        result.timeliness_vote = ReviewVote(
            judge_name="llm_gatekeeper",
            judge_alias="守门员",
            result=VoteResult.APPROVE if scores.get("novelty", 5) >= 5 else VoteResult.WEAK_APPROVE,
            score=scores.get("novelty", 5),
            reason=f"新颖性评分: {scores.get('novelty', 5)}"
        )

        result.depth_vote = ReviewVote(
            judge_name="llm_developer",
            judge_alias="全栈开发者",
            result=VoteResult.APPROVE if scores.get("audience_value", 5) >= 5 else VoteResult.WEAK_APPROVE,
            score=scores.get("audience_value", 5),
            reason=f"受众价值评分: {scores.get('audience_value', 5)}"
        )

        result.originality_vote = ReviewVote(
            judge_name="llm_pm",
            judge_alias="产品经理",
            result=VoteResult.APPROVE if result.grade in ["A", "B"] else VoteResult.REJECT,
            score=result.total_score / 5,
            reason=result.llm_recommendation
        )

    def _rule_based_review(
        self,
        result: ReviewResult,
        title: str,
        text: str,
        source_name: str,
        published_at: Optional[datetime] = None
    ) -> ReviewResult:
        """
        基于规则引擎的回退评审（原有逻辑）
        """
        combined_text = f"{title} {text}".lower()
        title_lower = title.lower()

        # 1. 相关性大师
        result.relevance_vote = self._judge_relevance(title, text, title_lower, combined_text)

        # 2. 实用性裁判
        result.practicality_vote = self._judge_practicality(title, text, combined_text)

        # 3. 时效性守门员
        result.timeliness_vote = self._judge_timeliness(published_at)

        # 4. 深度分析师
        result.depth_vote = self._judge_depth(title, text, combined_text, source_name)

        # 5. 原创性检察官
        result.originality_vote = self._judge_originality(
            title, text, combined_text, source_name, result.url
        )

        # 计算最终结果
        self._calculate_final_verdict(result)

        return result

    def _judge_relevance(self, title: str, text: str, title_lower: str, combined: str) -> ReviewVote:
        """相关性大师"""
        score = 0.0
        reasons = []

        core_keywords = {
            'AI前沿': ['gpt', 'claude', 'gemini', 'llm', 'multimodal', 'foundation model',
                      'reasoning', 'agi', 'agent', 'breakthrough', 'sota', 'benchmark'],
            '游戏美术': ['concept art', 'game art', 'texture', 'stable diffusion',
                      'midjourney', 'LoRA', 'controlnet', '3D generation', 'asset'],
            '游戏策划': ['AI NPC', 'procedural', 'dialogue', 'quest', 'narrative',
                       'gameplay', 'level design'],
            '使用技巧': ['prompt', 'tutorial', 'guide', 'best practice', 'workflow',
                       'ComfyUI', 'tips'],
            '工具推荐': ['launch', 'release', 'open source', 'tool', 'github',
                       'cursor', 'copilot', 'framework']
        }

        matched_categories = 0
        title_hits = 0

        for category, keywords in core_keywords.items():
            cat_hits = sum(1 for kw in keywords if kw in title_lower)
            if cat_hits > 0:
                matched_categories += 1
                title_hits += cat_hits

        if title_hits >= 2:
            score += 5
            reasons.append(f"标题命中{title_hits}个核心关键词")
        elif title_hits == 1:
            score += 2
            reasons.append("标题命中1个核心关键词")

        if matched_categories >= 2:
            score += 2
            reasons.append(f"涉及{matched_categories}个分类")

        if score >= 6:
            result = VoteResult.APPROVE
            verdict = "高度相关"
        elif score >= 3:
            result = VoteResult.WEAK_APPROVE
            verdict = "勉强相关"
        else:
            result = VoteResult.REJECT
            verdict = "不相关"

        return ReviewVote(
            judge_name="relevance_master",
            judge_alias="相关性大师",
            result=result,
            score=min(score, 10),
            reason=f"{verdict}。{'；'.join(reasons) if reasons else '未命中目标关键词'}"
        )

    def _judge_practicality(self, title: str, text: str, combined: str) -> ReviewVote:
        """实用性裁判"""
        score = 0.0
        reasons = []
        practical_count = 0

        practical_indicators = {
            'github': (r'github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+', 3, '含GitHub仓库'),
            'code_cmd': (r'pip install|npm install|git clone|import |def |class ', 2, '含可执行命令/代码'),
            'notebook': (r'Colab|\.ipynb|jupyter', 2, '含notebook'),
            'resource': (r'download|free.*download|资源', 2, '含资源下载'),
            'tutorial': (r'tutorial|guide|教程|how to|step by step', 1, '含教程指南'),
        }

        for name, (pattern, points, desc) in practical_indicators.items():
            if re.search(pattern, combined, re.IGNORECASE):
                score += points
                practical_count += 1
                reasons.append(desc)

        if practical_count >= 3:
            score += 2
            reasons.append(f"多项实用指标({practical_count}个)")

        if practical_count == 0:
            result = VoteResult.REJECT
            verdict = "无实用价值"
        elif practical_count == 1 and score < 3:
            result = VoteResult.REJECT
            verdict = "实用价值不足"
        elif score >= 5:
            result = VoteResult.APPROVE
            verdict = "极具实用价值"
        elif score >= 3:
            result = VoteResult.WEAK_APPROVE
            verdict = "有一定实用价值"
        else:
            result = VoteResult.REJECT
            verdict = "实用价值不足"

        return ReviewVote(
            judge_name="practicality_judge",
            judge_alias="实用性裁判",
            result=result,
            score=min(score, 10),
            reason=f"{verdict}。{'；'.join(reasons) if reasons else '未发现可操作资源'}"
        )

    def _judge_timeliness(self, published_at: Optional[datetime]) -> ReviewVote:
        """时效性守门员"""
        if published_at is None:
            return ReviewVote(
                judge_name="timeliness_gatekeeper",
                judge_alias="时效性守门员",
                result=VoteResult.WEAK_APPROVE,
                score=5.0,
                reason="无法判断时效性，给予中等评分"
            )

        # 统一时区格式
        if published_at.tzinfo is not None:
            now = datetime.now(published_at.tzinfo)
        else:
            now = datetime.utcnow()
        age = now - published_at
        age_days = age.total_seconds() / 86400

        if age_days < 0:
            score = 4.0
            reason = "发布时间异常（未来日期），可疑"
        elif age_days <= 7:
            score = 10.0
            reason = f"非常新鲜（{age_days:.0f}天前）"
        elif age_days <= 14:
            score = 8.0
            reason = f"新鲜（{age_days:.0f}天前）"
        elif age_days <= 30:
            score = 5.0
            reason = f"略显陈旧（{age_days:.0f}天前）"
        elif age_days <= 90:
            score = 2.0
            reason = f"过时不候（{age_days:.0f}天前）"
        else:
            score = 0.0
            reason = f"历史遗迹（{age_days:.0f}天前），一票否决"

        if age_days <= 30:
            result = VoteResult.APPROVE if age_days <= 7 else VoteResult.WEAK_APPROVE
        else:
            result = VoteResult.REJECT

        verdict = "时效性通过" if result != VoteResult.REJECT else "严重超时"

        return ReviewVote(
            judge_name="timeliness_gatekeeper",
            judge_alias="时效性守门员",
            result=result,
            score=score,
            reason=f"{verdict}。{reason}"
        )

    def _judge_depth(self, title: str, text: str, combined: str, source_name: str) -> ReviewVote:
        """深度分析师"""
        score = 0.0
        reasons = []
        char_count = len(text)

        if char_count > 1000:
            score += 4
            reasons.append(f"内容充实（{char_count}字）")
        elif char_count >= 500:
            score += 2
            reasons.append(f"内容适中（{char_count}字）")
        elif char_count >= 200:
            score += 1
            reasons.append(f"内容偏短（{char_count}字）")
        else:
            reasons.append(f"内容过短（{char_count}字）")

        # 结构完整性
        structure_score = 0
        if re.search(r'^#{1,6}\s|\n\s*[-*]\s', text, re.MULTILINE):
            structure_score += 1
        if re.search(r'```[\s\S]*?```|`[^`]+`', text):
            structure_score += 1
        if re.search(r'\d+\.\s+\w', text):
            structure_score += 1

        if structure_score >= 2:
            score += 2
            reasons.append("结构完整")
        elif structure_score == 1:
            score += 1
            reasons.append("结构简单")

        # 专业来源
        quality_sources = ['arxiv', 'github', 'official', 'blog', 'hugging face',
                          'openai', 'anthropic', 'deepmind', 'stability']
        if any(src in source_name.lower() for src in quality_sources):
            score += 2
            reasons.append("来自专业来源")

        # 标题党检测
        clickbait_patterns = [
            r'^.{5,15}竟然', r'^.{5,15}太.{0,5}了',
            r'震惊|惊呆了|炸裂|炸锅', r'必看|收藏|转发',
            r'\?|！{2,}|？{2,}', r'你不知道|不知道你就',
        ]
        clickbait_hits = sum(1 for p in clickbait_patterns if re.search(p, title))
        if clickbait_hits >= 2:
            score -= 3
            reasons.append("标题党嫌疑")

        if score >= 6:
            result = VoteResult.APPROVE
            verdict = "深度优秀"
        elif score >= 3:
            result = VoteResult.WEAK_APPROVE
            verdict = "深度一般"
        else:
            result = VoteResult.REJECT
            verdict = "深度不足"

        return ReviewVote(
            judge_name="depth_analyst",
            judge_alias="深度分析师",
            result=result,
            score=max(min(score, 10), 0),
            reason=f"{verdict}。{'；'.join(reasons) if reasons else '内容单薄'}"
        )

    def _judge_originality(self, title: str, text: str, combined: str,
                          source_name: str, url: str) -> ReviewVote:
        """原创性检察官"""
        score = 10.0
        reasons = []
        deductions = 0

        # 广告检测
        ad_patterns = [
            (r'buy now|order now|limited.*offer', 5, '促销广告'),
            (r'click here.*subscribe|sign up.*free trial', 4, '诱导点击'),
            (r'earn money|make money|passive income', 5, '赚钱诱惑'),
            (r'follow.*(?:instagram|twitter|tiktok|youtube)', 3, '社交媒体引流'),
            (r'patreon|ko-fi|buymeacoffee|support.*me', 4, '打赏引流'),
        ]

        for pattern, penalty, desc in ad_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                deductions += penalty
                reasons.append(f"检测到{desc}（-{penalty}分）")

        # 重复搬运检测
        duplicate_patterns = [
            (r'原标题：|Original|via\s+\w+', 2, '疑似搬运'),
            (r'转载|转自|来源：|source:', 1, '非原创来源标注'),
            (r'翻译自|译自|，本文.*译', 2, '翻译内容'),
        ]

        for pattern, penalty, desc in duplicate_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                deductions += penalty
                reasons.append(f"检测到{desc}（-{penalty}分）")

        score -= deductions

        if deductions >= 5:
            result = VoteResult.REJECT
            verdict = "广告/低质量"
        elif deductions >= 3:
            result = VoteResult.WEAK_APPROVE
            verdict = "质量存疑"
        elif score >= 7:
            result = VoteResult.APPROVE
            verdict = "质量良好"
        else:
            result = VoteResult.WEAK_APPROVE
            verdict = "质量一般"

        return ReviewVote(
            judge_name="originality_prosecutor",
            judge_alias="原创性检察官",
            result=result,
            score=max(min(score, 10), 0),
            reason=f"{verdict}。扣除{deductions}分。{'；'.join(reasons) if reasons else '无明显问题'}"
        )

    def _calculate_final_verdict(self, result: ReviewResult):
        """根据各维度投票计算最终裁决"""
        votes = [
            result.relevance_vote,
            result.practicality_vote,
            result.timeliness_vote,
            result.depth_vote,
            result.originality_vote,
        ]

        for vote in votes:
            if vote.result == VoteResult.APPROVE:
                result.approve_count += 1
            elif vote.result == VoteResult.WEAK_APPROVE:
                result.weak_count += 1
            else:
                result.reject_count += 1
            result.total_score += vote.score

        strong_approve = sum(1 for v in votes if v.result == VoteResult.APPROVE)
        weak_approve = result.weak_count

        if strong_approve >= 4:
            result.grade = "A"
        elif strong_approve + weak_approve >= 3:
            result.grade = "B"
        elif strong_approve + weak_approve >= 2:
            result.grade = "C"
        else:
            result.grade = "D"

        rejected = [v.judge_alias for v in votes if v.result == VoteResult.REJECT]

        if result.grade == "A":
            result.verdict = "强烈推荐！内容优质，高度符合工具开发目的。"
        elif result.grade == "B":
            result.verdict = "推荐。内容有价值，值得一读。"
        elif result.grade == "C":
            result.verdict = f"待定。部分评审未通过：{'、'.join(rejected)}。"
        else:
            result.verdict = f"过滤。关键评审未通过：{'、'.join(rejected)}。"


# 保持向后兼容的接口
def quick_review(title: str, text: str = "", source: str = "") -> dict:
    """
    快速评审接口（强制使用LLM）
    """
    committee = ReviewCommittee()
    result = committee.review(
        article_id=None,
        title=title,
        text=text,
        source_name=source,
        published_at=datetime.utcnow(),
        url=""
    )
    return result.to_dict()


# 全局评审委员会实例
_global_committee: Optional[ReviewCommittee] = None


def get_committee() -> ReviewCommittee:
    """获取全局评审委员会实例"""
    global _global_committee
    if _global_committee is None:
        _global_committee = ReviewCommittee()
    return _global_committee
