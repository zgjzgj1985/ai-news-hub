import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchArticles, fetchStats, toggleBookmark } from '@/api'

export const useArticleStore = defineStore('articles', () => {
  const articles = ref([])
  const total = ref(0)
  const page = ref(1)
  const limit = ref(20)
  const pages = ref(1)
  const loading = ref(false)
  const error = ref(null)

  const activeTag = ref('')
  const keyword = ref('')
  const sort = ref('newest')
  const gradeFilter = ref('AB')  // 默认只显示 A+B 级通过评审的内容

  const stats = ref(null)

  async function loadArticles() {
    loading.value = true
    error.value = null
    try {
      const params = { page: page.value, limit: limit.value, sort: sort.value }
      if (activeTag.value) params.tag = activeTag.value
      if (keyword.value) params.keyword = keyword.value
      if (gradeFilter.value) params.grade = gradeFilter.value

      const data = await fetchArticles(params)
      articles.value = data.items
      total.value = data.total
      pages.value = data.pages
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    try {
      stats.value = await fetchStats()
    } catch (e) {
      console.warn('Failed to load stats:', e.message)
    }
  }

  async function toggle(articleId) {
    const result = await toggleBookmark(articleId)
    const article = articles.value.find((a) => a.id === articleId)
    if (article) {
      article.is_bookmarked = result.status === 'added'
    }
    if (stats.value) {
      stats.value.total_bookmarks += result.status === 'added' ? 1 : -1
    }
    return result
  }

  function setTag(tag) {
    activeTag.value = tag
    page.value = 1
    loadArticles()
  }

  function setKeyword(kw) {
    keyword.value = kw
    page.value = 1
    loadArticles()
  }

  function setSort(s) {
    sort.value = s
    page.value = 1
    loadArticles()
  }

  function setGradeFilter(grade) {
    gradeFilter.value = grade
    page.value = 1
    loadArticles()
  }

  function setPage(p) {
    page.value = p
    loadArticles()
  }

  return {
    articles, total, page, limit, pages, loading, error,
    activeTag, keyword, sort, gradeFilter, stats,
    loadArticles, loadStats, toggle, setTag, setKeyword, setSort, setGradeFilter, setPage,
  }
})
