<template>
  <div class="app">
    <nav class="navbar">
      <div class="container-wide navbar-inner">
        <router-link to="/" class="logo">
          <span class="logo-text">AI情报站</span>
          <span class="logo-tagline">前沿资讯精选</span>
        </router-link>

        <div class="nav-links hide-mobile">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
            <span class="nav-label">资讯</span>
          </router-link>
          <router-link to="/bookmarks" class="nav-link" :class="{ active: $route.path === '/bookmarks' }">
            <span class="nav-label">收藏</span>
            <span v-if="bookmarkCount > 0" class="nav-badge">{{ bookmarkCount }}</span>
          </router-link>
          <router-link to="/settings" class="nav-link" :class="{ active: $route.path === '/settings' }">
            <span class="nav-label">设置</span>
          </router-link>
        </div>

        <div class="nav-right">
          <button class="btn btn-ghost btn-sm" @click="refresh" :disabled="refreshing">
            <svg :class="{ spinning: refreshing }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
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
  } catch (e) {}
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
  background: var(--bg-base);
  border-bottom: 3px solid var(--text-primary);
  height: var(--navbar-height);
  display: flex;
  align-items: center;
}

.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.logo {
  text-decoration: none;
  display: flex;
  flex-direction: column;
}

.logo-text {
  font-family: var(--font-serif);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.logo-tagline {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
  padding: var(--space-2) 0;
  border-bottom: 2px solid transparent;
  margin-bottom: -3px;
}

.nav-link:hover {
  color: var(--text-primary);
  opacity: 1;
}

.nav-link.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}

.nav-label {
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  background: var(--accent);
  border-radius: 9px;
}

.nav-right {
  display: flex;
  align-items: center;
}

.main-content {
  min-height: calc(100vh - var(--navbar-height));
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
