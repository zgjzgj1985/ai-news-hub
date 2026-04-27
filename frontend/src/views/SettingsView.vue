<template>
  <div class="settings-view">
    <div class="container">

      <!-- Tabs -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Feed Sources Tab -->
      <div v-if="activeTab === 'sources'" class="tab-content">
        <div class="section-header">
          <div>
            <h2 class="section-title">订阅源管理</h2>
            <p class="section-desc">管理 RSS 订阅源，开启/禁用特定来源</p>
          </div>
          <button class="btn btn-primary" @click="showAddModal = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            添加订阅源
          </button>
        </div>

        <!-- Source list -->
        <div class="source-list">
          <div
            v-for="source in sources"
            :key="source.id"
            class="source-item"
          >
            <div class="source-info">
              <div class="source-name">{{ source.name }}</div>
              <div class="source-url">{{ source.url }}</div>
              <div class="source-meta">
                <span class="category-badge">{{ source.category }}</span>
                <span v-if="source.last_fetched" class="text-muted text-xs">
                  上次抓取: {{ formatDate(source.last_fetched) }}
                </span>
              </div>
            </div>
            <div class="source-actions">
              <label class="toggle">
                <input
                  type="checkbox"
                  :checked="source.enabled"
                  @change="toggleSource(source.id, $event.target.checked)"
                />
                <span class="toggle-slider"></span>
              </label>
              <button class="btn btn-icon btn-ghost" @click="deleteSource(source.id)" title="删除">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                </svg>
              </button>
            </div>
          </div>

          <div v-if="sources.length === 0 && !sourcesLoading" class="empty-state">
            <p class="empty-desc">暂无订阅源</p>
          </div>
        </div>
      </div>

      <!-- LLM Review Tab -->
      <div v-if="activeTab === 'llm'" class="tab-content">
        <div class="section-header">
          <div>
            <h2 class="section-title">LLM 智能评审</h2>
            <p class="section-desc">基于本地 Qwen3.5 9B 模型进行深度语义评审</p>
          </div>
          <button class="btn btn-icon btn-ghost" @click="loadLLMStatus" title="刷新状态">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 :class="{ 'spin': llmLoading }">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
          </button>
        </div>

        <!-- LLM Status Card -->
        <div class="llm-status-card" :class="{ 'connected': llmStatus?.llm_available, 'disconnected': !llmStatus?.llm_available }">
          <div class="status-indicator">
            <span class="status-dot"></span>
            <span class="status-text">{{ llmStatus?.llm_available ? '已连接' : '未连接' }}</span>
          </div>

          <div class="status-details">
            <div class="status-row">
              <span class="status-label">LLM 启用</span>
              <span class="status-value">{{ llmStatus?.llm_enabled ? '是' : '否' }}</span>
            </div>
            <div class="status-row">
              <span class="status-label">模型</span>
              <span class="status-value mono">{{ llmStatus?.model || '-' }}</span>
            </div>
            <div class="status-row">
              <span class="status-label">服务地址</span>
              <span class="status-value mono">{{ llmStatus?.base_url || '-' }}</span>
            </div>
            <div class="status-row">
              <span class="status-label">已安装模型</span>
              <span class="status-value">
                <span v-if="llmStatus?.installed_models?.length">
                  <span v-for="m in llmStatus.installed_models" :key="m" class="model-badge">{{ m }}</span>
                </span>
                <span v-else>-</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Not connected warning -->
        <div v-if="!llmStatus?.llm_available" class="warning-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div>
            <p class="warning-title">Ollama 服务未运行</p>
            <p class="warning-desc">请确保已安装并启动 Ollama，且已下载 qwen3.5:9b 模型</p>
            <code class="warning-cmd">ollama pull qwen3.5:9b && ollama serve</code>
          </div>
        </div>

        <!-- Review Stats -->
        <div v-if="reviewStats" class="review-stats">
          <h3 class="stats-title">评审统计</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ reviewStats.total_reviewed }}</div>
              <div class="stat-label">已评审</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ reviewStats.total_pending }}</div>
              <div class="stat-label">待评审</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ reviewStats.pass_rate }}%</div>
              <div class="stat-label">通过率</div>
            </div>
          </div>
          <div class="grade-distribution">
            <div v-for="(item, grade) in reviewStats.grade_distribution" :key="grade"
                 class="grade-bar">
              <span class="grade-label" :style="{ color: item.color }">{{ grade }}</span>
              <div class="grade-progress">
                <div class="grade-fill" :style="{ width: reviewStats.total_reviewed ? (item.count / reviewStats.total_reviewed * 100) + '%' : '0%', background: item.color }"></div>
              </div>
              <span class="grade-count">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <!-- 批量评审进度 -->
        <div v-if="batchStatus?.running" class="batch-progress">
          <h3 class="stats-title">
            <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            批量评审进度
          </h3>
          <div class="progress-info">
            <span class="progress-text">
              已处理 {{ batchStatus.processed }} / {{ batchStatus.total }} 篇
            </span>
            <span class="progress-percent">{{ batchStatus.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: batchStatus.progress + '%' }"></div>
          </div>
          <div class="progress-stats">
            <span class="stat-success">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              成功 {{ batchStatus.success }}
            </span>
            <span v-if="batchStatus.failed > 0" class="stat-failed">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
              失败 {{ batchStatus.failed }}
            </span>
            <span class="stat-time">
              已运行 {{ batchStatus.elapsed_seconds }}s
            </span>
          </div>
        </div>

        <!-- LLM Batch Review -->
        <div class="llm-actions">
          <h3 class="stats-title">批量 LLM 评审</h3>
          <div class="action-row">
            <div class="batch-input">
              <label>评审数量</label>
              <input type="number" v-model="batchLimit" min="1" max="50" class="input" />
            </div>
            <button
              class="btn btn-primary"
              @click="runLLMBatch"
              :disabled="!llmStatus?.llm_available || llmRunning"
            >
              <svg v-if="llmRunning" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              {{ llmRunning ? '评审中...' : '开始批量评审' }}
            </button>
          </div>
          <p class="action-hint">使用 LLM 对未评审的文章进行智能评审（需要 Ollama 服务运行）</p>
        </div>

        <!-- Batch Results -->
        <div v-if="batchResults" class="batch-results">
          <h3 class="stats-title">评审结果</h3>
          <div class="results-summary">
            <span class="result-badge success">成功 {{ batchResults.reviewed_count }}</span>
            <span class="result-badge error">失败 {{ batchResults.failed_count }}</span>
          </div>
          <div class="results-list">
            <div v-for="r in batchResults.results.slice(0, 10)" :key="r.article_id" class="result-item">
              <span class="result-grade" :class="'grade-' + (r.grade || 'unknown')">{{ r.grade || '?' }}</span>
              <span class="result-title">{{ r.title || '未知' }}</span>
              <span v-if="r.error" class="result-error">{{ r.error }}</span>
              <span v-else class="result-score">{{ r.score?.toFixed(1) || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- About Tab -->
      <div v-if="activeTab === 'about'" class="tab-content">
        <div class="about-card">
          <div class="about-logo">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="var(--accent)" stroke-width="1.5"/>
              <circle cx="12" cy="12" r="4" fill="var(--accent)"/>
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h2 class="about-title">AI情报站</h2>
          <p class="about-version text-muted">v0.1.0</p>
          <p class="about-desc">
            聚焦 AI 前沿动态、游戏制作工作流（美术/策划）、使用技巧的资讯聚合工具。
            基于 RSS 自动抓取，支持智能分类、搜索和收藏。
          </p>
          <div class="about-tech">
            <span class="tech-badge">Python</span>
            <span class="tech-badge">FastAPI</span>
            <span class="tech-badge">Vue 3</span>
            <span class="tech-badge">SQLite</span>
            <span class="tech-badge">RSS</span>
          </div>
        </div>
      </div>

    </div>

    <!-- Add Source Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加订阅源</h3>
          <button class="btn btn-icon btn-ghost" @click="showAddModal = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称</label>
            <input v-model="newSource.name" class="input" placeholder="例如: Hugging Face Blog" />
          </div>
          <div class="form-group">
            <label>RSS URL</label>
            <input v-model="newSource.url" class="input" placeholder="https://example.com/feed.xml" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="newSource.category" class="input">
              <option value="general">通用</option>
              <option value="news">新闻</option>
              <option value="blog">博客</option>
              <option value="community">社区</option>
              <option value="research">学术研究</option>
            </select>
          </div>
          <div v-if="addError" class="form-error">{{ addError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addSource" :disabled="addLoading">
            {{ addLoading ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { fetchSources, createSource, updateSource, deleteSource as apiDeleteSource, fetchLLMStatus, llmBatchReview, fetchReviewStats, fetchBatchStatus } from '@/api'

const tabs = [
  { id: 'sources', label: '订阅源' },
  { id: 'llm', label: 'LLM评审' },
  { id: 'about', label: '关于' },
]
const activeTab = ref('sources')
const sources = ref([])
const sourcesLoading = ref(true)
const showAddModal = ref(false)
const addLoading = ref(false)
const addError = ref('')
const newSource = ref({ name: '', url: '', category: 'general' })

// LLM状态
const llmStatus = ref(null)
const llmLoading = ref(false)
const reviewStats = ref(null)
const batchLimit = ref(10)
const llmRunning = ref(false)
const batchResults = ref(null)
const batchStatus = ref(null)

// 批量状态轮询
let batchStatusInterval = null

async function loadSources() {
  sourcesLoading.value = true
  try {
    sources.value = await fetchSources()
  } catch (e) {
    console.warn(e)
  } finally {
    sourcesLoading.value = false
  }
}

async function loadLLMStatus() {
  llmLoading.value = true
  try {
    llmStatus.value = await fetchLLMStatus()
  } catch (e) {
    llmStatus.value = { llm_available: false, status: 'error', llm_enabled: false }
  } finally {
    llmLoading.value = false
  }
}

async function loadReviewStats() {
  try {
    reviewStats.value = await fetchReviewStats()
  } catch (e) {
    console.warn(e)
  }
}

async function loadBatchStatus() {
  try {
    batchStatus.value = await fetchBatchStatus()
    return batchStatus.value
  } catch (e) {
    console.warn(e)
    return null
  }
}

function startBatchStatusPolling() {
  if (batchStatusInterval) return
  batchStatusInterval = setInterval(async () => {
    const status = await loadBatchStatus()
    if (status && !status.running) {
      stopBatchStatusPolling()
      await loadReviewStats()
    }
  }, 2000)
}

function stopBatchStatusPolling() {
  if (batchStatusInterval) {
    clearInterval(batchStatusInterval)
    batchStatusInterval = null
  }
}

async function runLLMBatch() {
  llmRunning.value = true
  batchResults.value = null
  try {
    batchResults.value = await llmBatchReview(batchLimit.value)
    await loadReviewStats()
  } catch (e) {
    alert('批量评审失败: ' + e.message)
  } finally {
    llmRunning.value = false
  }
}

// 监听tab切换
watch(activeTab, async (newTab) => {
  if (newTab === 'llm') {
    await loadBatchStatus()
    if (batchStatus.value?.running) {
      startBatchStatusPolling()
    }
  } else {
    stopBatchStatusPolling()
  }
})

async function toggleSource(id, enabled) {
  try {
    await updateSource(id, { enabled })
    const s = sources.value.find(s => s.id === id)
    if (s) s.enabled = enabled
  } catch (e) {
    console.warn(e)
  }
}

async function deleteSource(id) {
  if (!confirm('确定要删除此订阅源吗？')) return
  try {
    await apiDeleteSource(id)
    sources.value = sources.value.filter(s => s.id !== id)
  } catch (e) {
    console.warn(e)
  }
}

async function addSource() {
  if (!newSource.value.name || !newSource.value.url) {
    addError.value = '请填写名称和 URL'
    return
  }
  addLoading.value = true
  addError.value = ''
  try {
    const source = await createSource(newSource.value)
    sources.value.push(source)
    showAddModal.value = false
    newSource.value = { name: '', url: '', category: 'general' }
  } catch (e) {
    addError.value = e.message
  } finally {
    addLoading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadSources()
  loadLLMStatus()
  loadReviewStats()
})

onUnmounted(() => {
  stopBatchStatusPolling()
})
</script>

<style scoped>
.settings-view {
  padding: var(--space-8) 0 var(--space-12);
}

.tab-bar {
  display: flex;
  gap: var(--space-1);
  margin-bottom: var(--space-8);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}

.tab-btn {
  padding: var(--space-3) var(--space-5);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: -1px;
}
.tab-btn:hover {
  color: var(--text-primary);
}
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab-content {
  animation: fadeIn var(--transition-base);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.section-desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.source-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-fast);
}
.source-item:hover {
  border-color: var(--text-muted);
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.source-url {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: var(--space-2);
}

.source-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.category-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  background: var(--bg-elevated);
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.source-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

/* Toggle switch */
.toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.toggle-slider {
  width: 40px;
  height: 22px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 11px;
  transition: all var(--transition-base);
  position: relative;
}
.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: var(--text-muted);
  border-radius: 50%;
  transition: all var(--transition-base);
}
.toggle input:checked + .toggle-slider {
  background: var(--accent-dim);
  border-color: var(--accent);
}
.toggle input:checked + .toggle-slider::after {
  left: 20px;
  background: var(--accent);
}

/* About */
.about-card {
  max-width: 480px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  text-align: center;
}
.about-logo {
  margin-bottom: var(--space-4);
}
.about-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  margin-bottom: var(--space-1);
}
.about-version {
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  margin-bottom: var(--space-5);
}
.about-desc {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: var(--space-6);
}
.about-tech {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.tech-badge {
  padding: var(--space-1) var(--space-3);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: var(--space-4);
}

.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border);
}
.modal-header h3 {
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.modal-body {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.form-group label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-secondary);
}

.form-error {
  font-size: var(--font-size-sm);
  color: var(--error);
  background: rgba(248, 81, 73, 0.1);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
}

.empty-state {
  text-align: center;
  padding: var(--space-8);
}
.empty-desc {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 640px) {
  .section-header {
    flex-direction: column;
  }
  .source-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .source-actions {
    width: 100%;
    justify-content: space-between;
  }
}

/* LLM Review Tab Styles */
.llm-status-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
}
.llm-status-card.connected {
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--bg-surface) 0%, rgba(59, 130, 246, 0.05) 100%);
}
.llm-status-card.disconnected {
  border-color: var(--border);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--error);
}
.llm-status-card.connected .status-dot {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}
.status-text {
  font-weight: 600;
  color: var(--text-primary);
}

.status-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
}
.status-label {
  color: var(--text-muted);
}
.status-value {
  color: var(--text-primary);
  font-weight: 500;
}
.status-value.mono {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
}
.model-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  margin-right: 4px;
}

.warning-box {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
}
.warning-box svg {
  flex-shrink: 0;
  color: var(--warning);
}
.warning-title {
  font-weight: 600;
  margin-bottom: var(--space-1);
}
.warning-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}
.warning-cmd {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  color: var(--accent);
}

.review-stats {
  margin-bottom: var(--space-6);
}
.stats-title {
  font-size: var(--font-size-base);
  font-weight: 700;
  margin-bottom: var(--space-4);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.stat-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  text-align: center;
}
.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--accent);
}
.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: var(--space-1);
}
.grade-distribution {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.grade-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.grade-label {
  font-weight: 700;
  width: 20px;
}
.grade-progress {
  flex: 1;
  height: 6px;
  background: var(--bg-elevated);
  border-radius: 3px;
  overflow: hidden;
}
.grade-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
.grade-count {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  min-width: 30px;
  text-align: right;
}

.llm-actions {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
}
.action-row {
  display: flex;
  gap: var(--space-4);
  align-items: flex-end;
}
.batch-input {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.batch-input label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.batch-input input {
  width: 80px;
}
.action-hint {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: var(--space-3);
}

.batch-results {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}
.results-summary {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.result-badge {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: 600;
}
.result-badge.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}
.result-badge.error {
  background: rgba(248, 81, 73, 0.1);
  color: var(--error);
}
.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.result-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}
.result-grade {
  font-weight: 700;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  color: white;
}
.result-grade.grade-A { background: #10b981; }
.result-grade.grade-B { background: #3b82f6; }
.result-grade.grade-C { background: #f59e0b; }
.result-grade.grade-D { background: #6b7280; }
.result-grade.grade-unknown { background: var(--text-muted); }
.result-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-score {
  font-family: var(--font-mono);
  color: var(--text-secondary);
}
.result-error {
  color: var(--error);
  font-size: var(--font-size-xs);
}

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 批量评审进度 */
.batch-progress {
  background: var(--bg-surface);
  border: 1px solid var(--accent);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
}

.batch-progress .stats-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--accent);
}

.batch-progress .stats-title svg {
  color: var(--accent);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.progress-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.progress-percent {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

.progress-bar {
  height: 8px;
  background: var(--bg-elevated);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-stats {
  display: flex;
  gap: var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.stat-success {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--success);
}

.stat-failed {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--error);
}

.stat-time {
  margin-left: auto;
}
</style>

