<template>
  <article class="article-card" @click="goToDetail">
    <div class="card-header">
      <div class="meta">
        <span class="source">{{ article.source_name }}</span>
        <span class="separator">—</span>
        <span class="date">{{ formatDate(article.published_at) }}</span>
      </div>
      <span v-if="article.review_grade" class="grade" :class="'g' + article.review_grade">{{ article.review_grade }}</span>
    </div>

    <h2 class="title">{{ displayTitle }}</h2>

    <p v-if="displaySummary" class="summary">{{ truncateSummary(displaySummary) }}</p>

    <div class="card-footer">
      <div class="tags">
        <span
          v-for="tag in article.tags"
          :key="tag"
          class="tag"
          :class="tagClass(tag)"
        >{{ tag }}</span>
      </div>

      <div class="actions">
        <a
          :href="article.url"
          target="_blank"
          rel="noopener noreferrer"
          class="link"
          @click.stop
        >阅读原文</a>
        <button
          class="bookmark"
          :class="{ on: article.is_bookmarked }"
          @click.stop="handleBookmark"
          :title="article.is_bookmarked ? '取消收藏' : '添加收藏'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" :fill="article.is_bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
      </div>
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

const displaySummary = computed(() => {
  return props.article.summary_zh || props.article.summary
})

const displayTitle = computed(() => {
  return props.article.title_zh || props.article.title
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

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function goToDetail() {
  router.push(`/article/${props.article.id}`)
}

async function handleBookmark() {
  await store.toggle(props.article.id)
}

function truncateSummary(text, maxLength = 120) {
  if (!text) return ''
  const plainText = text.replace(/<[^>]+>/g, '').trim()
  if (plainText.length <= maxLength) return plainText
  return plainText.substring(0, maxLength).trim() + '...'
}
</script>

<style scoped>
.article-card {
  padding: var(--space-8) 0;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.article-card:hover {
  padding-left: var(--space-6);
  padding-right: var(--space-6);
  margin-left: calc(-1 * var(--space-6));
  margin-right: calc(-1 * var(--space-6));
  background: var(--bg-surface);
  border-bottom-color: var(--border);
}

.article-card:hover .title {
  color: var(--accent);
}

.article-card:last-child {
  border-bottom: none;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
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

.separator {
  opacity: 0.4;
}

.grade {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  opacity: 0.7;
}

.grade.gA { background: #1a1a1a; color: #fff; opacity: 1; }
.grade.gB { background: #e5e5e5; color: #666; }
.grade.gC { background: transparent; color: #aaa; border: 1px solid #ddd; }
.grade.gD { background: transparent; color: #ccc; border: 1px solid #eee; }

.title {
  font-family: var(--font-serif);
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.35;
  margin-bottom: var(--space-2);
  letter-spacing: -0.01em;
}

.summary {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-3);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.link {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.link:hover {
  color: var(--accent);
}

.bookmark {
  background: none;
  border: none;
  padding: var(--space-1);
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  transition: color var(--transition-fast);
}

.bookmark:hover {
  color: var(--accent);
}

.bookmark.on {
  color: var(--accent);
}
</style>
