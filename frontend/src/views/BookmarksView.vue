<template>
  <div class="bookmarks-view">
    <div class="container">
      <header class="header">
        <h1 class="title">收藏</h1>
        <span class="count">{{ bookmarks.length }}篇</span>
      </header>

      <div v-if="loading" class="loading">
        <span v-for="i in 3" :key="i" class="skeleton"></span>
      </div>

      <div v-else-if="bookmarks.length === 0" class="empty">
        还没有收藏
      </div>

      <template v-else>
        <div v-for="item in bookmarks" :key="item.id" class="item">
          <ArticleCard
            v-if="item.article"
            :article="item.article"
          />
          <button class="remove" @click="removeBookmark(item.article_id)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </template>
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
  padding: var(--space-8) 0 var(--space-16);
}

.header {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  letter-spacing: -0.02em;
}

.count {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.loading {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.skeleton {
  height: 80px;
  background: var(--bg-surface);
}

.empty {
  padding: var(--space-16) 0;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.item {
  position: relative;
}

.remove {
  position: absolute;
  top: var(--space-4);
  right: 0;
  background: var(--bg-surface);
  border: none;
  padding: var(--space-2);
  cursor: pointer;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.item:hover .remove {
  opacity: 1;
}

.remove:hover {
  color: var(--error);
}
</style>
