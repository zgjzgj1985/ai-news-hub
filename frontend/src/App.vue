<template>
  <div class="app">
    <nav class="navbar">
      <div class="container navbar-inner">
        <router-link to="/" class="logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="var(--accent)" stroke-width="1.5"/>
            <circle cx="12" cy="12" r="4" fill="var(--accent)"/>
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>AI情报站</span>
        </router-link>

        <div class="nav-links hide-mobile">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">资讯</router-link>
          <router-link to="/bookmarks" class="nav-link" :class="{ active: $route.path === '/bookmarks' }">
            收藏
            <span v-if="bookmarkCount > 0" class="badge">{{ bookmarkCount }}</span>
          </router-link>
          <router-link to="/settings" class="nav-link" :class="{ active: $route.path === '/settings' }">设置</router-link>
        </div>

        <div class="nav-right">
          <button class="btn btn-ghost btn-sm" @click="refresh" :disabled="refreshing" title="刷新">
            <svg :class="{ spinning: refreshing }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            <span class="hide-mobile">{{ refreshing ? '刷新中...' : '刷新' }}</span>
          </button>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useArticleStore } from '@/stores/articles'
import { fetchBookmarks } from '@/api'
import { triggerRefresh } from '@/api'

const store = useArticleStore()
const bookmarkCount = ref(0)
const refreshing = ref(false)

async function loadBookmarkCount() {
  try {
    const data = await fetchBookmarks()
    bookmarkCount.value = data.length
  } catch (e) {
    // ignore
  }
}

async function refresh() {
  refreshing.value = true
  try {
    await triggerRefresh()
    await new Promise(r => setTimeout(r, 2000))
    await store.loadArticles()
    await store.loadStats()
  } catch (e) {
    console.warn(e)
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadBookmarkCount()
})
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(13, 17, 23, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  gap: var(--space-4);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
}
.logo:hover {
  color: var(--accent);
  text-decoration: none;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex: 1;
  margin-left: var(--space-6);
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  text-decoration: none;
}
.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
  text-decoration: none;
}
.nav-link.active {
  color: var(--accent);
  background: var(--accent-dim);
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
  background: var(--accent);
  color: #0d1117;
  border-radius: 9px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.main-content {
  min-height: calc(100vh - 56px);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
