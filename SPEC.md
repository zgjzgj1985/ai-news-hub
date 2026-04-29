# AI情报站 - 项目规格说明

## 1. 项目概述

**项目名称**: AI情报站
**类型**: 资讯聚合 Web 应用
**核心功能**: 聚合 AI 领域资讯，支持每日自动抓取、搜索、标签筛选、LLM 评审、自动翻译和收藏
**目标用户**: 开发者（游戏开发者、Vibe Coding 实践者）

---

## 2. 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy / APScheduler |
| 数据库 | SQLite |
| 前端 | Vue 3 + Vite + Pinia + Vue Router |
| AI 评审 | 本地 LLM（Qwen3.5 9B via Ollama） |
| RSS 解析 | feedparser + httpx + BeautifulSoup |
| 样式 | 原生 CSS（自定义属性变量系统） |

---

## 3. 数据模型

### Article（文章）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(500) | 标题 |
| title_zh | String(500) | 中文标题（翻译） |
| url | String(1000) | 原文链接 |
| summary | Text | 摘要/描述 |
| summary_zh | Text | 中文摘要（翻译） |
| source_name | String(200) | 来源名称 |
| source_url | String(1000) | 来源首页 |
| author | String(200) | 作者（可选） |
| published_at | DateTime | 发布时间 |
| fetched_at | DateTime | 抓取时间 |
| tags | JSON | 标签列表 |
| content_hash | String(64) | 去重哈希 |
| read_time_minutes | Integer | 预估阅读时间 |
| score | Integer | 热度分数（来自 HN/Reddit 等） |
| is_translated | Boolean | 是否已翻译 |
| translated_at | DateTime | 翻译时间 |
| review_grade | String(1) | 评审等级（A/B/C/D） |
| review_score | Integer | 综合评分（0-780） |
| review_result | JSON | 详细评审结果 |
| review_verdict | Text | 最终裁决理由 |
| reviewed_at | DateTime | 评审时间 |
| deep_review_done | Boolean | 是否已完成深度评审 |
| deep_review_body | Text | 抓取的正文内容（不暴露给前端） |

### Bookmark（收藏）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| article_id | Integer | 关联文章ID（外键，唯一） |
| created_at | DateTime | 收藏时间 |

### FeedSource（订阅源）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(200) | 源名称 |
| url | String(1000) | RSS URL |
| category | String(50) | 分类 |
| enabled | Boolean | 是否启用 |
| last_fetched | DateTime | 上次抓取时间 |
| priority | Integer | 优先级 |
| created_at | DateTime | 创建时间 |

---

## 4. API 接口

### 文章

- `GET /api/articles` — 获取文章列表（支持 tag/keyword/source/grade/page/limit/sort 筛选）
- `GET /api/articles/{id}` — 获取文章详情
- `POST /api/articles/{id}/bookmark` — 收藏/取消收藏
- `GET /api/articles/{id}/bookmark` — 查询收藏状态

### 收藏

- `GET /api/bookmarks` — 获取收藏列表
- `DELETE /api/bookmarks/{article_id}` — 取消收藏

### 统计

- `GET /api/stats` — 获取统计概览
- `GET /api/stats/review` — 获取评审统计

### 订阅源

- `GET /api/sources` — 获取所有订阅源
- `GET /api/sources/{id}` — 获取指定订阅源
- `POST /api/sources` — 添加订阅源
- `PATCH /api/sources/{id}` — 更新订阅源
- `DELETE /api/sources/{id}` — 删除订阅源

### 评审

- `GET /api/review/stats` — 获取评审统计
- `GET /api/review/llm-status` — LLM 服务状态与可用模型
- `POST /api/review/article/{id}` — 评审单篇文章
- `POST /api/review/article/{id}/llm-review` — 强制使用 LLM 评审
- `POST /api/review/article/{id}/re-review` — 重新评审
- `POST /api/review/batch` — 批量评审（后台）
- `POST /api/review/llm-batch` — LLM 批量评审
- `POST /api/review/batch-backlog` — 批量评审历史未评审文章
- `POST /api/review/filter` — 获取通过评审的文章
- `GET /api/review/articles` — 按评级筛选已评审文章
- `GET /api/review/batch-status` — 批量评审任务状态

### 翻译

- `POST /api/translate` — 翻译单段文本
- `POST /api/translate/article/{id}` — 翻译指定文章的摘要
- `POST /api/translate/article/{id}/regenerate` — 重新翻译
- `POST /api/translate/batch` — 批量翻译（后台，最多 100 篇）
- `POST /api/translate/all` — 翻译所有未翻译的文章
- `GET /api/translate/stats` — 获取翻译统计

### 任务

- `POST /api/admin/refresh` — 手动触发抓取
- `GET /api/health` — 健康检查

---

## 5. 内容分类标签体系

| 标签 | 说明 |
|------|------|
| vibe_coding | AI 辅助开发工作流 |
| 工具推荐 | 新工具与应用发布 |
| AI前沿 | 新模型、技术突破 |
| 使用技巧 | Prompt 工程、最佳实践 |
| 游戏策划 | AI 在游戏设计中的应用 |
| 游戏美术 | AI 辅助美术制作 |

---

## 6. 预置订阅源

1. Simon Willison — `https://simonwillison.net/atom/entry/`
2. Cursor Changelog — `https://changelog.cursor.com/rss`
3. DEV.to Cursor — `https://dev.to/feed/tags/cursor`
4. Replit Blog — `https://blog.replit.com/feed.xml`
5. Latent Space — `https://www.latent.space/rss`

---

## 7. 前端路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | HomeView | 首页资讯流 |
| `/article/:id` | ArticleView | 文章详情 |
| `/bookmarks` | BookmarksView | 收藏列表 |
| `/settings` | SettingsView | 设置页 |

---

## 8. 定时任务

| 任务 | 触发器 | 说明 |
|------|--------|------|
| RSS 抓取 | Cron (默认 09:30) | 获取所有订阅源更新 |
| 深度评审 | Interval (30min) | 抓取正文 + LLM 评分，每次 20 篇 |
| 翻译积压 | Interval (45min) | 翻译未翻译的摘要，每次 30 篇 |

---

## 9. 验收标准

- [x] 后端 API 正常响应，可通过 curl 测试
- [x] 前端能正确显示文章列表（卡片流）
- [x] 标签筛选正常工作
- [x] 搜索功能返回相关结果
- [x] 收藏/取消收藏功能正常
- [x] 设置页能管理订阅源
- [x] 定时任务能自动触发抓取
- [x] LLM 评审能正常工作
- [x] 响应式布局适配移动端
- [x] 自动翻译功能正常
- [x] 深度评审功能正常（抓取正文 + LLM 评分）
