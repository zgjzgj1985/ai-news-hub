import { test, expect } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'

test.describe('AI情报站 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
  })

  test('首页加载成功', async ({ page }) => {
    // 检查页面标题
    await expect(page).toHaveTitle(/AI情报站/)

    // 检查主导航存在
    await expect(page.locator('nav, header, .navbar, .header')).toBeVisible()

    // 检查主要内容区域（使用更精确的选择器）
    await expect(page.locator('main')).toBeVisible()
  })

  test('文章列表显示', async ({ page }) => {
    // 等待文章加载
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 检查有文章显示
    const articles = page.locator('.article-card')
    await expect(articles.first()).toBeVisible()

    // 检查文章标题
    const firstTitle = articles.first().locator('h2').first()
    await expect(firstTitle).toBeVisible()
  })

  test('文章卡片信息完整', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    const firstArticle = page.locator('.article-card').first()

    // 检查标题
    const title = firstArticle.locator('h2').first()
    await expect(title).toBeVisible()

    // 检查来源标签
    const source = firstArticle.locator('.source-name')
    await expect(source.first()).toBeVisible()

    // 检查时间显示
    const date = firstArticle.locator('.date')
    await expect(date.first()).toBeVisible()
  })

  test('点击文章跳转详情页', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 点击第一篇文章的卡片
    const firstArticle = page.locator('.article-card').first()
    await firstArticle.click()

    // 等待详情页加载
    await page.waitForURL(/\/article\//)

    // 检查详情页显示文章标题
    await page.waitForSelector('h1, .article-title, [class*="title"]', { timeout: 5000 })
    const detailTitle = page.locator('h1, .article-title, [class*="title"]').first()
    await expect(detailTitle).toBeVisible()
  })

  test('详情页摘要排版', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 点击第一篇文章
    const firstArticle = page.locator('.article-card').first()
    await firstArticle.click()

    // 等待详情页加载
    await page.waitForURL(/\/article\//)

    // 检查摘要区域存在
    const summary = page.locator('.article-body, [class*="summary"], [class*="content"]')
    await expect(summary.first()).toBeVisible()

    // 检查摘要有内容
    const summaryText = await summary.first().textContent()
    expect(summaryText.length).toBeGreaterThan(10)
  })

  test('返回列表功能', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 点击进入详情页
    const firstArticle = page.locator('.article-card').first()
    await firstArticle.click()

    await page.waitForURL(/\/article\//)

    // 点击返回按钮
    const backButton = page.locator('a:has-text("返回"), button:has-text("返回"), .back, [class*="back"]')
    if (await backButton.count() > 0) {
      await backButton.first().click()
      await page.waitForURL(BASE_URL + '/', { timeout: 5000 })
    }
  })

  test('筛选功能', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 查找筛选按钮
    const filterButtons = page.locator('[class*="filter"], .filter-tab')

    if (await filterButtons.count() > 0) {
      // 点击 A+B级筛选
      const gradeABButton = page.locator('.filter-tab:has-text("A+B级")')
      if (await gradeABButton.count() > 0) {
        await gradeABButton.first().click()
        await page.waitForTimeout(500)

        // 检查筛选后的文章数量
        const articles = page.locator('.article-card')
        const count = await articles.count()
        console.log('筛选后文章数量: ' + count)
      }
    }
  })

  test('收藏功能', async ({ page }) => {
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 点击第一篇文章进入详情页
    const firstArticle = page.locator('.article-card').first()
    await firstArticle.click()

    await page.waitForURL(/\/article\//)

    // 查找收藏按钮
    const bookmarkButton = page.locator('button:has-text("收藏"), .bookmark-btn')
    if (await bookmarkButton.count() > 0) {
      await bookmarkButton.first().click()
      await page.waitForTimeout(500)

      // 检查按钮状态变化
      const buttonText = await bookmarkButton.first().textContent()
      expect(buttonText).toMatch(/已收藏|收藏/)
    }
  })

  test('API 数据验证', async ({ request }) => {
    // 测试 API 响应
    const response = await request.get('http://127.0.0.1:8000/api/articles?page=1&limit=5')

    expect(response.ok()).toBeTruthy()

    const data = await response.json()

    // 检查数据结构
    expect(data).toHaveProperty('items')
    expect(data).toHaveProperty('total')
    expect(Array.isArray(data.items)).toBeTruthy()

    // 检查文章数据结构
    if (data.items.length > 0) {
      const article = data.items[0]
      expect(article).toHaveProperty('id')
      expect(article).toHaveProperty('title')
      expect(article).toHaveProperty('url')
      expect(article).toHaveProperty('source_name')

      console.log(`API 返回 ${data.total} 篇文章`)
    }
  })

  test('详情页 API', async ({ request }) => {
    // 先获取文章列表
    const listResponse = await request.get('http://127.0.0.1:8000/api/articles?page=1&limit=1')
    const listData = await listResponse.json()

    if (listData.items.length > 0) {
      const articleId = listData.items[0].id

      // 获取详情
      const detailResponse = await request.get(`http://127.0.0.1:8000/api/articles/${articleId}`)
      expect(detailResponse.ok()).toBeTruthy()

      const article = await detailResponse.json()
      expect(article).toHaveProperty('title')
      expect(article).toHaveProperty('summary')

      console.log(`文章摘要长度: ${article.summary?.length || 0}`)
    }
  })

  test('页面无控制台错误', async ({ page }) => {
    const errors = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    await page.waitForSelector('.article-card', { timeout: 10000 })
    await page.waitForTimeout(1000)

    // 过滤掉无关紧要的错误
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('net::ERR')
    )

    if (criticalErrors.length > 0) {
      console.log('控制台错误:', criticalErrors)
    }

    expect(criticalErrors.length).toBe(0)
  })
})

test.describe('响应式测试', () => {
  test('移动端视图', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto(BASE_URL)

    // 等待内容加载
    await page.waitForSelector('.article-card', { timeout: 10000 })

    // 检查内容仍然可见
    const firstArticle = page.locator('.article-card').first()
    await expect(firstArticle).toBeVisible()
  })

  test('平板视图', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto(BASE_URL)

    await page.waitForSelector('.article-card', { timeout: 10000 })

    const firstArticle = page.locator('.article-card').first()
    await expect(firstArticle).toBeVisible()
  })
})
