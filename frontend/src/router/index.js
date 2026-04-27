import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ArticleView from '@/views/ArticleView.vue'
import BookmarksView from '@/views/BookmarksView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes = [
  { path: '/', component: HomeView, meta: { title: 'AI情报站' } },
  { path: '/article/:id', component: ArticleView, meta: { title: '文章详情' } },
  { path: '/bookmarks', component: BookmarksView, meta: { title: '我的收藏' } },
  { path: '/settings', component: SettingsView, meta: { title: '设置' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - AI情报站` : 'AI情报站'
})

export default router
