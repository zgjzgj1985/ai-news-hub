# AI情报站

专注 AI 在**游戏制作**领域的实践与落地，精选能直接用于项目的实用内容。

**核心理念**：游戏开发者的时间很宝贵，只推荐值得花时间阅读的内容。我们追踪 AI 辅助游戏开发的最佳实践，让创作者专注于创作本身。

## 内容优先级

我们是面向**游戏开发者**的 AI 工具情报站，关注内容的**落地价值**而非理论深度。

| 优先级 | 内容类型 | 说明 |
|-------|---------|------|
| 🥇 **最高** | AI游戏设计应用 | 核心关注点：AI如何改变游戏设计与开发 |
| 🥈 **次高** | Vibe Coding实践 | 如何用AI工具提升开发效率 |
| 🥉 **中等** | AI美术工作流 | AI辅助游戏美术制作的实用技巧 |
| 📰 **基础** | 前沿资讯/工具 | 了解行业动态、发现新工具 |
| 📚 **极少** | 理论知识 | 论文/学术研究占比极少（<5%） |

> **筛选原则**：游戏开发者的时间很宝贵。只推荐值得花时间阅读的内容，优先实战、轻理论。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy |
| 前端 | Vue 3 / Vite / Pinia |
| 数据库 | SQLite |
| AI评审 | 本地 LLM (Qwen3.5 9B via Ollama) |
| 调度器 | APScheduler |

## 项目结构

```
AI情报站/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # 数据库模型与Schema
│   ├── scheduler.py         # 定时任务调度
│   ├── llm_client.py        # Ollama LLM 客户端
│   ├── review_committee.py  # LLM驱动的评审委员会
│   ├── scraper/
│   │   ├── rss_parser.py    # RSS抓取与解析
│   │   ├── classifier.py    # 内容分类器
│   │   └── sources.py       # 订阅源配置
│   ├── api/
│   │   ├── articles.py      # 文章API
│   │   ├── bookmarks.py    # 收藏API
│   │   ├── stats.py        # 统计API
│   │   └── review.py       # 评审API
│   └── prompts/
│       └── review_prompts.py # 评审Prompt管理
├── frontend/
│   └── src/
│       ├── views/          # 页面视图
│       ├── components/     # 公共组件
│       ├── stores/         # Pinia状态管理
│       └── api/            # API调用封装
└── docs/
    └── REVIEW_COMMITTEE_PLAN.md  # 评审系统设计文档
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

# 启动 Ollama 服务
ollama serve
```

2. **配置环境变量**

```bash
cd backend
cp .env.example .env  # 或手动创建 .env 文件

# .env 配置内容：
LLM_ENABLED=true
LLM_MODEL=qwen3.5:9b
LLM_BASE_URL=http://localhost:11434
```

### 启动服务

**后端**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可使用。

## 功能特性

### 1. 智能订阅源管理

- 预置高质量 RSS 订阅源（Hugging Face、Game Developer、r/ComfyUI、机器之心等）
- 支持添加/编辑/启用/禁用订阅源
- 每个源独立的每日抓取上限（防止噪音淹没优质内容）

### 2. 游戏开发者友好的内容分类

| 标签 | 优先级 | 说明 | 示例关键词 |
|------|-------|------|----------|
| **游戏策划** | 最高 | AI驱动的游戏设计与生成 | AI NPC、程序化生成、对话系统、剧情生成 |
| **Vibe Coding** | 次高 | AI辅助开发工作流 | Cursor工作流、Copilot实践、代码生成 |
| **游戏美术** | 中等 | AI辅助美术制作 | Stable Diffusion、LoRA、ComfyUI、资产生成 |
| **工具推荐** | 基础 | 开发工具与应用发布 | 新框架、开源工具、IDE插件 |
| **AI前沿** | 极少 | 前沿技术动态 | 新模型发布、技术突破 |

### 3. LLM 评审委员会

**核心特性**：使用本地 Qwen3.5 9B 模型对每篇文章进行严格评审，聚焦内容的**实用价值**和**落地可行性**。

**评审维度**（按重要性排序）：

| 维度 | 权重 | 说明 |
|------|------|------|
| **实用性** | 最高 | 是否有可直接用于项目的代码/工具/工作流 |
| **落地性** | 高 | 内容是否可在实际项目中应用 |
| **受众匹配** | 高 | 是否适合游戏开发者 |
| **新颖性** | 中 | 是否介绍新技术/方法 |
| **技术深度** | 低 | 理论知识深度（非核心） |

**评级标准**：

| 评级 | 条件 | 含义 |
|------|------|------|
| A | 实用性≥7 且总分≥7.5 | 强烈推荐，优先阅读 |
| B | 实用性≥5 且总分≥6 | 推荐，有参考价值 |
| C | 总分≥4 | 一般，可选阅读 |
| D | 低于C级 | 过滤，不显示 |

**特别规则**：

- **游戏开发优先**：内容必须与游戏制作相关，泛AI内容降级
- **实战加分**：有 step-by-step 教程、可下载资源的工作流加分
- **理论降级**：纯论文/概念介绍（无代码/无实践）降级
- **学术来源**：ArXiv等必须包含 GitHub 代码或实战案例

### 4. 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| RSS抓取 | 每日 08:00 | 获取所有订阅源更新 |
| 评审积压 | 每30分钟 | 自动评审未评审的文章（每次50篇） |

### 5. 前端功能

- **首页**：统计概览 + 文章列表 + 快速筛选
- **全文搜索**：支持标题和摘要关键词搜索
- **标签筛选**：按5大分类过滤文章（游戏策划/Vibe Coding/游戏美术/工具推荐/AI前沿）
- **评级筛选**：只看A级 / A+B级 / 全部
- **收藏管理**：收藏喜欢的文章
- **LLM状态**：实时显示评审模式（LLM/规则）

## API 端点

### 文章

```
GET  /api/articles          # 获取文章列表（支持分页、筛选、搜索）
GET  /api/articles/{id}     # 获取文章详情
POST /api/articles/{id}/bookmark  # 切换收藏状态
```

### 评审

```
GET  /api/review/stats           # 评审统计
GET  /api/review/llm-status      # LLM服务状态
POST /api/review/article/{id}   # 评审单篇文章
POST /api/review/batch           # 批量评审（后台）
POST /api/review/llm-batch       # LLM批量评审
GET  /api/review/articles        # 按评级筛选文章
```

### 管理

```
POST /api/admin/refresh          # 手动触发RSS抓取
GET  /api/sources                # 获取订阅源列表
```

## 数据库

使用 SQLite 存储，包含以下表：

- `articles`：文章数据（标题、URL、摘要、标签、评审结果等）
- `bookmarks`：收藏记录
- `feed_sources`：订阅源配置

## 开发说明

### 添加新的订阅源

编辑 `backend/scraper/sources.py` 中的 `FEED_SOURCES` 字典：

```python
"my_source": {
    "name": "我的来源",
    "url": "https://example.com/feed.xml",
    "category": "blog",
    "priority": 8,  # 优先级 1-10
}
```

### 自定义评审标准

编辑 `backend/prompts/review_prompts.py` 中的 `SYSTEM_PROMPT`，可调整：

- 各维度权重
- 评级阈值
- 特别规则（如学术论文降级条件）

### 前端组件

| 组件 | 功能 |
|------|------|
| `ArticleCard.vue` | 文章卡片，含评审徽章和收藏按钮 |
| `SearchBar.vue` | 搜索框，支持排序 |
| `TagFilter.vue` | 标签筛选组件 |
| `HomeView.vue` | 首页视图 |
| `SettingsView.vue` | 设置页面 |

## License

MIT
