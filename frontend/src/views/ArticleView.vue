<template>
  <div class="article-view">
    <div class="container">

      <!-- Loading -->
      <div v-if="loading" class="skeleton-detail">
        <div class="skeleton-line" style="width:30%;height:12px;"></div>
        <div class="skeleton-line" style="width:80%;height:28px;margin-top:16px;"></div>
        <div class="skeleton-line" style="width:60%;height:28px;"></div>
        <div class="skeleton-line" style="width:40%;height:16px;margin-top:24px;"></div>
        <div v-for="i in 5" :key="i" class="skeleton-line" :style="{width: ['100%','95%','88%','100%','70%'][i-1], height:'14px', marginTop:'12px'}"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="empty-state">
        <p class="empty-title">加载失败</p>
        <p class="empty-desc">{{ error }}</p>
        <button class="btn btn-ghost" @click="load">重试</button>
      </div>

      <!-- Article -->
      <article v-else-if="article" class="article-detail">
        <div class="article-header">
          <div class="article-meta">
            <span class="source-badge">{{ article.source_name }}</span>
            <span class="text-muted">&bull;</span>
            <span class="text-secondary text-sm">{{ formatDate(article.published_at) }}</span>
            <span class="text-muted">&bull;</span>
            <span class="text-secondary text-sm">{{ article.read_time_minutes }} min read</span>
          </div>

          <div class="article-actions">
            <button
              class="btn"
              :class="article.is_bookmarked ? 'btn-primary' : 'btn-ghost'"
              @click="handleBookmark"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" :fill="article.is_bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
              </svg>
              {{ article.is_bookmarked ? '已收藏' : '收藏' }}
            </button>
            <a :href="article.url" target="_blank" rel="noopener noreferrer" class="btn btn-ghost">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              原文链接
            </a>
          </div>
        </div>

        <h1 class="article-title">{{ displayTitle }}</h1>
        <p v-if="displayTitle && article.title_zh && displayTitle !== article.title" class="original-title">
          原文: {{ article.title }}
        </p>

        <div class="article-tags">
          <span
            v-for="tag in article.tags"
            :key="tag"
            class="tag"
            :class="tagClass(tag)"
          >{{ tag }}</span>
          <button
            v-if="article.summary && !article.summary_zh"
            class="btn btn-ghost btn-sm translate-btn"
            @click="handleTranslate"
            :disabled="translating"
            title="翻译摘要"
          >
            <svg v-if="translating" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0 0 14.07 6H17V4h-7V2H8v2H1v2h11.17A15.9 15.9 0 0 1 4.17 12l1.47 1.47"/>
              <path d="M21 11.5v2H11V2h2v9"/>
              <path d="M11 22v-2h2v2h-2"/>
            </svg>
            {{ translating ? '翻译中...' : '翻译摘要' }}
          </button>
          <span v-else-if="article.summary_zh" class="tag tag-translated">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0 0 14.07 6H17V4h-7V2H8v2H1v2h11.17A15.9 15.9 0 0 1 4.17 12l1.47 1.47"/>
              <path d="M21 11.5v2H11V2h2v9"/>
              <path d="M11 22v-2h2v2h-2"/>
            </svg>
            已翻译
          </span>
        </div>

        <div class="summary-tabs" v-if="article.summary && article.summary_zh">
          <button
            class="tab-btn"
            :class="{ active: activeSummary === 'zh' }"
            @click="activeSummary = 'zh'"
          >中文</button>
          <button
            class="tab-btn"
            :class="{ active: activeSummary === 'en' }"
            @click="activeSummary = 'en'"
          >英文</button>
        </div>

        <div v-if="displaySummaryText" class="article-body" v-html="formatSummary(displaySummaryText)"></div>
        <div v-else-if="article.summary" class="article-body" v-html="formatSummary(article.summary)"></div>
        <div v-else class="no-summary-detail">
          <div class="no-summary-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <p class="no-summary-title">该来源暂不支持摘要抓取</p>
          <p class="no-summary-desc">当前文章来自 {{ article.source_name }}，暂无摘要内容</p>
          <a :href="article.url" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            直接查看原文
          </a>
        </div>

        <div class="article-footer">
          <router-link to="/" class="btn btn-ghost">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            返回资讯列表
          </router-link>
        </div>
      </article>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchArticle, toggleBookmark, translateArticle } from '@/api'

const route = useRoute()
const article = ref(null)
const loading = ref(true)
const error = ref(null)
const translating = ref(false)
const activeSummary = ref('zh')

const TAG_MAP = {
  'AI前沿': 'tag-ai-frontier',
  '游戏美术': 'tag-game-art',
  '游戏策划': 'tag-game-design',
  '使用技巧': 'tag-tips',
  '工具推荐': 'tag-tools',
}

function tagClass(tag) {
  return TAG_MAP[tag] || 'tag-default'
}

// 根据选择的语言显示摘要
const displaySummaryText = computed(() => {
  if (!article.value) return ''
  if (activeSummary.value === 'zh' && article.value.summary_zh) {
    return article.value.summary_zh
  }
  if (activeSummary.value === 'en' && article.value.summary) {
    return article.value.summary
  }
  return article.value.summary_zh || article.value.summary || ''
})

// 优先显示翻译后的中文标题
const displayTitle = computed(() => {
  if (!article.value) return ''
  return article.value.title_zh || article.value.title
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

// 格式化摘要文本，智能分段落，提升阅读体验
function formatSummary(text) {
  if (!text) return ''

  // 移除无意义前缀
  text = text.replace(/^Back to Articles\s*/i, '').trim()

  // 如果文本本身包含HTML标签，清理并保留基本格式
  if (text.includes('<p') || text.includes('<br') || text.includes('<div')) {
    // 清理标签但保留换行
    return text
      .replace(/<p[^>]*>/gi, '<p>')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '</p>\n')
      .replace(/<[^>]+>/g, '')
      .trim()
  }

  // 清理多余空白和特殊字符
  text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  text = text.replace(/\t/g, ' ')
  text = text.replace(/\u00a0/g, ' ')  // 不间断空格
  text = text.replace(/[ ]{2,}/g, ' ')

  // 策略1: 尝试按Markdown标题或数字列表分段
  let paragraphs = text.split(/\n(?=#{1,6}\s|\d+[.)、]\s)/)

  // 策略2: 按双换行分段
  if (paragraphs.length < 2) {
    paragraphs = text.split(/\n{2,}/)
  }

  // 策略3: 按单换行分段但识别短行（如列表项）
  if (paragraphs.length < 2) {
    paragraphs = splitByLines(text)
  }

  // 策略4: 如果段落太少，按句子智能分段
  if (paragraphs.length < 2) {
    paragraphs = smartSplitParagraphs(text)
  }

  // 过滤空段落并转HTML
  const cleanParagraphs = paragraphs
    .map(p => p.trim())
    .filter(p => p.length > 10)  // 过滤太短的段落
    .map((p, i) => `<p class="${i === 0 ? 'first' : ''}">${escapeHtml(p)}</p>`)

  return cleanParagraphs.join('')
}

// 按行智能分段，合并短行
function splitByLines(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0)
  const paragraphs = []
  let current = []
  let currentLen = 0
  const MIN_PARAGRAPH_CHARS = 80  // 每段至少80字符才独立成段

  lines.forEach(line => {
    const isListItem = /^[•\-\*\d+[.)、]\s]/.test(line)
    const isShortLine = line.length < 40

    if (isListItem || isShortLine) {
      // 列表项或短行，合并到当前段落
      current.push(line)
      currentLen += line.length
    } else {
      // 普通段落行
      if (currentLen > 0) {
        // 先输出累积的列表/短行
        if (currentLen >= MIN_PARAGRAPH_CHARS) {
          paragraphs.push(current.join(' '))
        } else {
          current.push(line)
          paragraphs.push(current.join(' '))
          current = []
          currentLen = 0
          return
        }
        current = []
        currentLen = 0
      }
      current.push(line)
      currentLen += line.length
    }
  })

  // 加入最后一段
  if (current.length > 0) {
    paragraphs.push(current.join(' '))
  }

  return paragraphs.length > 0 ? paragraphs : [text]
}

// 智能按句子分段落
function smartSplitParagraphs(text) {
  // 按句子分割（中英文标点）
  const sentences = text.split(/(?<=[.!?。！？；;])\s+/)

  const paragraphs = []
  let current = []
  let charCount = 0
  const CHARS_PER_PARAGRAPH = 250  // 每段约250字

  sentences.forEach(sentence => {
    const trimmed = sentence.trim()
    if (!trimmed) return

    current.push(trimmed)
    charCount += trimmed.length

    // 每段250字或3句组成一段
    if (charCount >= CHARS_PER_PARAGRAPH || current.length >= 3) {
      paragraphs.push(current.join(' '))
      current = []
      charCount = 0
    }
  })

  // 加入剩余句子
  if (current.length > 0) {
    paragraphs.push(current.join(' '))
  }

  return paragraphs.length > 0 ? paragraphs : [text]
}

// HTML转义，防止XSS
function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

async function load() {
  loading.value = true
  error.value = null
  try {
    article.value = await fetchArticle(route.params.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleBookmark() {
  const result = await toggleBookmark(article.value.id)
  article.value.is_bookmarked = result.status === 'added'
}

async function handleTranslate() {
  if (!article.value) return
  translating.value = true
  try {
    const result = await translateArticle(article.value.id)
    if (result.success && result.translated) {
      article.value.summary_zh = result.translated
      article.value.is_translated = true
      activeSummary.value = 'zh'
    }
  } catch (e) {
    console.error('翻译失败:', e)
  } finally {
    translating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.article-view {
  padding: var(--space-8) 0 var(--space-12);
}

.article-detail {
  max-width: 720px;
  margin: 0 auto;
}

.article-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.article-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-3);
  background: var(--accent-dim);
  color: var(--accent);
  font-size: var(--font-size-xs);
  font-weight: 700;
  border-radius: 999px;
  letter-spacing: 0.03em;
}

.article-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.article-title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.original-title {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-style: italic;
  margin-bottom: var(--space-5);
}

.article-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-bottom: var(--space-6);
}

.article-body {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

/* 摘要段落样式 */
.article-body :deep(p) {
  margin: 0 0 1.5em 0;
  line-height: 1.9;
  color: var(--text-secondary);
}

.article-body :deep(p:last-child) {
  margin-bottom: 0;
}

/* 第一个段落特殊处理 - 引导段落 */
.article-body :deep(p.first),
.article-body :deep(p:first-child) {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.75;
  margin-bottom: 1.8em;
  padding-bottom: 1.5em;
  border-bottom: 1px solid var(--border);
}

/* 列表项样式 */
.article-body :deep(ul),
.article-body :deep(ol) {
  margin: 1em 0;
  padding-left: 1.5em;
}

.article-body :deep(li) {
  margin-bottom: 0.5em;
  line-height: 1.8;
}

/* 引用样式 */
.article-body :deep(blockquote) {
  margin: 1.5em 0;
  padding: 1em 1.5em;
  border-left: 4px solid var(--accent);
  background: var(--bg-elevated);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-style: italic;
}

/* 代码块样式 */
.article-body :deep(pre) {
  margin: 1.5em 0;
  padding: 1em;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.article-body :deep(code) {
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 0.9em;
}

.article-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
  line-height: 1.6;
}

/* 链接样式 */
.article-body :deep(a) {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.article-body :deep(a:hover) {
  border-bottom-color: var(--accent);
}

/* 标题样式 */
.article-body :deep(h2),
.article-body :deep(h3) {
  margin: 1.5em 0 0.8em;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.article-body :deep(h2) {
  font-size: var(--font-size-xl);
}

.article-body :deep(h3) {
  font-size: var(--font-size-lg);
}

/* 分割线 */
.article-body :deep(hr) {
  margin: 2em 0;
  border: none;
  border-top: 1px solid var(--border);
}

/* 图片样式 */
.article-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
  margin: 1em 0;
}

/* 翻译标签样式 */
.tag-translated {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: var(--font-size-xs);
  padding: 2px var(--space-2);
  border-radius: 999px;
}

/* 翻译按钮样式 */
.translate-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  padding: 4px var(--space-3);
  border-radius: 999px;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  transition: all var(--transition-fast);
}

.translate-btn:hover:not(:disabled) {
  background: var(--accent-dim);
  color: var(--accent);
  border-color: var(--accent);
}

.translate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 旋转动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 摘要切换标签 */
.summary-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  padding: var(--space-1);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  width: fit-content;
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  font-weight: 500;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-secondary);
}

.tab-btn.active {
  background: var(--bg-surface);
  color: var(--accent);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 空摘要提示 */
.empty-summary {
  background: var(--bg-surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  color: var(--text-muted);
}

/* 无摘要详情样式 */
.no-summary-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-12);
  background: var(--bg-surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  text-align: center;
}

.no-summary-icon {
  color: var(--warning);
  opacity: 0.8;
}

.no-summary-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.no-summary-desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  max-width: 400px;
}

.article-footer {
  padding-top: var(--space-6);
  border-top: 1px solid var(--border);
}

/* Skeleton */
.skeleton-detail {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-8) 0;
}

.skeleton-line {
  background: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-hover) 50%, var(--bg-elevated) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-12);
  text-align: center;
}
.empty-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}
.empty-desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

@media (max-width: 640px) {
  .article-title {
    font-size: var(--font-size-2xl);
  }
  .article-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
