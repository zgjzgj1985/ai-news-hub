<template>
  <article class="article-card" @click="goToDetail">
    <div class="card-header">
      <div class="card-meta">
        <span class="source-name">{{ article.source_name }}</span>
        <span class="dot"></span>
        <span class="date">{{ formatDate(article.published_at) }}</span>
        <span class="dot"></span>
        <span class="read-time">{{ article.read_time_minutes }} min</span>
      </div>
      <div class="header-right">
        <span
          v-if="article.review_grade"
          class="review-badge"
          :class="gradeClass(article.review_grade)"
          :title="article.review_verdict || '评审中'"
        >
          {{ article.review_grade }}
        </span>
        <span v-if="article.title_zh" class="translated-badge" title="已翻译">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0 0 14.07 6H17V4h-7V2H8v2H1v2h11.17A15.9 15.9 0 0 1 4.17 12l1.47 1.47"/>
            <path d="M21 11.5v2H11V2h2v9"/>
            <path d="M11 22v-2h2v2h-2"/>
          </svg>
        </span>
        <button
          class="bookmark-btn"
          :class="{ bookmarked: article.is_bookmarked }"
          @click.stop="handleBookmark"
          :title="article.is_bookmarked ? '取消收藏' : '收藏'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" :fill="article.is_bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
      </div>
    </div>

    <h2 class="card-title">{{ displayTitle }}</h2>

    <p v-if="displaySummary" class="card-summary">{{ truncateSummary(displaySummary) }}</p>

    <!-- 无摘要提示 -->
    <div v-else class="no-summary-hint">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <span>该来源暂不支持摘要抓取</span>
      <a
        :href="article.url"
        target="_blank"
        rel="noopener noreferrer"
        class="direct-link"
        @click.stop
      >
        直接查看原文
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </a>
    </div>

    <div class="card-footer">
      <div class="tags">
        <span
          v-for="tag in article.tags"
          :key="tag"
          class="tag"
          :class="tagClass(tag)"
          @click.stop="filterByTag(tag)"
        >{{ tag }}</span>
      </div>
      <a
        :href="article.url"
        target="_blank"
        rel="noopener noreferrer"
        class="read-link"
        @click.stop
        title="在原文阅读"
      >
        阅读原文
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </a>
    </div>

    <div v-if="article.review_grade === 'D'" class="review-rejected">
      <span class="rejected-label">评审未通过</span>
      <span v-if="article.review_verdict" class="rejected-reason">{{ article.review_verdict }}</span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useArticleStore } from '@/stores/articles'

const props = defineProps({
  article: { type: Object, required: true },
})

const router = useRouter()
const store = useArticleStore()

// 优先显示翻译后的中文摘要
const displaySummary = computed(() => {
  if (props.article.summary_zh) {
    return props.article.summary_zh
  }
  return props.article.summary
})

// 优先显示翻译后的中文标题
const displayTitle = computed(() => {
  if (props.article.title_zh) {
    return props.article.title_zh
  }
  return props.article.title
})

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

const GRADE_COLORS = {
  'A': { bg: '#10b981', label: '强烈推荐' },
  'B': { bg: '#3b82f6', label: '推荐' },
  'C': { bg: '#f59e0b', label: '待定' },
  'D': { bg: '#6b7280', label: '过滤' },
}

function gradeClass(grade) {
  return `grade-${grade.toLowerCase()}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function goToDetail() {
  router.push(`/article/${props.article.id}`)
}

async function handleBookmark() {
  await store.toggle(props.article.id)
}

function filterByTag(tag) {
  store.setTag(tag)
  router.push('/')
}

// 截断摘要并智能分段落显示
function truncateSummary(text, maxLength = 200) {
  if (!text) return ''
  // 移除HTML标签
  const plainText = text.replace(/<[^>]+>/g, '').trim()
  if (plainText.length <= maxLength) return plainText
  // 智能截断，在句号处截断
  const truncated = plainText.substring(0, maxLength)
  const lastPunctuation = Math.max(
    truncated.lastIndexOf('。'),
    truncated.lastIndexOf('.'),
    truncated.lastIndexOf('!'),
    truncated.lastIndexOf('！')
  )
  if (lastPunctuation > maxLength * 0.6) {
    return truncated.substring(0, lastPunctuation + 1) + '...'
  }
  return truncated + '...'
}
</script>

<style scoped>
.article-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  cursor: pointer;
  transition: border-color var(--transition-base), box-shadow var(--transition-base), transform var(--transition-base);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.article-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent-dim), var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  flex-wrap: wrap;
}

.source-name {
  color: var(--accent);
  font-weight: 600;
}

.dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--text-muted);
  flex-shrink: 0;
}

.bookmark-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.bookmark-btn:hover {
  color: var(--warning);
  background: var(--bg-elevated);
}
.bookmark-btn.bookmarked {
  color: var(--warning);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  transition: color var(--transition-fast);
}
.article-card:hover .card-title {
  color: var(--accent);
}

.card-summary {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-1);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.read-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
  text-decoration: none;
  transition: color var(--transition-fast);
}
.read-link:hover {
  color: var(--accent);
  text-decoration: none;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.review-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: white;
  cursor: default;
}

.translated-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.grade-a {
  background: #10b981;
}

.grade-b {
  background: #3b82f6;
}

.grade-c {
  background: #f59e0b;
}

.grade-d {
  background: #6b7280;
  opacity: 0.6;
}

.no-summary-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.no-summary-hint svg {
  flex-shrink: 0;
  color: var(--warning);
}

.direct-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--accent);
  font-weight: 500;
  text-decoration: none;
  margin-left: auto;
  white-space: nowrap;
}

.direct-link:hover {
  text-decoration: underline;
}

.review-rejected {
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--text-muted);
  opacity: 0.7;
}

.rejected-label {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.rejected-reason {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: 2px;
}
</style>
