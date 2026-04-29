# AI情报站

专注 AI 在**游戏开发**和 **Vibe Coding** 领域的实践与落地，精选能直接用于项目的实用内容。

**核心理念**：开发者的时间很宝贵，只推荐值得花时间阅读的内容。我们追踪 AI 辅助开发的最佳实践，让创作者专注于创作本身。

## 内容优先级

我们是面向**开发者**的 AI 工具情报站，关注内容的**落地价值**而非理论深度。

| 优先级 | 内容类型 | 说明 |
|-------|---------|------|
| 🥇 **最高** | Vibe Coding 实践 | 如何用 AI 工具提升开发效率（Cursor、Copilot、Replit 等） |
| 🥈 **次高** | AI 工具推荐 | 新框架、开源工具、IDE 插件、产品发布 |
| 🥉 **中等** | AI 前沿动态 | 新模型发布、技术突破 |
| 📰 **基础** | 实用技巧 | Prompt 工程、最佳实践 |

> **筛选原则**：开发者的时间很宝贵。只推荐值得花时间阅读的内容，优先实战、轻理论。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 前端 | Vue 3 / Vite / Pinia / Vue Router |
| 数据库 | SQLite |
| AI 评审 | 本地 LLM（Qwen3.5 9B via Ollama） |
| 调度器 | APScheduler |

## 项目结构

```
AI情报站/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # 数据库模型与 Schema
│   ├── scheduler.py         # 定时任务调度
│   ├── llm_client.py        # Ollama LLM 客户端
│   ├── review_committee.py  # LLM 驱动的评审委员会
│   ├── .env                 # 环境变量配置（需手动创建）
│   ├── api/
│   │   ├── articles.py      # 文章 API
│   │   ├── bookmarks.py     # 收藏 API
│   │   ├── stats.py         # 统计与订阅源管理 API
│   │   ├── review.py        # 评审 API
│   │   ├── sources.py       # 订阅源 CRUD API
│   │   └── translate.py     # 翻译 API
│   ├── scraper/
│   │   ├── rss_parser.py    # RSS 抓取与解析
│   │   ├── classifier.py    # 内容分类器
│   │   ├── deep_reviewer.py # 深度评审（抓取正文 + LLM 评分）
│   │   ├── translator.py    # 摘要翻译模块
│   │   └── sources.py       # 订阅源配置
│   └── prompts/
│       └── review_prompts.py # 评审 Prompt 管理
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面视图（HomeView, ArticleView, BookmarksView, SettingsView）
│   │   ├── components/      # 公共组件（ArticleCard 等）
│   │   ├── stores/         # Pinia 状态管理
│   │   └── api/            # API 调用封装
├── docs/
│   ├── REVIEW_COMMITTEE_PLAN.md  # 评审系统设计文档
│   └── UX_REVIEW_REPORT.md       # UX 评审报告
└── README.md
```

## 快速开始

### 前置条件

1. **安装 Ollama**（用于本地 LLM 评审）

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 从 https://ollama.com/download 下载安装

# 下载 Qwen3.5 9B 模型
ollama pull qwen3.5:9b

# 启动 Ollama 服务（后台运行）
ollama serve
```

2. **配置环境变量**

```bash
cd backend
cp .env.example .env  # 或手动创建 .env 文件
```

`.env` 关键配置：

```
LLM_ENABLED=true
LLM_MODEL=qwen3.5:9b
LLM_BASE_URL=http://localhost:11434
LLM_TIMEOUT=60
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=30
DATABASE_URL=sqlite:///D:/path/to/your/data/articles.db
```

> **注意**：Windows 环境下，请将 `DATABASE_URL` 设置为包含中文路径的绝对路径，例如 `sqlite:///D:/Vibe coding/data/articles.db`。

### 启动服务

**后端**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可使用。

### 数据库迁移

首次启动后端时，如遇到 `no such column` 错误，需运行迁移脚本：

```bash
cd backend
python migrate_add_review.py    # 添加评审相关字段
python migrate_add_score.py     # 添加 score 字段
python migrate_deep_review.py    # 添加深度评审字段
```

## 功能特性

### 1. 智能订阅源管理

- 预置高质量 RSS 订阅源（Simon Willison、Cursor Changelog、DEV.to、Replit Blog、Latent Space 等）
- 支持通过 API 添加/编辑/启用/禁用订阅源
- 每日自动抓取更新

### 2. LLM 评审委员会

**核心特性**：使用本地 Qwen3.5 9B 模型对每篇文章进行严格评审，聚焦内容的**实用价值**和**落地可行性**。

**评审流程**：

1. 抓取文章正文（支持多种提取策略）
2. 构建评审提示词（正文 + 摘要一起给 LLM）
3. LLM 评分（6 维度）
4. 计算加权分并给出评级

**评级标准**：

| 评级 | 条件 | 含义 |
|------|------|------|
| A | 实用性 ≥7 且总分 ≥7.5 | 强烈推荐，优先阅读 |
| B | 实用性 ≥5 且总分 ≥6 | 推荐，有参考价值 |
| C | 总分 ≥4 | 一般，可选阅读 |
| D | 低于 C 级 | 过滤，不显示 |

**特别规则**：

- **实战加分**：有 step-by-step 教程、可下载资源的工作流加分
- **理论降级**：纯论文/概念介绍（无代码/无实践）降级
- **游戏开发优先**：内容必须与开发相关，泛 AI 内容降级

### 3. 深度评审

与普通评审不同，深度评审会**抓取文章正文**后让 LLM 阅读理解并评分。评审结果标记 `deep_review_done=True`，且不直接暴露分数到前端（仅显示 A/B/C/D 徽章）。

### 4. 自动翻译

对非中文来源的文章，自动将摘要翻译为中文。翻译状态持久化，已翻译的文章不会重复翻译。

### 5. 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| RSS 抓取 | 每日 09:30 | 获取所有订阅源更新 |
| 深度评审 | 每 30 分钟 | 抓取正文 + LLM 评分（每次 20 篇） |
| 翻译积压 | 每 45 分钟 | 翻译未翻译的摘要（每次 30 篇） |

### 6. 前端功能

- **首页**：统计概览 + 文章列表 + 快速筛选
- **全文搜索**：支持标题和摘要关键词搜索
- **标签筛选**：按分类过滤文章
- **评级筛选**：只看 A 级 / A+B 级 / 全部
- **收藏管理**：收藏喜欢的文章
- **LLM 状态**：实时显示 LLM 服务状态

## API 端点

### 文章

```
GET  /api/articles                  # 获取文章列表（支持分页、标签、关键词、来源、评级筛选）
GET  /api/articles/{id}             # 获取文章详情
POST /api/articles/{id}/bookmark   # 切换收藏状态
GET  /api/articles/{id}/bookmark   # 查询收藏状态
```

### 收藏

```
GET    /api/bookmarks               # 获取收藏列表
DELETE /api/bookmarks/{article_id}  # 取消收藏
```

### 统计与订阅源

```
GET  /api/stats               # 统计概览（文章数、标签分布、新增统计）
GET  /api/stats/review        # 评审统计（各评级数量、通过率、待评审数）
GET  /api/sources             # 获取订阅源列表
POST /api/sources             # 添加订阅源
PATCH /api/sources/{id}       # 更新订阅源
DELETE /api/sources/{id}      # 删除订阅源
```

### 评审

```
GET  /api/review/stats            # 评审统计
GET  /api/review/llm-status      # LLM 服务状态与可用模型
POST /api/review/article/{id}     # 评审单篇文章
POST /api/review/article/{id}/llm-review   # 强制使用 LLM 评审
POST /api/review/article/{id}/re-review    # 重新评审（清除旧结果）
POST /api/review/batch            # 批量评审（后台）
POST /api/review/llm-batch        # LLM 批量评审
POST /api/review/batch-backlog    # 批量评审历史未评审文章
POST /api/review/filter           # 获取通过评审的文章
GET  /api/review/articles         # 按评级筛选已评审文章
GET  /api/review/batch-status     # 批量评审任务状态
```

### 翻译

```
POST /api/translate                          # 翻译单段文本
POST /api/translate/article/{id}            # 翻译指定文章的摘要
POST /api/translate/article/{id}/regenerate # 重新翻译
POST /api/translate/batch                   # 批量翻译（后台，最多 100 篇）
POST /api/translate/all                     # 翻译所有未翻译的文章
GET  /api/translate/stats                    # 翻译统计
```

### 管理

```
POST /api/admin/refresh   # 手动触发 RSS 抓取
GET  /api/health          # 健康检查
```

## 数据库

使用 SQLite 存储（`data/articles.db`），包含以下表：

| 表 | 说明 |
|---|------|
| `articles` | 文章数据（标题、URL、摘要、标签、评审结果、翻译状态等） |
| `bookmarks` | 收藏记录 |
| `feed_sources` | 订阅源配置 |

`articles` 表关键字段：

- `review_grade` — 评审等级（A/B/C/D）
- `review_score` — 综合评分
- `review_result` — 详细评审结果（JSON）
- `deep_review_done` — 是否已完成深度评审
- `is_translated` — 是否已翻译
- `summary_zh` / `title_zh` — 中文翻译

## 开发说明

### 添加新的订阅源

通过 API 添加：

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{"name": "我的来源", "url": "https://example.com/feed.xml", "category": "blog", "priority": 8}'
```

### 自定义评审标准

编辑 `backend/prompts/review_prompts.py` 中的 `SYSTEM_PROMPT`，可调整各维度权重、评级阈值和特别规则。

### 已知问题与解决方案

1. **Event loop 错误**：`get_llm_client()` 每次返回新实例，避免跨事件循环复用导致连接池失效。
2. **中文路径**：Windows 环境下请使用绝对路径配置 `DATABASE_URL`。
3. **迁移脚本**：新增字段后运行对应迁移脚本：`migrate_add_review.py`、`migrate_deep_review.py`。

## License

MIT
