# AI情报站 - 项目规格说明

## 1. 项目概述

**项目名称**: AI情报站
**类型**: 资讯聚合 Web 应用
**核心功能**: 聚合 AI 前沿资讯、游戏制作工作流资讯、AI 使用技巧，支持每日自动抓取、搜索、标签筛选和收藏
**目标用户**: 游戏开发者（美术/策划）、AI 爱好者

---

## 2. 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 数据库 | SQLite（开发）+ PostgreSQL（生产） |
| 前端 | Vue 3 + Vite + Pinia + Vue Router |
| 定时任务 | APScheduler |
| RSS 解析 | feedparser + httpx |
| 样式 | 原生 CSS（自定义属性变量系统） |

---

## 3. 数据模型

### Article（文章）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(500) | 标题 |
| url | String(1000) | 原文链接 |
| summary | Text | 摘要/描述 |
| source_name | String(200) | 来源名称 |
| source_url | String(1000) | 来源首页 |
| author | String(200) | 作者（可选） |
| published_at | DateTime | 发布时间 |
| fetched_at | DateTime | 抓取时间 |
| tags | JSON | 标签列表 |
| content_hash | String(64) | 去重哈希 |
| read_time_minutes | Integer | 预估阅读时间 |
| is_bookmarked | Boolean | 是否收藏（关联） |

### Bookmark（收藏）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| article_id | Integer | 关联文章ID（外键） |
| created_at | DateTime | 收藏时间 |

### FeedSource（订阅源）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(200) | 源名称 |
| url | String(1000) | RSS URL |
| category | String(50) | 分类（newsletter/blog/community） |
| enabled | Boolean | 是否启用 |
| last_fetched | DateTime | 上次抓取时间 |
| priority | Integer | 优先级 |

---

## 4. API 接口

### 文章
- `GET /api/articles` — 获取文章列表（支持 tag/keyword/page/limit 筛选）
- `GET /api/articles/{id}` — 获取文章详情
- `POST /api/articles/{id}/bookmark` — 收藏/取消收藏
- `GET /api/articles/{id}/bookmark` — 查询收藏状态

### 收藏
- `GET /api/bookmarks` — 获取收藏列表
- `DELETE /api/bookmarks/{article_id}` — 取消收藏

### 订阅源
- `GET /api/sources` — 获取所有订阅源
- `POST /api/sources` — 添加订阅源
- `PATCH /api/sources/{id}` — 更新订阅源（启用/禁用）
- `DELETE /api/sources/{id}` — 删除订阅源

### 任务
- `POST /api/admin/refresh` — 手动触发抓取
- `GET /api/stats` — 获取统计信息

---

## 5. 内容分类标签体系

| 标签 | 英文 | 说明 |
|------|------|------|
| AI前沿 | ai-frontier | 新模型发布、技术突破 |
| 游戏美术 | game-art | 资产生成、概念设计、3D建模、AI绘图 |
| 游戏策划 | game-design | NPC生成、关卡设计、剧情生成 |
| 使用技巧 | tips | Prompt工程、最佳实践 |
| 工具推荐 | tools | 新工具、新产品 |

---

## 6. 预置订阅源

1. Hacker News (AI相关) — `https://hnrss.org/frontpage`
2. MIT Technology Review — `https://www.technologyreview.com/feed/`
3. OpenAI Blog — `https://openai.com/blog/rss/`
4. Stability AI Blog — `https://stability.ai/news/feed`
5. The Verge AI — `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`
6. Game Developer — `https://www.gamedeveloper.com/rss.xml`
7. ArXiv cs.AI — `https://arxiv.org/rss/cs.AI`
8. Hugging Face Blog — `https://huggingface.co/blog/feed.xml`

---

## 7. 前端路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | HomeView | 首页资讯流 |
| `/article/:id` | ArticleView | 文章详情 |
| `/bookmarks` | BookmarksView | 收藏列表 |
| `/settings` | SettingsView | 设置页 |

---

## 8. 验收标准

- [ ] 后端 API 正常响应，可通过 curl 测试
- [ ] 首次启动自动创建数据库表并填充预置订阅源
- [ ] RSS 抓取正常，能将文章存入数据库
- [ ] 前端能正确显示文章列表（卡片流）
- [ ] 标签筛选正常工作
- [ ] 搜索功能返回相关结果
- [ ] 收藏/取消收藏功能正常
- [ ] 设置页能管理订阅源
- [ ] 定时任务能自动触发抓取
- [ ] 响应式布局适配移动端
