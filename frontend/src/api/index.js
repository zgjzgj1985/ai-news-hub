import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 120秒超时，兼容LLM评审
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '网络错误'
    return Promise.reject(new Error(msg))
  }
)

// ---- Articles ----
export const fetchArticles = (params) => api.get('/articles', { params })
export const fetchArticle = (id) => api.get(`/articles/${id}`)
export const toggleBookmark = (id) => api.post(`/articles/${id}/bookmark`)
export const getBookmarkStatus = (id) => api.get(`/articles/${id}/bookmark`)

// ---- Bookmarks ----
export const fetchBookmarks = () => api.get('/bookmarks')
export const deleteBookmark = (articleId) => api.delete(`/bookmarks/${articleId}`)

// ---- Sources ----
export const fetchSources = () => api.get('/sources')
export const createSource = (data) => api.post('/sources', data)
export const updateSource = (id, data) => api.patch(`/sources/${id}`, data)
export const deleteSource = (id) => api.delete(`/sources/${id}`)

// ---- Stats ----
export const fetchStats = (params) => api.get('/stats', { params })

// ---- Review ----
export const fetchReviewStats = () => api.get('/stats/review')
export const fetchBatchStatus = () => api.get('/review/batch-status')
export const reviewArticle = (articleId) => api.post(`/review/article/${articleId}`)
export const batchReview = (gradeFilter) => api.post('/review/batch', {}, { params: { grade_filter: gradeFilter } })
export const reReviewArticle = (articleId) => api.post(`/review/article/${articleId}/re-review`)

// ---- LLM Review ----
export const fetchLLMStatus = () => api.get('/review/llm-status')
export const llmReviewArticle = (articleId) => api.post(`/review/article/${articleId}/llm-review`)
export const llmBatchReview = (limit) => api.post('/review/llm-batch', {}, { params: { limit } })

// ---- Translation ----
export const translateArticle = (articleId) => api.post(`/translate/article/${articleId}`)
export const translateAll = (limit) => api.post('/translate/all', {}, { params: { limit } })
export const fetchTranslateStats = () => api.get('/translate/stats')
export const regenerateTranslation = (articleId) => api.post(`/translate/article/${articleId}/regenerate`)

// ---- Admin ----
export const triggerRefresh = () => api.post('/admin/refresh')

export default api
