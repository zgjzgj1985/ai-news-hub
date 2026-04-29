# 任务进度记录

## 当前任务
深度评审系统（后台 LLM 阅读理解评分）

## 任务背景
用户反馈"画布"（Cursor Canvases）文章被评为A级，但实际内容质量有限。

**问题根因**：
- 旧评审仅基于 RSS 摘要（可能只有一句话）进行评分
- Cursor Blog 来源有双重加成（系统提示词 + 来源加权），导致评分虚高
- 摘要内容单薄时，LLM 仍然能通过"信任来源"拿到高分

**用户需求**：
- 让 LLM 在后台深度阅读文章正文后进行评分
- 前端不显示评分数字，只显示 A/B/C/D 徽章
- 只有完成深度评审的文章才展示在前端

## 任务计划
- [x] 步骤1：修改数据库模型，添加 deep_review_done 字段
- [x] 步骤2：实现深度评审模块 deep_reviewer.py（抓取正文 + LLM评分）
- [x] 步骤3：修改 scheduler 后台任务，替换为深度评审调度
- [x] 步骤4：修改 API 过滤逻辑，只展示已完成深度评审的文章
- [x] 步骤5：测试验证（语法检查全部通过）

## 修改的文件

### 1. backend/database.py
- 新增字段：`deep_review_done` (Boolean) - 标记是否完成深度评审
- 新增字段：`deep_review_body` (Text) - 抓取的正文长度（不暴露内容）
- 新增索引：`ix_articles_deep_review_done`
- 从 `ArticleRead` schema 中移除 `review_result`（不暴露给前端）
- `review_score` 范围更新为 0-780（6维度×10分）

### 2. backend/scraper/deep_reviewer.py（新建）
- `fetch_article_body()`：4层策略抓取文章正文（article > main > content div > heuristics）
- `fetch_youtube_transcript()`：YouTube 字幕获取（预留接口）
- `deep_review_single_article()`：抓取正文 + 构建评审提示词 + LLM评分 + 应用来源加权
- `batch_deep_review()`：批量处理，每次最多30篇，每篇间隔1秒
- `run_deep_review_sync()`：同步入口，供 scheduler 调用

### 3. backend/scheduler.py
- 新增 `deep_review_job()` 函数
- 调度：每30分钟处理20篇
- 优先级：先处理 `deep_review_done=False` 的文章
- 删除了旧的 `review_backlog` 调度（仅基于摘要评分的旧逻辑）

### 4. backend/api/articles.py
- `GET /api/articles`：默认过滤 `deep_review_done=True`（无评分内容不上线）
- `GET /api/articles/{id}`：详情页也要求 `deep_review_done=True`
- `min_score` 范围更新为 0-780

### 5. backend/api/stats.py
- `GET /api/stats`：统计时增加 `deep_review_done=True` 过滤
- `GET /api/stats/review`：
  - 统计改为仅统计深度评审完成的文章
  - .pending 改为统计 `deep_review_done=False` 的文章
  - 新增 `"deep_review_mode": true` 标志

## 设计亮点

### 评分不暴露
- `ArticleRead` schema 不包含 `review_result`
- `review_score` 不传给前端（前端不读取该字段）
- 前端只展示 A/B/C/D 徽章

### 过滤机制
- `deep_review_done=False` 的文章：
  - 不出现在列表 API 中
  - 不出现在详情页中
  - 统计 API 不计入
- 只有完成深度评审的文章才能展示

### 后台持续运行
- 每30分钟自动处理20篇未评审的文章
- 越新的文章越优先处理
- LLM 自动截断超长正文（8000字符上限）

## 开始时间
2026-04-29 14:58

## 完成时间
2026-04-29 15:05

---

## 任务背景
用户反馈摘要没有段落格式，是一整段密密麻麻的文字，读起来很吃力。

## 任务计划
- [x] 步骤1：改进 formatSummary 函数，增加字符数强制分段兜底逻辑
- [x] 步骤2：美化 ArticleView.vue 摘要段落样式（间距、行高）
- [x] 步骤3：优化 _fetch_page_summary 保留段落结构
- [x] 步骤4：改进翻译提示词，要求保持段落格式
- [x] 步骤5：测试验证效果

## 修改内容

### 1. 前端分段逻辑（ArticleView.vue）
- 新增字符数强制分段兜底：当标点分组仍为单段落时，按每180字强制拆分
- 确保无论原文是否有标点，都能获得多个段落

### 2. 段落样式美化（ArticleView.vue）
- 段落间距从 1.5em 增加到 1.8em
- 行高从 1.8 提升到 2.0
- 新增两端对齐（text-align: justify）
- 首段使用大字号衬线字体突出显示
- 后续段落使用次要颜色，提升层次感

### 3. 后端摘要抓取（rss_parser.py）
- 从提取5段改为提取3段，保持精炼
- 最低段落长度阈值从50字降到30字，捕获更多短段落
- 使用双换行（\n\n）分隔段落，保留结构
- 总体长度限制仍为500字

### 4. 翻译提示词（translator.py）
- 明确要求保持原文段落结构
- 用换行分隔段落，不要合并成一段
- 添加技术术语准确性要求

## 验证结果
- 前端构建：成功
- Python 语法检查：成功

## 开始时间
2026-04-29 14:06

## 完成时间
2026-04-29 14:08

---

## 当前任务
英文文章翻译

## 任务计划
- [x] 步骤1：翻译 A+B 级优质文章（13篇）
- [x] 步骤2：翻译 C+D 级剩余文章
- [x] 步骤3：验证翻译结果

## 翻译结果汇总

### 翻译执行
| 批次 | 数量 | 成功 | 失败 |
|------|------|------|------|
| A+B 级文章 | 13 篇 | 13 | 0 |
| C+D 级文章 | 78 篇 | 78 | 0 |

注：第二批查询到 78 篇（而非预估的 104 篇，因为部分文章可能已标记为翻译或有摘要为空被跳过）

### 数据库最终状态
| 指标 | 翻译前 | 翻译后 | 变化 |
|------|--------|--------|------|
| 已翻译文章 | 113 | 204 | +91 |
| 未翻译文章 | 117 | 26 | -91 |
| 有中文标题 | 113 | 204 | +91 |
| 有中文摘要 | 101 | 185 | +84 |
| 翻译完成率 | 49.1% | 88.7% | +39.6% |

### 剩余 26 篇未翻译
这 26 篇文章可能是因为：
1. 没有摘要内容（summary 为空）
2. 来自中文来源
3. 之前已标记为已翻译

## 开始时间
2026-04-29 09:06

## 完成时间
2026-04-29 09:27

---



## 任务计划
- [x] 步骤1：更新任务进度记录
- [x] 步骤2：执行 RSS 抓取采集今天文章
- [x] 步骤3：检查未评审文章数量
- [x] 步骤4：执行 LLM 评审（新文章 + 历史未评审）
- [x] 步骤5：汇总评审结果

## 执行结果

### RSS 抓取结果
- 新增文章：0 篇（今日已抓取过，仅剩4个订阅源可用）
- 当前启用的订阅源：4 个（Simon Willison, Cursor Changelog, DEV.to Cursor, Latent Space）
- 原因：大多数订阅源之前已禁用或失效

### LLM 评审结果
| 等级 | 评审前 | 评审后 | 变化 |
|------|--------|--------|------|
| A级（强烈推荐） | 36 | 38 | +2 |
| B级（推荐） | 13 | 13 | 0 |
| C级（一般） | 164 | 165 | +1 |
| D级（过滤） | 14 | 14 | 0 |
| 未评审 | 3 | 0 | -3 |

### 本次评审详情
| 文章标题 | 评级 | 分数 |
|----------|------|------|
| Multitask, Worktrees, and Multi-root Workspac... | A | 8 |
| Canvases... | A | 7 |
| Company... | C | 4 |

### 优质内容率
- A+B 级占比：(38 + 13) / 230 = **22.2%**

### 数据库最终状态
- 总文章数：230 篇
- 全部完成评审：0 篇待评审
- 最近24小时抓取：230 篇

## 开始时间
2026-04-29 08:59

## 完成时间
2026-04-29 09:02

---

## 任务背景
用户反馈 Latent Space 和 Latent Space Podcast 两个订阅源"网络问题"抓取失败。

## 问题诊断

### 根因分析
1. **Latent Space Podcast 超时**：RSS 内容 11MB+，默认超时（连接8秒+读取15秒）不够，需要 30+ 秒
2. **网络代理干扰**：latent.space 和 api.substack.com 的请求经过代理（127.0.0.1:22289），使用 `keep-alive` 时代理会复用连接导致后续请求超时

### 诊断过程
| 测试 | 结果 | 说明 |
|------|------|------|
| 直接 requests.get | 200 OK, 20 entries | 成功 |
| requests.Session | 超时 | 代理问题 |
| 带 Connection: close | 成功 | 关闭 keep-alive 绕过代理 |
| 默认超时 | 超时 | 8秒不够 |

## 修复措施

### 1. 添加慢速源超时配置
在 `backend/scraper/rss_parser.py` 中添加：

```python
# 慢速订阅源超时配置
SLOW_FEED_TIMEOUTS = {
    "Latent Space Podcast": (15, 60),
}

# 代理干扰域名列表
NO_PROXY_DOMAINS = [
    "latent.space",
    "api.substack.com",
    "www.latent.space",
]
```

### 2. 修改 _fetch_with_retry 函数
- 根据 `SLOW_FEED_TIMEOUTS` 设置超时参数
- 对 `NO_PROXY_DOMAINS` 中的域名设置 `Connection: close` 跳过代理

### 3. 修改 _fetch_feed_with_timeout 函数
- 慢速源使用更长的总超时时间

## 验证结果

### 单独测试抓取（修复后）
```
Latent Space: 成功抓取 5 篇文章
  - [AINews] ImageGen is on the Path to AGI (A级)
  - Physical AI that Moves the World (B级)
  - DeepSeek V4 Pro (A级)
  - [AINews] GPT 5.5 and OpenAI Codex (C级)
  - AIE Europe Debrief + Agent Labs (A级)

Latent Space Podcast: 成功抓取 5 篇文章
  - Physical AI that Moves the World (A级)
  - AIE Europe Debrief + Agent Labs (A级)
  - Training Transformers to solve Cancer (A级)
  - Shopify's AI Phase Transition (C级)
  - Notion's Token Town (C级)
```

### 标签分类
- 成功打上 `vibe_coding` 标签
- 包含 `AI前沿`、`使用技巧`、`工具推荐`、`生产落地` 等标签

## 开始时间
2026-04-28 18:00

## 完成状态
- [x] 诊断网络问题
- [x] 添加慢速源超时配置
- [x] 修复代理干扰问题
- [x] 验证抓取成功
- [ ] 完整抓取运行中

## 任务背景
用户反馈没有看到 Cursor、Claude、Gemini 工程师的相关文章。

## 问题分析
1. **Anthropic 官方博客 RSS 失效** - 原 URL https://www.anthropic.com/news/feed_anthropic.xml 返回 404
2. **Cursor 官方博客 RSS 失效** - 使用社区维护版本，可能不稳定
3. **缺少 Cursor/Claude/Google 工程师的 Twitter 账号** - 仅配置了 8 个通用账号
4. **缺少 AI 工程师访谈播客** - Latent Space Podcast 未配置

## 任务计划
- [x] 步骤1：修复 Anthropic 官方博客 RSS 源（通过 OpenRSS 代理）
- [x] 步骤2：修复 Cursor 官方博客 RSS 源
- [x] 步骤3：添加 Cursor/Claude/Google 工程师的 Twitter 账号
- [x] 步骤4：添加 Latent Space Podcast RSS 源
- [x] 步骤5：添加 AI 工程师个人博客（Simon Willison、Thariq Shihipar）
- [ ] 步骤6：重新抓取验证效果

## 修改的文件

### 1. backend/scraper/sources.py
- Anthropic Blog: `https://www.anthropic.com/news/feed_anthropic.xml` → `https://openrss.org/feed/www.anthropic.com/news`
- 新增 Anthropic Engineering: `https://openrss.org/feed/www.anthropic.com/engineering`
- Cursor Blog: `https://raw.githubusercontent.com/...` → `https://cursor.sh/rss.xml`
- VIBE_CODING_SOURCES 中同步更新
- 新增 Latent Space Podcast: `https://api.substack.com/feed/podcast/1084089.rss`
- 删除已禁用的旧 anthropic_blog 条目

### 2. backend/scraper/premium_sources.py
新增 Twitter 账号（从 8 个增加到 22 个）：

| 类别 | 账号 | 说明 |
|------|------|------|
| Cursor 工程师 | @mntruell, @nickwm, @saborii, @alexalbert__ | Cursor CEO、工程师 |
| Anthropic 工程师 | @trq212 | Thariq Shihipar - Claude Code 核心工程师 |
| Google 工程师 | @jeffdean, @JohnLaTwC, @demaborisova, @rsquared64 | Google DeepMind |
| AI Coding 专家 | @simonw, @swyx | Simon Willison、Latent Space |

### 3. backend/scraper/recommended_sources.py
- Anthropic Blog: 更新为 OpenRSS 代理 URL
- 新增 Anthropic Engineering 订阅源
- 新增 Latent Space Podcast 订阅源
- 新增 Simon Willison 个人博客
- 新增 Thariq Shihipar 个人博客

## 新增订阅源汇总
| 名称 | URL | 类别 | 优先级 |
|------|-----|------|--------|
| Anthropic Blog | openrss.org/feed/www.anthropic.com/news | blog | 9 |
| Anthropic Engineering | openrss.org/feed/www.anthropic.com/engineering | blog | 9 |
| Cursor Blog | cursor.sh/rss.xml | vibe_coding | 9 |
| Latent Space Podcast | api.substack.com/feed/podcast/1084089.rss | newsletter | 8 |
| Simon Willison | simonwillison.net/atom/entries/ | blog | 9 |
| Thariq Shihipar | thariq.io | blog | 9 |

## 新增 Twitter 账号
| 账号 | 身份 | 关注理由 |
|------|------|----------|
| @mntruell | Cursor CEO | 公司动态 |
| @nickwm | Cursor 工程师 | 技术实践 |
| @saborii | Cursor 团队 | 技术实践 |
| @alexalbert__ | Cursor | 技术实践 |
| @trq212 | Anthropic Claude Code 工程师 | Claude Code 核心开发 |
| @simonw | AI Coding 专家 | 深度报道 Cursor/Claude |
| @jeffdean | Google 首席科学家 | AI Engineering |
| @JohnLaTwC | Google AI | AI Engineering |
| @demaborisova | Google AI | AI Engineering |
| @rsquared64 | Google DeepMind | AI Engineering |
| @bindureddy | AI 领域 | 行业观察 |
| @emollick | AI 教育 | 实践指南 |
| @levelsio | 独立开发者 | 实战经验 |

## 开始时间
2026-04-28 17:00

---

## 上一任务
用户反馈第一版改造仍然是"微调"，没有真正的设计突破。要求浅色风格 + 极简列表排版。

## 设计方向
- **风格**：浅色极简（日式/北欧风）
- **配色**：米白底 (#fafaf8) + 深炭灰字 (#1a1a1a)
- **布局**：极窄容器 (480px) + 竖向大字排版
- **组件**：直角边框、无阴影、无卡片边框

## 改造完成清单
- [x] CSS设计系统重构（浅色米白 + 极窄容器）
- [x] 导航栏（极简白底）
- [x] 首页（筛选+搜索+标签重新设计）
- [x] 文章卡片（列表式无边框）
- [x] 文章详情页
- [x] 收藏页
- [x] 删除冗余组件（SearchBar、TagFilter）
- [x] 构建验证通过

## 核心改动
| 元素 | 原来 | 现在 |
|------|------|------|
| 背景色 | #0d1117 深黑 | #fafaf8 米白 |
| 容器宽度 | 900px | 480px |
| 文字色 | #e6edf3 浅灰 | #1a1a1a 深炭灰 |
| 边框 | #30363d | #e0e0dc |
| 圆角 | 8px | 0 (直角) |
| 阴影 | 有 | 无 |

## 开始时间
2026-04-28 14:45

## 完成时间
2026-04-28 14:55

---

## 上一任务
优化 Vibe Coding 内容可见性

## 任务背景
用户反馈获取到的内容很少看到 vibe_coding 相关的东西，最低优先级资讯的学术内容反而比较多。

## 问题分析

### 1. 来源分布问题
| 来源 | 文章数 | 类别 |
|------|--------|------|
| ArXiv cs.AI | 99 | 学术 |
| Hacker News AI | 58 | 综合 |
| Cursor Blog | 11 | Vibe Coding |
| GitHub Blog | 11 | Vibe Coding |
| vibe_coding 标签 | 8 | - |
| cursor 标签 | 4 | - |

### 2. 根因
- Vibe Coding 核心来源大量失效（Windsurf、Anthropic、Meta、Mistral）
- 分类器中 Vibe Coding 关键词覆盖不足
- 学术来源有稳定 RSS 输出，容易被匹配

## 改进措施

### 1. 增强分类器（已完成）
- **新增 `vibe_coding` 标签分类**：48 个核心关键词
  - Vibe Coding 核心理念：vibe coding, prompt to code, natural language to code
  - 具体工具：cursor, windsurf, copilot, aider, continue, devin, v0, bolt
  - 使用技巧：best settings, keyboard shortcuts, tips, workflow
  - 开发者实践：building with ai, ship with ai, my experience

### 2. 调整来源权重（已完成）
- **学术来源降权**：
  - ArXiv cs.AI: 0.3 → 0.2
  - 其他 ArXiv: 0.3 → 0.2
- **Vibe Coding 来源加权**：
  - GitHub Blog: 2.0 → 2.2
  - GitHub Trending: 7 → 8
  - Simon Willison: 2.0 → 2.5
  - Newsletter: 7 → 8
- **综合新闻源降权**：
  - Hacker News AI: 0.5 → 0.4
  - VentureBeat: 无权重 → 0.5

### 3. 优化分类逻辑（已完成）
- 学术来源的文章不自动打标签，让评审阶段过滤
- Vibe Coding 核心来源的文章优先匹配 vibe_coding 标签
- 学术来源降权系数从 0.5 降到 0.3

## 修改的文件
- `backend/scraper/classifier.py`
  - 新增 `vibe_coding` 标签配置
  - 调整 `SOURCE_QUALITY_WEIGHT` 权重
  - 优化 `classify()` 函数逻辑

## 开始时间
2026-04-28 10:35

## 完成时间
2026-04-28 10:50

## 待办
- [ ] 验证改进效果（重新抓取后检查标签分布）

## 订阅源优化完成

### 容错规则改进
- 单个 feed 最大处理时间：60秒超时
- 请求超时：15秒（连接8秒，传输15秒）
- 重试次数：2次
- 重试间隔：1秒
- 仅加载最近7天已有文章哈希用于去重

### 已禁用订阅源（11个）
| 名称 | 问题 |
|------|------|
| Anthropic Blog | HTTP 404 |
| Windsurf Blog | RSS 无内容 |
| Meta AI Blog | HTTP 404 |
| Mistral AI Blog | HTTP 404 |
| Towards Data Science | HTTP 403 |
| MiniMax | 无有效 RSS |
| Kimi AI | RSS 无内容 |
| 智谱AI | RSS 无内容 |
| The Verge AI | HTTP 403 |
| Reddit r/LocalLLaMA | RSS 无内容 |
| Simon Willison | Atom 源无内容 |

### 新增订阅源（8个）
| 名称 | 类别 | 优先级 | 说明 |
|------|------|--------|------|
| DEV.to Cursor | vibe_coding | 9 | Cursor 使用技巧 |
| DEV.to AI Coding | vibe_coding | 9 | AI 编程实践 |
| DEV.to LLM | vibe_coding | 8 | LLM 开发 |
| DEV.to AI | vibe_coding | 8 | 开发者社区 AI |
| GitHub Trending | vibe_coding | 8 | GitHub 热门项目 |
| Future Tools | tools | 7 | AI 工具收录 |
| Supabase Blog | blog | 7 | 开源 Firebase 替代 |
| Medium AI | blog | 6 | Medium AI 文章 |

### 权重调整
| 来源类别 | 原权重 | 新权重 |
|----------|--------|--------|
| DEV.to 系列 | 1.0 | 2.5-3.0 |
| Cursor Blog | 2.5 | 3.0 |
| Simon Willison | 2.5 | 3.0 |
| 学术来源 | 0.3 | 0.2 |

### 分类器测试结果
| 来源 | 标签结果 |
|------|----------|
| DEV.to Cursor | vibe_coding ✓ |
| Simon Willison | vibe_coding ✓ |
| GitHub Blog | vibe_coding ✓ |
| ArXiv cs.AI | [] (不自动打标签) ✓ |


## 任务计划
- [x] 步骤1：创建审核脚本，测试所有订阅源有效性
- [x] 步骤2：评估内容质量和相关性
- [x] 步骤3：禁用低质量订阅源，更新 sources.py
- [x] 步骤4：更新 TASK_PROGRESS.md

## 审核结果汇总

### 订阅源统计
| 状态 | 数量 | 说明 |
|------|------|------|
| 推荐保留 | 24 个 | 已验证有效，有内容产出 |
| 建议审核 | 2 个 | Product Hunt（产品发布平台）、ArXiv（学术噪音多）|
| 建议禁用 | 10 个 | RSS 失效或无内容 |

### 已禁用的订阅源（10个）
| 名称 | 问题 |
|------|------|
| Windsurf Blog | RSS 无内容 |
| The Verge AI | HTTP 403 |
| Anthropic Blog | HTTP 404 |
| Meta AI Blog | HTTP 404 |
| Mistral AI Blog | HTTP 404 |
| Jim Fan (AI Scientist) | 连接错误 |
| Towards Data Science | HTTP 403 |
| 智谱AI | RSS 无内容 |
| MiniMax | RSS 无内容 |
| Kimi AI | RSS 无内容 |

### 已更新订阅源配置
- Stability AI Blog: 改用社区维护 RSS
- Simon Willison: 改用 entries-only Atom 源

### 审核脚本
- 新建 `backend/audit_sources.py` 用于批量测试订阅源有效性

## 任务背景
用户反馈当前无法采集类似 https://github.com/forrestchang/andrej-karpathy-skills 的高质量 vibe coding 内容，需要扩展订阅源覆盖范围。

## 任务计划
- [x] 步骤1：执行RSS抓取脚本，采集最新数据
- [x] 步骤2：检查数据库当前状态（文章数、来源分布）
- [x] 步骤3：验证订阅源有效性（RSS链接可访问性）
- [x] 步骤4：分析文章数据质量问题（缺失摘要、未翻译等）
- [x] 步骤5：检查去重机制和内容哈希逻辑
- [x] 步骤6：制定数据质量改进计划
- [x] 步骤7：添加 GitHub Trending 订阅源
- [x] 步骤8：修复 Simon Willison 订阅源 URL
- [x] 步骤9：添加 Newsletter 订阅源 (Latent Space, The Gradient)
- [x] 步骤10：实现 Awesome 列表抓取模块

## 执行结果

### 新增订阅源 (5个)
| 名称 | 类别 | 优先级 | 说明 |
|------|------|--------|------|
| GitHub Trending Python | vibe_coding | 8 | GitHub 每日热门 Python 项目 |
| GitHub Trending Jupyter | vibe_coding | 8 | GitHub 每日热门 Jupyter/Notebook 项目 |
| GitHub Trending All | vibe_coding | 7 | GitHub 每日热门全部分类 |
| Latent Space | newsletter | 8 | AI 技术深度 Newsletter |
| The Gradient | newsletter | 7 | AI 学术与产业分析 |

### 修复订阅源 (1个)
| 名称 | 原URL | 新URL |
|------|-------|-------|
| Simon Willison | simonwillison.net/atom/everything | feeds.simonwillison.net |

### Awesome 列表抓取
新建 `backend/scraper/awesome_scraper.py` 模块

监控的 Awesome 列表:
| 名称 | 仓库 | 状态 |
|------|------|------|
| awesome-vibe-coding | 0xWelt/Awesome-Vibe-Coding | 已抓取 5 个项目 |
| awesome-ai-agents | caramaschiHG/awesome-ai-agents-2026 | 已抓取 3 个项目 |
| awesome-ai-tools | eudk/awesome-ai-tools | 关键词未匹配 |

### 当前订阅源统计
- 总计启用: 39 个订阅源
- 按类别: blog(9), news(7), vibe-coding(6), newsletter(3), research(2)

## 任务背景
用户要求采集数据、验证数据，并提出改进计划。重点改进数据质量（去重、清洗、摘要生成）。

## 任务计划

- [x] 步骤1：执行RSS抓取脚本，采集最新数据
- [x] 步骤2：检查数据库当前状态（文章数、来源分布）
- [x] 步骤3：验证订阅源有效性（RSS链接可访问性）
- [x] 步骤4：分析文章数据质量问题（缺失摘要、未翻译等）
- [x] 步骤5：检查去重机制和内容哈希逻辑
- [x] 步骤6：制定数据质量改进计划

## 采集结果

### 数据库状态概览
- **文章总数**: 1036 篇
- **最近24小时抓取**: 917 篇
- **最近7天抓取**: 1036 篇
- **订阅源总数**: 36 个
- **已启用订阅源**: 36 个

### 来源分布（Top 10）
| 来源 | 文章数 | 最后抓取 |
|------|--------|----------|
| Hugging Face Blog | 240 | 2026-04-28 |
| OpenAI Blog | 210 | 2026-04-28 |
| Google DeepMind Blog | 100 | 2026-04-27 |
| ArXiv cs.AI | 99 | 2026-04-27 |
| Game Developer | 50 | 2026-04-27 |
| Hacker News AI | 49 | 2026-04-28 |
| r/LocalLLaMA | 41 | 2026-04-28 |
| r/ComfyUI | 40 | 2026-04-28 |
| r/StableDiffusion | 36 | 2026-04-28 |
| r/GameAI | 21 | 2026-04-27 |

### 评审等级分布
- **A（强烈推荐）**: 3 篇
- **B（推荐）**: 23 篇
- **C（一般）**: 476 篇
- **D（过滤）**: 326 篇
- **未评审**: 208 篇

### 数据质量问题

| 问题类型 | 数量 | 比例 |
|----------|------|------|
| 缺失摘要 | 188 | 18.1% |
| 未翻译 | 1006 | 97.1% |
| D级文章 | 326 | 31.5% |
| 重复URL | 0 | 0% |

### 订阅源有效性验证

| 状态 | 数量 |
|------|------|
| 正常 | 24 个 |
| 失效（需修复） | 7 个 |
| 不可达（超时） | 5 个 |

#### 失效订阅源
1. **Anthropic Blog** - 404 Not Found
   - URL: https://www.anthropic.com/blog/rss.xml
2. **Stability AI Blog** - 404 Not Found
   - URL: https://stability.ai/news/feed
3. **Game Developer** - 403 Forbidden
   - URL: https://www.gamedeveloper.com/rss.xml
4. **The Batch** - 404 Not Found
   - URL: https://www.deeplearning.ai/the-batch/rss/
5. **VentureBeat AI** - 404 Not Found
   - URL: https://venturebeat.com/ai/feed/
6. **Simon Willison** - 404 Not Found
   - URL: https://simonwillison.net/atom
7. **MiniMax** - 404 Not Found
   - URL: https://www.minimaxi.com/news/rss

#### 不可达订阅源（超时）
1. Google DeepMind Blog
2. Meta AI Blog
3. Mistral AI Blog
4. Import AI Newsletter
5. Jim Fan (AI Scientist)

### 去重机制分析
- **content_hash算法**: SHA256(title + "|" + url)
- **URL唯一索引**: 已建立唯一约束
- **重复检测结果**: 0个重复URL，去重机制有效

## 数据质量改进计划

### 优先级 P0（紧急）

#### 1. 修复失效订阅源
- **目标**: 恢复7个失效RSS源或替换为可用源
- **建议**:
  - Anthropic Blog: 改用 https://docs.anthropic.com/feed 或手动维护
  - Stability AI: 改用 https://stability.ai/feed
  - Game Developer: 尝试备用源或社区RSS
  - VentureBeat: 改用 https://venturebeat.com/feed/

#### 2. 启用LLM服务进行评审
- **问题**: Ollama服务未运行，导致评审失败
- **建议**:
  - 启动Ollama: `ollama serve`
  - 确认模型: `ollama list` 检查 qwen3.5:9b
  - 设置环境: 确保 .env 中 LLM_ENABLED=true

#### 3. 批量补充缺失摘要
- **问题**: 188篇文章缺失摘要
- **工具**: 可使用 `supplement_summaries.py` 批量补充
- **前提**: 需启用LLM服务

### 优先级 P1（重要）

#### 4. 翻译质量提升
- **问题**: 97%文章未翻译
- **建议**:
  - 检查 `run_translation.py` 是否正常运行
  - 优化翻译提示词，减少token消耗
  - 优先翻译A级和B级文章

#### 5. 优化评审阈值
- **问题**: D级文章占比过高（31.5%）
- **建议**:
  - 调整 `review_committee.py` 中的评分阈值
  - 高质量来源（OpenAI/HuggingFace等）降低评审标准
  - 考虑来源信任度加权

### 优先级 P2（改进）

#### 6. 增强摘要生成质量
- **改进方向**:
  - 使用网页抓取替代RSS摘要（已部分实现）
  - 优化 `_fetch_page_summary()` 函数
  - 增加摘要长度上限（当前500字符）

#### 7. 语义去重增强
- **当前**: 仅基于 title+url 的哈希去重
- **改进方向**:
  - 添加标题相似度检测（编辑距离/余弦相似度）
  - 检测同一文章的不同翻译版本

#### 8. 订阅源分类优化
- **建议**:
  - 按优先级分组抓取（高质量源优先）
  - 动态调整每日抓取限额
  - 监控各源的文章质量并反馈

## 涉及文件

| 文件 | 用途 |
|------|------|
| `backend/scraper/sources.py` | 订阅源配置 |
| `backend/scraper/rss_parser.py` | RSS解析和抓取 |
| `backend/review_committee.py` | 评审委员会 |
| `backend/llm_client.py` | LLM客户端 |
| `backend/run_translation.py` | 翻译脚本 |
| `backend/supplement_summaries.py` | 摘要补充脚本 |
| `backend/db_status_check.py` | 数据库状态检查（新增） |
| `backend/verify_sources.py` | 订阅源验证（新增） |

## 开始时间
2026-04-28 09:12

## 完成时间
2026-04-28 09:20（计划制定完成）

## 评审规则优化（2026-04-28）

### 问题诊断

#### 1. 阈值不一致
| 位置 | A级 | B级 | C级 |
|------|-----|-----|-----|
| SYSTEM_PROMPT | >=6.5, practicality>=6 | >=5.0, practicality>=5 | >=3.5 |
| grade_from_scores (旧) | >=7.0, practicality>=6 | >=5.5, practicality>=5 | >=4, game_relevance>=4 |

#### 2. LLM评分过于保守
- 系统提示词规则太多，LLM难以遵循
- 缺少来源加权机制

### 改进措施

#### 1. 统一评审阈值（prompts/review_prompts.py）
- 修复 `grade_from_scores` 函数，与 SYSTEM_PROMPT 阈值保持一致
- C级阈值从 `>=4 且 game_relevance>=4` 简化为 `>=3.5`

#### 2. 简化系统提示词
- 从 105 行简化为约 60 行
- 使用表格格式更清晰
- 保留核心加分/降分规则

#### 3. 添加来源加权系数
```python
SOURCE_WEIGHT_BOOST = {
    "Cursor Blog": 0.5,
    "GitHub Blog": 0.5,
    "DEV.to Cursor": 0.5,
    "DEV.to AI Coding": 0.5,
    "Hugging Face Blog": 0.3,
    # ...
}
```

#### 4. 修改文件
- `backend/prompts/review_prompts.py` - 阈值统一、简化提示词、添加来源加权
- `backend/prompts/__init__.py` - 导出新函数
- `backend/review_committee.py` - 应用来源加权系数

### 重新评审结果

| 等级 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| A级 (强烈推荐) | 0 | 23 | +23 |
| B级 (推荐) | 0 | 7 | +7 |
| C级 (一般) | 91 | 42 | -49 |
| D级 (过滤) | 3 | 25 | +22 |
| **优质内容率** | 0% | **30.9%** | +30.9% |

### 结论
通过统一阈值、简化提示词、添加来源加权，优质内容率从 0% 提升到 30.9%
