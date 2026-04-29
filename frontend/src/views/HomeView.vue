<template>
  <div class="home-view">
    <div class="container">

      <!-- 极简筛选 -->
      <nav class="filters">
        <button
          v-for="filter in quickFilters"
          :key="filter.value"
          class="filter-link"
          :class="{ active: store.gradeFilter === filter.value }"
          @click="store.setGradeFilter(filter.value)"
        >
          {{ filter.label }}
        </button>
        <button
          v-if="store.activeTag || store.keyword"
          class="filter-clear"
          @click="clearAllFilters"
        >
          清除筛选
        </button>
      </nav>

      <!-- 搜索 -->
      <div class="search-wrap">
        <input
          type="text"
          class="search-input"
          placeholder="搜索..."
          v-model="searchInput"
          @keyup.enter="store.setKeyword(searchInput)"
        />
      </div>

      <!-- 标签 -->
      <div class="tags">
        <button
          v-for="item in filterItems"
          :key="item.value"
          class="tag-btn"
          :class="{ active: store.activeTag === item.value }"
          @click="handleTagClick(item.value)"
        >
          {{ item.label }}<span class="tag-count">{{ item.count }}</span>
        </button>
      </div>

      <!-- 文章列表 -->
      <section class="article-list">
        <div v-if="store.loading" class="loading">
          <span v-for="i in 5" :key="i" class="skeleton"></span>
        </div>

        <div v-else-if="store.error" class="error">
          加载失败
          <button class="btn btn-ghost" @click="store.loadArticles()">重试</button>
        </div>

        <div v-else-if="store.articles.length === 0" class="empty">
          <p>暂无符合条件的资讯</p>
          <button class="btn btn-ghost" @click="clearAllFilters">清除筛选</button>
        </div>

        <template v-else>
          <ArticleCard
            v-for="article in store.articles"
            :key="article.id"
            :article="article"
          />
        </template>
      </section>

      <!-- 分页 -->
      <div v-if="store.pages > 0" class="pagination">
        <span class="total">{{ store.total }}篇</span>
        <button
          class="btn btn-ghost"
          :disabled="store.page <= 1"
          @click="store.setPage(store.page - 1)"
        >
          上一页
        </button>
        <span class="page-num">{{ store.page }} / {{ store.pages }}</span>
        <button
          class="btn btn-ghost"
          :disabled="store.page >= store.pages"
          @click="store.setPage(store.page + 1)"
        >
          下一页
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useArticleStore } from '@/stores/articles'
import { useReviewStore } from '@/stores/review'
import ArticleCard from '@/components/ArticleCard.vue'

const store = useArticleStore()
const reviewStore = useReviewStore()
const searchInput = ref(store.keyword || '')

const quickFilters = [
  { label: '最新', value: '' },
  { label: '重要', value: 'A' },
  { label: '推荐', value: 'B' },
]

const filterItems = computed(() => {
  const tagMap = store.stats?.tag_counts || {}
  return [
    { label: 'AI前沿', value: 'AI前沿', count: tagMap['AI前沿'] || 0 },
    { label: '游戏美术', value: '游戏美术', count: tagMap['游戏美术'] || 0 },
    { label: '游戏策划', value: '游戏策划', count: tagMap['游戏策划'] || 0 },
    { label: '使用技巧', value: '使用技巧', count: tagMap['使用技巧'] || 0 },
    { label: '工具', value: '工具推荐', count: tagMap['工具推荐'] || 0 },
  ]
})

function handleTagClick(tag) {
  store.setTag(store.activeTag === tag ? '' : tag)
}

function clearAllFilters() {
  store.setTag('')
  store.setKeyword('')
  store.setGradeFilter('')
  searchInput.value = ''
}

onMounted(() => {
  store.loadArticles()
  store.loadStats()
})
</script>

<style scoped>
.home-view {
  padding: var(--space-8) 0 var(--space-16);
}

/* 筛选器 */
.filters {
  display: flex;
  gap: var(--space-8);
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 2px solid var(--border);
}

.filter-link {
  background: none;
  border: none;
  padding: var(--space-2) 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  cursor: pointer;
  transition: color var(--transition-fast);
  border-bottom: 2px solid transparent;
  margin-bottom: -6px;
}

.filter-link:hover {
  color: var(--text-primary);
}

.filter-link.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}

.filter-sub {
  font-size: 10px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 4px;
}

.filter-clear {
  margin-left: auto;
  background: none;
  border: 1px solid var(--border);
  padding: var(--space-1) var(--space-3);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-clear:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* 搜索 */
.search-wrap {
  margin-bottom: var(--space-8);
}

.search-input {
  width: 100%;
  padding: var(--space-4) 0;
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--border);
  color: var(--text-primary);
  font-family: var(--font-serif);
  font-size: var(--font-size-xl);
  outline: none;
  transition: border-color var(--transition-fast);
}

.search-input:focus {
  border-color: var(--accent);
}

.search-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

/* 标签 */
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-8);
}

.tag-btn {
  background: transparent;
  border: 1px solid var(--border);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tag-btn:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
  background: var(--bg-surface);
}

.tag-btn.active {
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: var(--bg-base);
}

.tag-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  margin-left: var(--space-2);
  padding: 0 4px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  background: var(--text-muted);
  color: var(--bg-base);
  border-radius: 8px;
}

.tag-btn.active .tag-count {
  background: rgba(255,255,255,0.3);
}

.tag-btn:not(.active) .tag-count {
  background: var(--text-muted);
}

/* 文章列表 */
.article-list {
  display: flex;
  flex-direction: column;
}

.loading {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.skeleton {
  height: 60px;
  background: linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-elevated) 50%, var(--bg-surface) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.error, .empty {
  padding: var(--space-12) 0;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-6);
  margin-top: var(--space-16);
  padding-top: var(--space-8);
  border-top: 2px solid var(--border);
  font-size: var(--font-size-sm);
}

.total {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  margin-right: auto;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.page-num {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  font-weight: 600;
}
</style>
