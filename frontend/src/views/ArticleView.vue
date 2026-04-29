<template>
  <div class="article-view">
    <div class="container">

      <div v-if="loading" class="loading">
        <div class="skeleton-title"></div>
        <div class="skeleton-meta"></div>
        <div class="skeleton-body"></div>
      </div>

      <div v-else-if="error" class="error">
        加载失败
        <button class="btn btn-ghost" @click="load">重试</button>
      </div>

      <article v-else-if="article" class="article">
        <header class="header">
          <div class="meta">
            <span class="source">{{ article.source_name }}</span>
            <span class="sep">·</span>
            <span class="date">{{ formatDate(article.published_at) }}</span>
          </div>
          <div class="actions">
            <button
              class="action-btn"
              :class="{ on: article.is_bookmarked }"
              @click="handleBookmark"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" :fill="article.is_bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.5">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
              </svg>
            </button>
            <a :href="article.url" target="_blank" class="action-btn" title="原文">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
          </div>
        </header>

        <h1 class="title">{{ displayTitle }}</h1>

        <div class="tags">
          <span
            v-for="tag in article.tags"
            :key="tag"
            class="tag"
            :class="tagClass(tag)"
          >{{ tag }}</span>
        </div>

        <div v-if="displaySummaryText" class="body">
          <div v-if="article.summary && article.summary_zh" class="lang-toggle">
            <button
              class="lang-btn"
              :class="{ active: activeSummary === 'zh' }"
              @click="activeSummary = 'zh'"
            >中文</button>
            <button
              class="lang-btn"
              :class="{ active: activeSummary === 'en' }"
              @click="activeSummary = 'en'"
            >英文</button>
          </div>
          <div v-html="formatSummary(displaySummaryText)"></div>
        </div>

        <div v-else class="no-summary">
          该来源暂不支持摘要抓取
          <a :href="article.url" target="_blank" class="btn btn-ghost">查看原文</a>
        </div>

        <footer class="footer">
          <router-link to="/" class="back">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            返回
          </router-link>
        </footer>
      </article>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchArticle, toggleBookmark } from '@/api'

const route = useRoute()
const article = ref(null)
const loading = ref(true)
const error = ref(null)
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

const displayTitle = computed(() => {
  if (!article.value) return ''
  return article.value.title_zh || article.value.title
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

function formatSummary(text) {
  if (!text) return ''
  text = text.replace(/^Back to Articles\s*/i, '').trim()
  if (text.includes('<p') || text.includes('<br') || text.includes('<div')) {
    text = text.replace(/<p[^>]*>/gi, '<p>').replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '</p>\n').replace(/<[^>]+>/g, '').trim()
  }
  text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\t/g, ' ').replace(/\u00a0/g, ' ').replace(/[ ]{2,}/g, ' ')
  const paragraphs = text.split(/\n{2,}/).filter(p => p.trim())
  if (paragraphs.length < 2) {
    const sentences = text.split(/(?<=[.!?。！？；;])\s+/)
    const grouped = []
    let current = []
    let count = 0
    sentences.forEach(s => {
      const t = s.trim()
      if (!t) return
      current.push(t)
      count += t.length
      if (count >= 200 || current.length >= 3) {
        grouped.push(current.join(' '))
        current = []
        count = 0
      }
    })
    if (current.length) grouped.push(current.join(' '))
    paragraphs.length = 0
    paragraphs.push(...grouped)
  }
  if (paragraphs.length < 2) {
    const forced = []
    for (let i = 0; i < text.length; i += 180) {
      forced.push(text.slice(i, i + 180))
    }
    if (forced.length > 1) {
      return forced.map(p => `<p>${renderFormatted(p)}</p>`).join('')
    }
  }
  return paragraphs.map(p => `<p>${renderFormatted(p)}</p>`).join('')
}

function renderFormatted(text) {
  // 常见 Markdown 格式转换为 HTML
  let t = text
    // 代码：``内联代码`` > `代码`（后者优先匹配）
    .replace(/``([^`]+)``/g, '<code>$1</code>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 粗体：**text** 或 __text__
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    // 斜体：*text* 或 _text_（排除 URL 中的下划线）
    .replace(/(?<!\/)\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/(?<!\/)\b_([^_\n]+)_(?!\/)/g, '<em>$1</em>')
    // 删除线：~~text~~
    .replace(/~~([^~]+)~~/g, '<del>$1</del>')
  // 最后转义剩余的危险 HTML 标签和属性
  t = t
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // 还原之前转换的 Markdown HTML 标签中的转义字符
    .replace(/&lt;code&gt;/g, '<code>')
    .replace(/&lt;\/code&gt;/g, '</code>')
    .replace(/&lt;strong&gt;/g, '<strong>')
    .replace(/&lt;\/strong&gt;/g, '</strong>')
    .replace(/&lt;em&gt;/g, '<em>')
    .replace(/&lt;\/em&gt;/g, '</em>')
    .replace(/&lt;del&gt;/g, '<del>')
    .replace(/&lt;\/del&gt;/g, '</del>')
  return t
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

onMounted(load)
</script>

<style scoped>
.article-view {
  padding: var(--space-10) 0 var(--space-16);
}

.article {
  max-width: 680px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.source {
  font-weight: 600;
  color: var(--text-secondary);
}

.sep {
  opacity: 0.4;
}

.actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
}

.action-btn:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.action-btn.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.title {
  font-family: var(--font-serif);
  font-size: var(--font-size-2xl);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-4);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.body {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--text-secondary);
}

.lang-toggle {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.lang-btn {
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: 1px solid var(--border);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.lang-btn:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.lang-btn.active {
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: var(--bg-base);
}

.body :deep(p) {
  margin: 0 0 1.8em;
  line-height: 2;
  text-align: justify;
}

.body :deep(p:first-child) {
  font-family: var(--font-serif);
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  line-height: 1.85;
  margin-bottom: 2em;
}

.body :deep(p:nth-child(n+2)) {
  color: var(--text-secondary);
}

.body :deep(strong),
.body :deep(b) {
  font-weight: 700;
  color: var(--text-primary);
}

.body :deep(em),
.body :deep(i) {
  font-style: italic;
}

.body :deep(code) {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.875em;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.1em 0.4em;
  border-radius: 3px;
  color: var(--text-primary);
}

.body :deep(del) {
  text-decoration: line-through;
  opacity: 0.6;
}

.no-summary {
  padding: var(--space-12) 0;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.footer {
  margin-top: var(--space-12);
  padding-top: var(--space-6);
  border-top: 2px solid var(--border);
}

.back {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

.back:hover {
  color: var(--text-primary);
}

/* Loading */
.loading {
  padding: var(--space-8) 0;
}

.skeleton-title {
  height: 40px;
  width: 85%;
  background: var(--bg-surface);
  margin-bottom: var(--space-4);
}

.skeleton-meta {
  height: 16px;
  width: 35%;
  background: var(--bg-surface);
  margin-bottom: var(--space-6);
}

.skeleton-body {
  height: 300px;
  background: var(--bg-surface);
}

.error {
  padding: var(--space-12) 0;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

@media (max-width: 640px) {
  .title {
    font-size: var(--font-size-xl);
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }
}
</style>
