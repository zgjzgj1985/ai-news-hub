import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchReviewStats, fetchBatchStatus, reviewArticle, batchReview, fetchLLMStatus, llmBatchReview } from '@/api'

export const useReviewStore = defineStore('review', () => {
  const stats = ref(null)
  const llmStatus = ref(null)
  const batchStatus = ref(null)
  const loading = ref(false)
  const llmLoading = ref(false)
  const error = ref(null)

  let batchStatusInterval = null

  async function loadStats() {
    loading.value = true
    error.value = null
    try {
      stats.value = await fetchReviewStats()
    } catch (e) {
      error.value = e.message
      console.warn('Failed to load review stats:', e.message)
    } finally {
      loading.value = false
    }
  }

  async function loadLLMStatus() {
    try {
      llmStatus.value = await fetchLLMStatus()
      return llmStatus.value
    } catch (e) {
      console.warn('Failed to load LLM status:', e.message)
      llmStatus.value = { llm_available: false, status: 'error' }
      return llmStatus.value
    }
  }

  async function loadBatchStatus() {
    try {
      batchStatus.value = await fetchBatchStatus()
      return batchStatus.value
    } catch (e) {
      console.warn('Failed to load batch status:', e.message)
      return null
    }
  }

  // 开始轮询批量状态
  function startBatchStatusPolling() {
    if (batchStatusInterval) return
    batchStatusInterval = setInterval(async () => {
      const status = await loadBatchStatus()
      if (status && !status.running) {
        stopBatchStatusPolling()
        await loadStats()  // 完成后刷新统计数据
      }
    }, 2000)
  }

  function stopBatchStatusPolling() {
    if (batchStatusInterval) {
      clearInterval(batchStatusInterval)
      batchStatusInterval = null
    }
  }

  async function reviewArticleById(articleId) {
    try {
      const result = await reviewArticle(articleId)
      if (stats.value) {
        await loadStats()
      }
      return result
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function runBatchReview() {
    try {
      const result = await batchReview()
      // 如果任务启动成功，开始轮询状态
      if (result.status === 'started' || result.status === 'running') {
        await loadBatchStatus()
        startBatchStatusPolling()
      }
      return result
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function runLLMBatchReview(limit = 10) {
    llmLoading.value = true
    try {
      const result = await llmBatchReview(limit)
      await loadStats()
      return result
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      llmLoading.value = false
    }
  }

  return {
    stats,
    llmStatus,
    batchStatus,
    loading,
    llmLoading,
    error,
    loadStats,
    loadLLMStatus,
    loadBatchStatus,
    startBatchStatusPolling,
    stopBatchStatusPolling,
    reviewArticleById,
    runBatchReview,
    runLLMBatchReview,
  }
})
