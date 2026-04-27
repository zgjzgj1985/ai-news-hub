# 评审委员会升级计划

## 目标

将现有的**规则引擎评审系统**升级为**本地LLM驱动（Qwen3 8B）**的智能评审系统，对AI情报站推送的内容进行严格评审，判断是否符合工具开发的设计目的。

---

## 一、现状分析

### 1.1 现有系统

- **评审方式**：基于正则匹配和关键词规则的规则引擎
- **评审专家**：5位虚拟专家（相关性、实用性、时效性、深度、原创性）
- **评审结果**：A/B/C/D 四级评级

### 1.2 问题

1. 规则引擎无法理解语义，只能做表层匹配
2. 无法判断内容的**实用价值**和**开发参考性**
3. 无法识别高质量教程与低质量水文
4. 无法评估内容是否符合**工具开发**的核心目的

### 1.3 目标系统

- **评审方式**：本地LLM（Qwen3 8B）语义理解评审
- **评审标准**：严格围绕"工具开发"目的
- **集成方式**：通过 Ollama API 调用

---

## 二、技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     评审委员会 (LLM)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  CTO评审    │    │ 架构师评审  │    │ 开发者评审  │   │
│  │ (技术深度)  │    │ (实用性)    │    │ (可操作性)  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │ 毒舌编辑    │    │ 时效守门员  │                        │
│  │ (内容质量)  │    │ (新鲜度)    │                        │
│  └─────────────┘    └─────────────┘                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   LLM调用层 (Ollama)                       │
├─────────────────────────────────────────────────────────────┤
│                   本地模型: Qwen3 8B                        │
│                   接口: http://localhost:11434              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、实现计划

### 3.1 第一步：创建LLM调用模块

**文件**：`backend/llm_client.py`

**功能**：
- 连接 Ollama API
- 支持流式/非流式响应
- 支持 JSON 模式输出
- 支持自定义 system prompt
- 实现重试和错误处理

**关键代码结构**：

```python
class LLMClient:
    def __init__(self, base_url="http://localhost:11434", model="qwen3:8b")
    def chat(self, messages: list, json_mode=True) -> dict
    def generate(self, prompt: str, system: str = "") -> str
    def is_available() -> bool  # 检查服务是否可用
```

### 3.2 第二步：设计评审Prompt

**文件**：`backend/prompts/review_prompts.py`

**评审角色**：
1. **CTO（技术总监）** - 评估技术深度和创新性
2. **架构师** - 评估架构设计和工程价值
3. **全栈开发者** - 评估代码质量和可操作性
4. **产品经理** - 评估内容质量和受众价值
5. **守门员** - 评估时效性和相关性

**Prompt设计原则**：
- 严格、犀利、不留情面
- 拒绝水文、标题党、广告内容
- 聚焦工具开发目的

### 3.3 第三步：重构评审委员会

**文件**：`backend/review_committee.py`（重构）

**改进点**：
- 将规则引擎替换为 LLM 调用
- 保留原有的数据结构和API接口
- 实现异步评审（不阻塞主流程）
- 添加批量评审支持

**评审流程**：
1. 文章进入评审队列
2. 构建评审Prompt（包含文章标题、摘要、来源）
3. 调用LLM获取评审结果
4. 解析JSON结果，更新数据库
5. 返回评审结果

### 3.4 第四步：配置管理

**文件**：`backend/.env`

**新增配置**：
```
# LLM评审配置
LLM_ENABLED=true
LLM_MODEL=qwen3:8b
LLM_BASE_URL=http://localhost:11434
LLM_TIMEOUT=60
LLM_TEMPERATURE=0.1  # 低温度保证稳定性

# 评审配置
REVIEW_BATCH_SIZE=10  # 批量评审大小
REVIEW_MAX_RETRIES=3   # 最大重试次数
```

### 3.5 第五步：API增强

**文件**：`backend/api/review.py`（增强）

**新增端点**：
- `GET /api/review/llm-status` - 检查LLM连接状态
- `POST /api/review/llm-article/{id}` - 单独使用LLM评审某篇文章
- `POST /api/review/llm-batch` - 批量LLM评审

---

## 四、详细实现

### 4.1 LLM调用模块

```python
# backend/llm_client.py

class LLMClient:
    """本地LLM客户端 - 连接Ollama/Qwen3 8B"""

    DEFAULT_MODEL = "qwen3:8b"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, model: str = None, base_url: str = None, timeout: int = 60):
        self.model = model or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("LLM_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout

    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    async def areview(self, title: str, summary: str, source: str) -> dict:
        """异步LLM评审"""
        # 构建评审Prompt
        prompt = build_review_prompt(title, summary, source)
        # 调用LLM
        response = await self._chat_async(prompt)
        # 解析结果
        return parse_review_response(response)
```

### 4.2 评审Prompt设计

```python
# backend/prompts/review_prompts.py

SYSTEM_PROMPT = """你是一个犀利的评审委员会，对AI工具开发相关内容进行严格评审。

你的评审标准极其严格：
1. 只推荐对"工具开发"有直接帮助的内容
2. 拒绝水文、标题党、重复内容
3. 要求有实质性技术内容或可操作资源
4. 评估时效性，过时内容降级处理

输出必须是JSON格式，包含：
- grade: A/B/C/D
- scores: {tech_depth, practicality, novelty, usefulness}
- verdict: 简短裁决理由
- recommendation: 是否推荐及理由
"""

def build_review_prompt(title: str, summary: str, source: str) -> str:
    return f"""请严格评审以下文章：

标题：{title}
来源：{source}
摘要：{summary}

评审维度：
1. tech_depth：技术深度（0-10）
2. practicality：实用性（0-10）
3. novelty：新颖性（0-10）
4. usefulness：对工具开发的帮助度（0-10）

最终评级标准：
- A级：4项平均>=7，且至少3项>=7
- B级：4项平均>=5，且至少2项>=5
- C级：平均>=3
- D级：低于C级标准
"""
```

### 4.3 评审委员会重构

```python
# backend/review_committee.py

class ReviewCommittee:
    """LLM驱动的评审委员会"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.use_llm = os.getenv("LLM_ENABLED", "false").lower() == "true"

    async def areview(self, article) -> ReviewResult:
        """异步LLM评审"""
        if not self.use_llm or not self.llm_client.is_available():
            # 回退到规则引擎
            return self._rule_based_review(article)

        try:
            result = await self.llm_client.areview(
                title=article.title,
                summary=article.summary or "",
                source=article.source_name
            )
            return self._parse_llm_result(result, article)
        except Exception as e:
            # LLM失败时回退
            return self._rule_based_review(article)
```

---

## 五、数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   RSS抓取   │ -> │   分类器    │ -> │  评审队列   │ -> │   LLM评审   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   前端展示   │ <-   过滤显示    │ <-   评级筛选   │ <- │  结果入库   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 六、文件清单

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `backend/llm_client.py` | 新建 | LLM调用模块 |
| `backend/prompts/review_prompts.py` | 新建 | 评审Prompt管理 |
| `backend/review_committee.py` | 重构 | LLM驱动的评审委员会 |
| `backend/.env` | 修改 | 添加LLM配置 |
| `backend/api/review.py` | 增强 | 添加LLM状态检查端点 |
| `backend/requirements.txt` | 修改 | 添加httpx异步支持 |

---

## 七、依赖项

```
# 新增依赖
httpx>=0.27.0  # 异步HTTP客户端（已有）

# 本地服务
# - Ollama 或 LM Studio
# - Qwen3 8B 模型
```

---

## 八、部署要求

### 8.1 Ollama配置

```bash
# 安装Ollama
# 下载Qwen3 8B模型
ollama pull qwen3:8b

# 启动Ollama服务
ollama serve
```

### 8.2 环境验证

```bash
# 检查Ollama状态
curl http://localhost:11434/api/tags

# 测试模型
ollama run qwen3:8b "Hello"
```

---

## 九、测试计划

1. **单元测试**：LLM客户端、P解析逻辑
2. **集成测试**：Ollama连接、评审流程
3. **对比测试**：规则引擎 vs LLM评审结果
4. **手动测试**：抽查评审结果质量

---

## 十、预期效果

- 评审结果更加语义化、智能化
- 过滤掉更多无价值内容
- 提高内容与"工具开发"目的的匹配度
- 评审理由更加详细、有说服力

---

## 十一、风险与对策

| 风险 | 对策 |
|------|------|
| LLM响应慢 | 添加超时，使用异步处理 |
| LLM不可用 | 回退到规则引擎 |
| JSON解析失败 | 添加重试和默认兜底 |
| 模型质量差 | 调整Prompt和Temperature |
