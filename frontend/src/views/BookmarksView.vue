<template>
  <div class="bookmarks-view">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">我的收藏</h1>
        <span class="count-badge">{{ bookmarks.length }}</span>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="article-list-inner">
        <div v-for="i in 4" :key="i" class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line long"></div>
          <div class="skeleton-line medium"></div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="bookmarks.length === 0" class="empty-state">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.2">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
        <p class="empty-title">还没有收藏</p>
        <p class="empty-desc">在资讯列表中点击书签图标即可收藏感兴趣的文章</p>
        <router-link to="/" class="btn btn-primary">浏览资讯</router-link>
      </div>

      <!-- Bookmarks -->
      <div v-else class="article-list-inner">
        <div v-for="item in bookmarks" :key="item.id" class="bookmark-item">
          <ArticleCard
            v-if="item.article"
            :article="item.article"
          />
          <button
            class="remove-btn"
            @click="removeBookmark(item.article_id)"
            title="取消收藏"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchBookmarks, deleteBookmark } from '@/api'
import ArticleCard from '@/components/ArticleCard.vue'

const bookmarks = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    bookmarks.value = await fetchBookmarks()
  } catch (e) {
    console.warn(e)
  } finally {
    loading.value = false
  }
}

async function removeBookmark(articleId) {
  try {
    await deleteBookmark(articleId)
    bookmarks.value = bookmarks.value.filter(b => b.article_id !== articleId)
  } catch (e) {
    console.warn(e)
  }
}

onMounted(load)
</script>

<style scoped>
.bookmarks-view {
  padding: var(--space-8) 0 var(--space-12);
}

.page-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--text-primary);
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 var(--space-2);
  background: var(--accent-dim);
  color: var(--accent);
  font-size: var(--font-size-sm);
  font-weight: 700;
  border-radius: 999px;
}

.article-list-inner {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

.bookmark-item {
  position: relative;
}

.remove-btn {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  transition: all var(--transition-fast);
  z-index: 2;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.bookmark-item:hover .remove-btn {
  opacity: 1;
}
.remove-btn:hover {
  background: rgba(248, 81, 73, 0.15);
  border-color: var(--error);
  color: var(--error);
}

/* Skeleton */
.skeleton-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-hover) 50%, var(--bg-elevated) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}
.skeleton-line.short { width: 30%; }
.skeleton-line.medium { width: 65%; }
.skeleton-line.long { width: 85%; height: 18px; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-12) var(--space-4);
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
  max-width: 320px;
}
</style>
