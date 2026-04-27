# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: app.spec.js >> AI情报站 E2E 测试 >> 文章列表显示
- Location: tests\app.spec.js:21:3

# Error details

```
TimeoutError: page.waitForSelector: Timeout 10000ms exceeded.
Call log:
  - waiting for locator('.article-card') to be visible

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - generic [ref=e5]:
      - link "AI情报站" [ref=e6] [cursor=pointer]:
        - /url: /
        - img [ref=e7]
        - generic [ref=e11]: AI情报站
      - generic [ref=e12]:
        - link "资讯" [ref=e13] [cursor=pointer]:
          - /url: /
        - link "收藏" [ref=e14] [cursor=pointer]:
          - /url: /bookmarks
        - link "设置" [ref=e15] [cursor=pointer]:
          - /url: /settings
      - button "刷新" [ref=e17] [cursor=pointer]:
        - img [ref=e18]
        - generic [ref=e21]: 刷新
  - main [ref=e22]:
    - generic [ref=e24]:
      - generic [ref=e25]:
        - generic [ref=e26]:
          - generic [ref=e27]:
            - generic [ref=e28]: "100"
            - generic [ref=e29]: 篇资讯
          - generic [ref=e31]:
            - generic [ref=e32]: "96"
            - generic [ref=e33]: 今日新增
          - generic [ref=e35]:
            - generic [ref=e36]: "0"
            - generic [ref=e37]: 收藏
          - generic [ref=e39]:
            - generic [ref=e40]: "34"
            - generic [ref=e41]: 订阅源
          - generic [ref=e43]:
            - generic [ref=e45]: LLM
            - generic [ref=e46]: 评审
        - generic [ref=e47]:
          - generic [ref=e48]:
            - img [ref=e49]
            - text: 评审委员会
          - generic [ref=e51]:
            - generic "强烈推荐" [ref=e52]: 0 A
            - generic "推荐" [ref=e53]: 15 B
            - generic "待定" [ref=e54]: 85 C
            - generic "已过滤" [ref=e55]: 185 D
          - generic [ref=e56]: 通过率 5.3%
      - generic [ref=e57]:
        - generic [ref=e58]:
          - button "全部" [ref=e59] [cursor=pointer]
          - button "只看A级" [ref=e60] [cursor=pointer]
          - button "A+B级" [ref=e61] [cursor=pointer]
        - generic [ref=e62]:
          - generic [ref=e63]: 当前筛选：
          - generic [ref=e64]:
            - text: A+B级
            - button "×" [ref=e65] [cursor=pointer]
          - button "清除筛选" [ref=e66] [cursor=pointer]
      - generic [ref=e67]:
        - generic [ref=e68]:
          - generic [ref=e69]:
            - img
            - textbox "搜索 AI 资讯..." [ref=e70]
          - combobox [ref=e71] [cursor=pointer]:
            - option "最新优先" [selected]
            - option "最早优先"
        - generic [ref=e72]:
          - button "全部" [ref=e73] [cursor=pointer]
          - button "AI前沿 73" [ref=e74] [cursor=pointer]:
            - text: AI前沿
            - generic [ref=e75]: "73"
          - button "游戏美术 23" [ref=e76] [cursor=pointer]:
            - text: 游戏美术
            - generic [ref=e77]: "23"
          - button "游戏策划 1" [ref=e78] [cursor=pointer]:
            - text: 游戏策划
            - generic [ref=e79]: "1"
          - button "使用技巧 9" [ref=e80] [cursor=pointer]:
            - text: 使用技巧
            - generic [ref=e81]: "9"
          - button "工具推荐 13" [ref=e82] [cursor=pointer]:
            - text: 工具推荐
            - generic [ref=e83]: "13"
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | const BASE_URL = 'http://localhost:5173'
  4   | 
  5   | test.describe('AI情报站 E2E 测试', () => {
  6   |   test.beforeEach(async ({ page }) => {
  7   |     await page.goto(BASE_URL)
  8   |   })
  9   | 
  10  |   test('首页加载成功', async ({ page }) => {
  11  |     // 检查页面标题
  12  |     await expect(page).toHaveTitle(/AI情报站/)
  13  | 
  14  |     // 检查主导航存在
  15  |     await expect(page.locator('nav, header, .navbar, .header')).toBeVisible()
  16  | 
  17  |     // 检查主要内容区域（使用更精确的选择器）
  18  |     await expect(page.locator('main')).toBeVisible()
  19  |   })
  20  | 
  21  |   test('文章列表显示', async ({ page }) => {
  22  |     // 等待文章加载
> 23  |     await page.waitForSelector('.article-card', { timeout: 10000 })
      |                ^ TimeoutError: page.waitForSelector: Timeout 10000ms exceeded.
  24  | 
  25  |     // 检查有文章显示
  26  |     const articles = page.locator('.article-card')
  27  |     await expect(articles.first()).toBeVisible()
  28  | 
  29  |     // 检查文章标题
  30  |     const firstTitle = articles.first().locator('h2').first()
  31  |     await expect(firstTitle).toBeVisible()
  32  |   })
  33  | 
  34  |   test('文章卡片信息完整', async ({ page }) => {
  35  |     await page.waitForSelector('.article-card', { timeout: 10000 })
  36  | 
  37  |     const firstArticle = page.locator('.article-card').first()
  38  | 
  39  |     // 检查标题
  40  |     const title = firstArticle.locator('h2').first()
  41  |     await expect(title).toBeVisible()
  42  | 
  43  |     // 检查来源标签
  44  |     const source = firstArticle.locator('.source-name')
  45  |     await expect(source.first()).toBeVisible()
  46  | 
  47  |     // 检查时间显示
  48  |     const date = firstArticle.locator('.date')
  49  |     await expect(date.first()).toBeVisible()
  50  |   })
  51  | 
  52  |   test('点击文章跳转详情页', async ({ page }) => {
  53  |     await page.waitForSelector('.article-card', { timeout: 10000 })
  54  | 
  55  |     // 点击第一篇文章的卡片
  56  |     const firstArticle = page.locator('.article-card').first()
  57  |     await firstArticle.click()
  58  | 
  59  |     // 等待详情页加载
  60  |     await page.waitForURL(/\/article\//)
  61  | 
  62  |     // 检查详情页显示文章标题
  63  |     await page.waitForSelector('h1, .article-title, [class*="title"]', { timeout: 5000 })
  64  |     const detailTitle = page.locator('h1, .article-title, [class*="title"]').first()
  65  |     await expect(detailTitle).toBeVisible()
  66  |   })
  67  | 
  68  |   test('详情页摘要排版', async ({ page }) => {
  69  |     await page.waitForSelector('.article-card', { timeout: 10000 })
  70  | 
  71  |     // 点击第一篇文章
  72  |     const firstArticle = page.locator('.article-card').first()
  73  |     await firstArticle.click()
  74  | 
  75  |     // 等待详情页加载
  76  |     await page.waitForURL(/\/article\//)
  77  | 
  78  |     // 检查摘要区域存在
  79  |     const summary = page.locator('.article-body, [class*="summary"], [class*="content"]')
  80  |     await expect(summary.first()).toBeVisible()
  81  | 
  82  |     // 检查摘要有内容
  83  |     const summaryText = await summary.first().textContent()
  84  |     expect(summaryText.length).toBeGreaterThan(10)
  85  |   })
  86  | 
  87  |   test('返回列表功能', async ({ page }) => {
  88  |     await page.waitForSelector('.article-card', { timeout: 10000 })
  89  | 
  90  |     // 点击进入详情页
  91  |     const firstArticle = page.locator('.article-card').first()
  92  |     await firstArticle.click()
  93  | 
  94  |     await page.waitForURL(/\/article\//)
  95  | 
  96  |     // 点击返回按钮
  97  |     const backButton = page.locator('a:has-text("返回"), button:has-text("返回"), .back, [class*="back"]')
  98  |     if (await backButton.count() > 0) {
  99  |       await backButton.first().click()
  100 |       await page.waitForURL(BASE_URL + '/', { timeout: 5000 })
  101 |     }
  102 |   })
  103 | 
  104 |   test('筛选功能', async ({ page }) => {
  105 |     await page.waitForSelector('.article-card', { timeout: 10000 })
  106 | 
  107 |     // 查找筛选按钮
  108 |     const filterButtons = page.locator('[class*="filter"], .filter-tab')
  109 | 
  110 |     if (await filterButtons.count() > 0) {
  111 |       // 点击 A+B级筛选
  112 |       const gradeABButton = page.locator('.filter-tab:has-text("A+B级")')
  113 |       if (await gradeABButton.count() > 0) {
  114 |         await gradeABButton.first().click()
  115 |         await page.waitForTimeout(500)
  116 | 
  117 |         // 检查筛选后的文章数量
  118 |         const articles = page.locator('.article-card')
  119 |         const count = await articles.count()
  120 |         console.log('筛选后文章数量: ' + count)
  121 |       }
  122 |     }
  123 |   })
```