<template>
  <div class="home-view">
    <div class="container">

      <!-- Hero / Stats bar -->
      <section class="hero" v-if="store.stats">
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ store.stats.total_articles }}</span>
            <span class="stat-label">篇资讯</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ store.stats.articles_last_24h }}</span>
            <span class="stat-label">今日新增</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ store.stats.total_bookmarks }}</span>
            <span class="stat-label">收藏</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ store.stats.total_sources }}</span>
            <span class="stat-label">订阅源</span>
          </div>
          <!-- LLM状态指示器 -->
          <div class="stat-divider"></div>
          <div class="stat-item llm-status" :class="{ connected: reviewStore.llmStatus?.llm_available }">
            <span class="llm-dot"></span>
            <span class="stat-value llm-value">{{ reviewStore.llmStatus?.llm_available ? 'LLM' : '规则' }}</span>
            <span class="stat-label">评审</span>
          </div>
        </div>

        <!-- 评审委员会统计 -->
        <div v-if="reviewStats" class="review-stats">
          <span class="review-stats-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            评审委员会
          </span>
          <div class="review-grades">
            <span class="grade-pill grade-a" title="强烈推荐">{{ reviewStats.grade_counts.A }} A</span>
            <span class="grade-pill grade-b" title="推荐">{{ reviewStats.grade_counts.B }} B</span>
            <span class="grade-pill grade-c" title="待定">{{ reviewStats.grade_counts.C }} C</span>
            <span class="grade-pill grade-d" title="已过滤">{{ reviewStats.grade_counts.D }} D</span>
          </div>
          <span class="review-pass-rate">通过率 {{ reviewStats.pass_rate }}%</span>
        </div>
      </section>

      <!-- 快速筛选 -->
      <section class="quick-filters">
        <div class="filter-tabs">
          <button
            v-for="filter in quickFilters"
            :key="filter.value"
            class="filter-tab"
            :class="{ active: activeGradeFilter === filter.value }"
            @click="setGradeFilter(filter.value)"
          >
            {{ filter.label }}
          </button>
        </div>
        <!-- 当前筛选状态 -->
        <div v-if="activeGradeFilter || activeTag || searchInput" class="filter-status">
          <span class="filter-status-label">当前筛选：</span>
          <span v-if="activeGradeFilter" class="filter-tag">
            {{ getGradeFilterLabel(activeGradeFilter) }}
            <button class="filter-tag-remove" @click="setGradeFilter('')">×</button>
          </span>
          <span v-if="activeTag" class="filter-tag">
            {{ activeTag }}
            <button class="filter-tag-remove" @click="store.setTag('')">×</button>
          </span>
          <span v-if="searchInput" class="filter-tag">
            关键词: {{ searchInput }}
            <button class="filter-tag-remove" @click="clearSearch">×</button>
          </span>
          <button class="filter-clear" @click="clearSearchAndTags">清除筛选</button>
        </div>
      </section>

      <!-- Controls: Search + Filters -->
      <section class="controls">
        <SearchBar
          v-model="searchInput"
          placeholder="搜索 AI 资讯..."
          show-sort
          :sort="store.sort"
          @update:sort="store.setSort"
          @search="store.setKeyword(searchInput)"
        />

        <TagFilter
          v-model="activeTag"
          :items="filterItems"
          @tag-click="handleTagClick"
        />
      </section>

      <!-- Article List -->
      <section class="article-list">
        <!-- Loading -->
        <div v-if="store.loading" class="article-list-inner">
          <div v-for="i in 6" :key="i" class="skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-tags">
              <div class="skeleton-tag"></div>
              <div class="skeleton-tag"></div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="store.error" class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p class="empty-title">加载失败</p>
          <p class="empty-desc">{{ store.error }}</p>
          <button class="btn btn-ghost" @click="store.loadArticles()">重试</button>
        </div>

        <!-- Empty -->
        <div v-else-if="store.articles.length === 0" class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <p class="empty-title">暂无资讯</p>
          <p class="empty-desc">点击顶部「刷新」按钮获取最新资讯</p>
        </div>

        <!-- Articles -->
        <div v-else class="article-list-inner">
          <ArticleCard
            v-for="article in store.articles"
            :key="article.id"
            :article="article"
          />
        </div>
      </section>

      <!-- Pagination -->
      <section v-if="store.pages > 1" class="pagination">
        <button
          class="btn btn-ghost"
          :disabled="store.page <= 1"
          @click="store.setPage(store.page - 1)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          上一页
        </button>

        <div class="page-info">
          <span class="font-mono">{{ store.page }} / {{ store.pages }}</span>
          <span class="text-muted text-sm">&nbsp;共 {{ store.total }} 篇</span>
        </div>

        <button
          class="btn btn-ghost"
          :disabled="store.page >= store.pages"
          @click="store.setPage(store.page + 1)"
        >
          下一页
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useArticleStore } from '@/stores/articles'
import { useReviewStore } from '@/stores/review'
import ArticleCard from '@/components/ArticleCard.vue'
import SearchBar from '@/components/SearchBar.vue'
import TagFilter from '@/components/TagFilter.vue'

const store = useArticleStore()
const reviewStore = useReviewStore()
const searchInput = ref('')
const activeTag = ref('')
const activeGradeFilter = ref('AB')  // 默认：A+B级

const reviewStats = computed(() => reviewStore.stats)

// 快速筛选选项
const quickFilters = [
  { label: '全部', value: '', desc: '显示所有内容' },
  { label: '只看A级', value: 'A', desc: '只看强烈推荐' },
  { label: 'A+B级', value: 'AB', desc: '只看推荐及以上' },
]

const filterItems = computed(() => {
  const items = [
    { label: '全部', value: '', count: 0 },
    { label: 'AI前沿', value: 'AI前沿', count: store.stats?.tag_counts?.['AI前沿'] || 0 },
    { label: '游戏美术', value: '游戏美术', count: store.stats?.tag_counts?.['游戏美术'] || 0 },
    { label: '游戏策划', value: '游戏策划', count: store.stats?.tag_counts?.['游戏策划'] || 0 },
    { label: '使用技巧', value: '使用技巧', count: store.stats?.tag_counts?.['使用技巧'] || 0 },
    { label: '工具推荐', value: '工具推荐', count: store.stats?.tag_counts?.['工具推荐'] || 0 },
  ]
  return items
})

// 快速筛选功能
function setGradeFilter(filter) {
  activeGradeFilter.value = filter
  store.setGradeFilter(filter)
}

// 选择标签时清除评级筛选，显示所有非D级文章
function handleTagClick(tag) {
  activeTag.value = tag
  activeGradeFilter.value = ''  // 清除评级筛选
  store.setGradeFilter('')      // 设为显示所有评级
  store.setTag(tag)
}

function getGradeFilterLabel(filter) {
  const labels = { 'A': 'A级(强烈推荐)', 'B': 'B级(推荐)', 'AB': 'A+B级' }
  return labels[filter] || filter
}

function clearSearch() {
  searchInput.value = ''
  store.setKeyword('')
}

function clearSearchAndTags() {
  activeTag.value = ''
  searchInput.value = ''
  store.setTag('')
  store.setKeyword('')
}

watch(activeTag, (val) => {
  store.setTag(val)
})

onMounted(() => {
  store.loadArticles()
  store.loadStats()
  reviewStore.loadStats()
  reviewStore.loadLLMStatus()
})
</script>

<style scoped>
.home-view {
  padding: var(--space-6) 0 var(--space-12);
}

.hero {
  margin-bottom: var(--space-4);
}

.stats-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-4) var(--space-6);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border);
  flex-shrink: 0;
}

/* LLM状态指示器 */
.llm-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.llm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all var(--transition-base);
}

.llm-status.connected .llm-dot {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
  animation: pulse 2s infinite;
}

.llm-value {
  font-size: var(--font-size-lg) !important;
  color: var(--text-secondary) !important;
  transition: color var(--transition-fast);
}

.llm-status.connected .llm-value {
  color: var(--success) !important;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.controls {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

/* 快速筛选 */
.quick-filters {
  margin-bottom: var(--space-4);
}

.filter-tabs {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.filter-tab {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-tab:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.filter-tab.active {
  background: var(--accent-dim);
  color: var(--accent);
  font-weight: 600;
}

/* 筛选状态显示 */
.filter-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
}

.filter-status-label {
  color: var(--text-muted);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--accent-dim);
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.filter-tag-remove {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  padding: 0 2px;
  font-size: 14px;
  line-height: 1;
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}

.filter-tag-remove:hover {
  opacity: 1;
}

.filter-clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 8px;
  font-size: var(--font-size-xs);
  transition: color var(--transition-fast);
}

.filter-clear:hover {
  color: var(--error);
}

.article-list-inner {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

/* Skeleton loading */
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
.skeleton-line.short { width: 40%; }
.skeleton-line.medium { width: 70%; }
.skeleton-line.long { width: 90%; height: 20px; }
.skeleton-tags { display: flex; gap: var(--space-2); }
.skeleton-tag {
  width: 60px;
  height: 20px;
  background: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-hover) 50%, var(--bg-elevated) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
  max-width: 300px;
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-8);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border);
}

.page-info {
  display: flex;
  align-items: center;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

@media (max-width: 640px) {
  .stats-row {
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
  }
  .stat-value {
    font-size: var(--font-size-xl);
  }
  .stat-divider {
    height: 24px;
  }
  .stat-label {
    display: none;
  }
  .stats-row .stat-item:first-child .stat-label,
  .stats-row .stat-item:nth-child(5) .stat-label {
    display: inline;
  }
  .llm-status {
    display: none;
  }
  .filter-tabs {
    flex-direction: column;
  }
  .filter-tab {
    text-align: center;
  }
}

.review-stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
}

.review-stats-title {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--text-muted);
  font-weight: 600;
}

.review-grades {
  display: flex;
  gap: var(--space-2);
}

.grade-pill {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
  color: white;
  font-size: var(--font-size-xs);
}

.grade-pill.grade-a { background: #10b981; }
.grade-pill.grade-b { background: #3b82f6; }
.grade-pill.grade-c { background: #f59e0b; }
.grade-pill.grade-d { background: #6b7280; }

.review-pass-rate {
  color: var(--text-muted);
  margin-left: auto;
}
</style>
