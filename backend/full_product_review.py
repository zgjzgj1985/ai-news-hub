# AI情报站 - 全面体验评审脚本

import asyncio
import sys
import io
from datetime import datetime
from playwright.async_api import async_playwright

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class AIAgencyProductReviewer:
    """
    以机器犀利产品体验官视角，对AI情报站进行全面评审
    评审维度：
    1. 首屏体验 - 第一眼是否吸引
    2. 核心功能 - 文章浏览、筛选、搜索是否好用
    3. 交互细节 - 按钮、状态反馈是否清晰
    4. 信息架构 - 内容组织是否合理
    5. 性能感知 - 加载是否流畅
    """

    def __init__(self):
        self.base_url = "http://localhost:5173"
        self.api_url = "http://127.0.0.1:8000"
        self.issues = []
        self.praises = []
        self.score_card = {}

    def log_issue(self, category, severity, message, suggestion=""):
        """记录问题"""
        self.issues.append({
            "category": category,
            "severity": severity,
            "message": message,
            "suggestion": suggestion
        })
        severity_prefix = {"critical": "[CRITICAL]", "major": "[WARNING] ", "minor": "[MINOR]   "}
        prefix = severity_prefix.get(severity, "[INFO]    ")
        print(f"  {prefix} {message}")
        if suggestion:
            print(f"     建议: {suggestion}")

    def log_praise(self, category, message):
        """记录优点"""
        self.praises.append({"category": category, "message": message})
        print(f"  [OK] {message}")

    def print_section(self, title):
        """打印分节标题"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")

    async def run_review(self):
        """执行全面评审"""
        start_time = datetime.now()
        print(f"\n{'#'*60}")
        print(f"# AI情报站 - 产品体验评审报告")
        print(f"# 评审时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# 评审视角: 机器犀利产品体验官")
        print(f"{'#'*60}")

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                locale="zh-CN"
            )
            page = await context.new_page()

            # 启用请求日志用于调试
            page.on("console", lambda msg: print(f"  [CONSOLE ERROR] {msg.text}") if msg.type == "error" else None)

            try:
                # 第一部分：首屏体验
                await self.review_first_screen(page)

                # 第二部分：核心功能体验
                await self.review_core_functions(page)

                # 第三部分：交互细节
                await self.review_interaction_details(page)

                # 第四部分：内容质量
                await self.review_content_quality(page)

                # 第五部分：性能感知
                await self.review_performance(page)

                # 生成评分卡
                self.generate_score_card()

                # 输出总结
                self.print_summary()

            except Exception as e:
                import traceback
                self.log_issue("SYSTEM", "critical", f"测试过程出错: {str(e)}")
                traceback.print_exc()

            finally:
                await browser.close()

    async def review_first_screen(self, page):
        """评审首屏体验"""
        self.print_section("第一部分：首屏体验")

        # 加载首页
        print("\n正在加载首页...")
        load_start = datetime.now()
        await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
        load_time = (datetime.now() - load_start).total_seconds()

        print(f"  页面加载耗时: {load_time:.2f}秒")

        if load_time > 3:
            self.log_issue("PERFORMANCE", "minor", f"首屏加载偏慢({load_time:.1f}秒)，用户可能感到焦虑")
        else:
            self.log_praise("PERFORMANCE", f"首屏加载较快({load_time:.1f}秒)")

        # 检查页面标题
        title = await page.title()
        print(f"  页面标题: {title}")
        if "AI情报站" in title:
            self.log_praise("BRAND", "标题清晰，包含品牌名")
        else:
            self.log_issue("SEO", "minor", "页面标题不够明确，建议包含'AI情报站'")

        # 检查核心元素是否存在
        print("\n检查核心UI元素...")

        # 头部导航
        header = await page.query_selector("header")
        if header:
            self.log_praise("UI", "页面头部存在")
        else:
            self.log_issue("UI", "major", "页面缺少头部导航栏")

        # 文章卡片容器
        articles_container = await page.query_selector("[class*='article'], [class*='card'], .article-list, article")
        if articles_container:
            self.log_praise("UI", "文章列表容器存在")
        else:
            self.log_issue("UI", "critical", "找不到文章列表容器")

        # 检查是否有文章内容
        await page.wait_for_timeout(1000)
        article_cards = await page.query_selector_all("[class*='card'], article, .article-item")
        print(f"  检测到文章卡片数量: {len(article_cards)}")

        if len(article_cards) == 0:
            # 可能是加载失败或空状态
            page_content = await page.inner_text("body")
            if "加载失败" in page_content or "error" in page_content.lower():
                self.log_issue("CONTENT", "critical", "页面显示加载失败，内容为空")
            else:
                self.log_issue("CONTENT", "major", "文章列表为空，可能没有数据")

        # 检查统计概览区域
        stats_section = await page.query_selector("[class*='stat'], [class*='overview'], [class*='summary']")
        if stats_section:
            stats_text = await stats_section.inner_text()
            print(f"  统计区域内容: {stats_text[:100]}...")
            self.log_praise("UI", "存在统计概览区域，信息丰富度好")
        else:
            self.log_issue("UI", "minor", "缺少统计概览区域，无法快速了解整体情况")

    async def review_core_functions(self, page):
        """评审核心功能"""
        self.print_section("第二部分：核心功能体验")

        # 1. 快速筛选功能
        print("\n[1] 测试快速筛选功能...")
        filters = await page.query_selector_all("[class*='filter'], [class*='toggle'], button")

        grade_filter_found = False
        for f in filters:
            text = await f.inner_text()
            class_attr = await f.get_attribute("class") or ""
            if "A级" in text or "只看" in text or "grade" in class_attr.lower():
                grade_filter_found = True
                print(f"  发现筛选按钮: {text}")
                await f.click()
                await page.wait_for_timeout(500)

                # 检查筛选结果
                article_cards = await page.query_selector_all("[class*='card'], article")
                print(f"  筛选后文章数: {len(article_cards)}")
                break

        if not grade_filter_found:
            self.log_issue("FEATURE", "major", "未找到'只看A级'等快速筛选按钮，核心功能缺失")
        else:
            self.log_praise("FEATURE", "快速筛选功能正常工作")

        # 2. 标签筛选功能
        print("\n[2] 测试标签筛选功能...")
        tag_buttons = await page.query_selector_all("[class*='tag'], [class*='label'], .filter-btn")

        if len(tag_buttons) > 0:
            self.log_praise("FEATURE", f"发现{len(tag_buttons)}个标签筛选按钮")
            # 点击第一个标签
            tag_text = await tag_buttons[0].inner_text()
            print(f"  点击标签: {tag_text}")
            await tag_buttons[0].click()
            await page.wait_for_timeout(500)

            # 检查URL是否变化（是否支持前端路由）
            url = page.url
            print(f"  筛选后URL: {url}")
        else:
            self.log_issue("FEATURE", "major", "未找到标签筛选组件，无法按分类浏览")

        # 3. 搜索功能
        print("\n[3] 测试搜索功能...")
        search_input = await page.query_selector("input[type='search'], input[placeholder*='搜索'], input[placeholder*='search']")

        if search_input:
            self.log_praise("FEATURE", "搜索输入框存在")
            await search_input.fill("AI")
            await page.wait_for_timeout(500)

            # 查找搜索按钮
            search_btn = await page.query_selector("button[type='submit'], button:has-text('搜索')")
            if search_btn:
                await search_btn.click()
                await page.wait_for_timeout(1000)
                print("  搜索已执行")
            else:
                # 尝试回车搜索
                await search_input.press("Enter")
                await page.wait_for_timeout(1000)

            # 检查是否有搜索结果
            article_cards = await page.query_selector_all("[class*='card'], article")
            print(f"  搜索结果数量: {len(article_cards)}")
        else:
            self.log_issue("FEATURE", "major", "未找到搜索输入框，核心功能缺失")

        # 4. 收藏功能
        print("\n[4] 测试收藏功能...")
        await page.goto(self.base_url, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        bookmark_buttons = await page.query_selector_all("[class*='bookmark'], [class*='star'], [class*='favorite']")

        if len(bookmark_buttons) > 0:
            print(f"  发现{len(bookmark_buttons)}个收藏按钮")
            # 点击第一个收藏按钮
            await bookmark_buttons[0].click()
            await page.wait_for_timeout(500)

            # 检查是否有点击反馈
            btn_class = await bookmark_buttons[0].get_attribute("class") or ""
            if "active" in btn_class or "filled" in btn_class:
                self.log_praise("INTERACTION", "收藏按钮有视觉反馈")
            else:
                self.log_issue("INTERACTION", "minor", "收藏按钮点击后缺少视觉状态变化")
        else:
            self.log_issue("FEATURE", "major", "未找到收藏按钮，无法收藏文章")

    async def review_interaction_details(self, page):
        """评审交互细节"""
        self.print_section("第三部分：交互细节")

        # 1. 悬停效果
        print("\n[1] 测试悬停效果...")
        article_cards = await page.query_selector_all("[class*='card'], article")

        if len(article_cards) > 0:
            # 悬停在第一张卡片上
            await article_cards[0].hover()
            await page.wait_for_timeout(300)

            # 检查是否有阴影/边框变化
            box = await article_cards[0].bounding_box()
            if box:
                print(f"  卡片尺寸: {box['width']:.0f}x{box['height']:.0f}")
        else:
            print("  跳过（无文章卡片）")

        # 2. 按钮状态
        print("\n[2] 检查按钮状态...")
        buttons = await page.query_selector_all("button")

        for btn in buttons[:3]:
            text = await btn.inner_text()
            disabled = await btn.get_attribute("disabled")
            btn_class = await btn.get_attribute("class") or ""

            if disabled is not None:
                print(f"  按钮'{text}'处于禁用状态")
            else:
                print(f"  按钮'{text}'可用")

        # 3. 加载状态
        print("\n[3] 检查加载状态显示...")
        loading_elements = await page.query_selector_all("[class*='loading'], [class*='spinner'], [class*='skeleton']")

        if len(loading_elements) > 0:
            self.log_praise("UX", "有加载状态指示器")
        else:
            print("  未检测到专门的加载状态元素")

        # 4. 空状态处理
        print("\n[4] 检查空状态提示...")
        body_text = await page.inner_text("body")

        if "暂无" in body_text or "空" in body_text or "没有" in body_text:
            self.log_praise("UX", "有空状态提示文案")
        else:
            print("  页面无空状态文案（或暂无空数据）")

        # 5. 错误处理
        print("\n[5] 检查错误提示...")
        error_elements = await page.query_selector_all("[class*='error'], [class*='alert'], [role='alert']")

        if len(error_elements) > 0:
            self.log_praise("UX", "有错误提示区域")
        else:
            print("  未检测到错误提示区域")

    async def review_content_quality(self, page):
        """评审内容质量"""
        self.print_section("第四部分：内容质量")

        # 检查文章标题
        titles = await page.query_selector_all("h1, h2, h3, [class*='title']")
        print(f"\n发现标题元素数量: {len(titles)}")

        title_samples = []
        for t in titles[:5]:
            text = await t.inner_text()
            if len(text) > 5:  # 过滤空白
                title_samples.append(text)

        if title_samples:
            print("  文章标题示例:")
            for t in title_samples[:3]:
                print(f"    - {t[:60]}...")

            # 检查标题是否清晰可读
            if any(len(t) > 20 for t in title_samples):
                self.log_praise("CONTENT", "文章标题清晰可读")
            else:
                self.log_issue("CONTENT", "minor", "部分文章标题可能过短")
        else:
            self.log_issue("CONTENT", "critical", "无法获取文章标题，数据可能有问题")

        # 检查摘要/描述
        descriptions = await page.query_selector_all("p, [class*='summary'], [class*='desc'], [class*='excerpt']")

        if descriptions:
            desc_text = await descriptions[0].inner_text()
            print(f"\n  发现摘要内容: {desc_text[:100]}...")
            if len(desc_text) > 20:
                self.log_praise("CONTENT", "文章有摘要/描述信息")
        else:
            self.log_issue("CONTENT", "minor", "文章缺少摘要描述")

        # 检查来源和时间信息
        meta_elements = await page.query_selector_all("[class*='source'], [class*='time'], [class*='date'], [class*='author']")

        if meta_elements:
            self.log_praise("CONTENT", "文章包含来源/时间等元信息")
        else:
            print("  未明确发现来源时间信息")

        # 检查评级徽章
        grade_badges = await page.query_selector_all("[class*='grade'], [class*='level'], [class*='badge'], [class*='tag']")

        if grade_badges:
            self.log_praise("FEATURE", f"发现{len(grade_badges)}个评级/等级徽章")
        else:
            self.log_issue("FEATURE", "minor", "未发现评级徽章，无法快速判断内容质量")

    async def review_performance(self, page):
        """评审性能感知"""
        self.print_section("第五部分：性能感知")

        # 测试页面切换响应
        print("\n测试页面切换性能...")

        # 模拟导航操作
        nav_links = await page.query_selector_all("nav a, header a")

        for link in nav_links[:2]:
            href = await link.get_attribute("href")
            text = await link.inner_text()

            if href and href != "#":
                start = datetime.now()
                try:
                    await link.click()
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    elapsed = (datetime.now() - start).total_seconds()
                    print(f"  导航到'{text}': {elapsed:.2f}秒")

                    if elapsed > 2:
                        self.log_issue("PERFORMANCE", "minor", f"导航到'{text}'较慢({elapsed:.1f}秒)")
                except Exception as e:
                    print(f"  导航到'{text}'失败: {str(e)}")

        # 返回首页
        await page.goto(self.base_url, wait_until="networkidle")

    def generate_score_card(self):
        """生成评分卡"""
        self.print_section("评分卡")

        categories = {
            "首屏体验": {"weight": 0.15, "score": 0},
            "核心功能": {"weight": 0.35, "score": 0},
            "交互细节": {"weight": 0.15, "score": 0},
            "内容质量": {"weight": 0.20, "score": 0},
            "性能感知": {"weight": 0.15, "score": 0}
        }

        # 统计各维度得分
        category_issues = {}
        for issue in self.issues:
            cat = issue["category"]
            category_issues[cat] = category_issues.get(cat, []) + [issue]

        # 根据问题严重程度扣分
        for cat in categories:
            issues = category_issues.get(cat, [])
            base_score = 100

            for issue in issues:
                if issue["severity"] == "critical":
                    base_score -= 25
                elif issue["severity"] == "major":
                    base_score -= 10
                elif issue["severity"] == "minor":
                    base_score -= 3

            categories[cat]["score"] = max(0, base_score)
            categories[cat]["issues"] = len(issues)

        # 计算加权总分
        total_score = sum(c["score"] * c["weight"] for c in categories.values())

        # 打印评分
        print("\n各维度评分：")
        for cat, data in categories.items():
            score = data["score"]
            issues_count = data.get("issues", 0)
            bar = "#" * int(score / 10) + "-" * (10 - int(score / 10))
            grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
            print(f"  {cat:10s}: {bar} {score:3d} ({grade}) - {issues_count}个问题")

        print(f"\n  {'综合评分':10s}: {total_score:.1f}/100")

        self.score_card = {
            "categories": categories,
            "total": total_score
        }

    def print_summary(self):
        """打印总结报告"""
        self.print_section("总结报告")

        # 问题汇总
        print("\n【问题清单】")
        critical = [i for i in self.issues if i["severity"] == "critical"]
        major = [i for i in self.issues if i["severity"] == "major"]
        minor = [i for i in self.issues if i["severity"] == "minor"]

        if critical:
            print(f"\n  严重问题 ({len(critical)}个):")
            for i in critical:
                print(f"     - {i['message']}")

        if major:
            print(f"\n  重要问题 ({len(major)}个):")
            for i in major:
                print(f"     - {i['message']}")

        if minor:
            print(f"\n  优化建议 ({len(minor)}个):")
            for i in minor[:5]:
                print(f"     - {i['message']}")
            if len(minor) > 5:
                print(f"     ... 还有{len(minor) - 5}个")

        # 优点汇总
        print("\n【优点清单】")
        praise_by_cat = {}
        for p in self.praises:
            cat = p["category"]
            if cat not in praise_by_cat:
                praise_by_cat[cat] = []
            praise_by_cat[cat].append(p["message"])

        for cat, items in praise_by_cat.items():
            print(f"  {cat}: {len(items)}项")
            for item in items[:3]:
                print(f"    * {item}")

        # 最终评价
        print("\n【产品体验官点评】")
        total_score = self.score_card.get("total", 0)

        if total_score >= 85:
            print("  这是一款体验优秀的产品！核心功能完善，交互流畅。")
            print("  建议：继续保持，持续打磨细节体验。")
        elif total_score >= 70:
            print("  产品整体可用，但有明显可改进空间。")
            print("  建议：优先修复严重问题，再优化细节体验。")
        elif total_score >= 55:
            print("  产品基础功能可用，但体验欠佳，需要较大改进。")
            print("  建议：系统性重构交互流程，重点提升核心功能体验。")
        else:
            print("  产品存在严重体验问题，核心功能可能不可用。")
            print("  建议：立即修复阻塞性问题，确保基本可用性。")

        print(f"\n{'='*60}")
        print(f"评审完成！综合评分: {total_score:.1f}/100")
        print(f"{'='*60}\n")

        return self.issues, self.score_card


async def main():
    reviewer = AIAgencyProductReviewer()
    await reviewer.run_review()

if __name__ == "__main__":
    asyncio.run(main())
