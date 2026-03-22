import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'

const routes = [
  { path: '/setup',    component: () => import('../views/Setup.vue'),   meta: { title: '초기 설정', public: true } },
  { path: '/login',    component: () => import('../views/Login.vue'),   meta: { title: '로그인', public: true } },
  { path: '/',         redirect: '/home' },
  { path: '/home',     component: () => import('../views/Home.vue'),      meta: { title: '홈' } },
  { path: '/workspace', component: () => import('../views/Workspace.vue'), meta: { title: '워크스페이스' } },
  { path: '/browser',  component: () => import('../views/Browser.vue'), meta: { title: '파일 브라우저' } },
  { path: '/settings', component: () => import('../views/Settings.vue'),meta: { title: '설정' } },
  { path: '/get-lrc',  component: () => import('../views/GetLrc.vue'),  meta: { title: 'Get LRC' } },
  // Legacy routes kept
  { path: '/albums',   component: () => import('../views/Albums.vue'),  meta: { title: '앨범' } },
  { path: '/albums/:id', component: () => import('../views/AlbumDetail.vue'), meta: { title: '앨범 상세' } },
  { path: '/artists',  component: () => import('../views/Artists.vue'), meta: { title: '아티스트' } },
  { path: '/tracks',   component: () => import('../views/Tracks.vue'),  meta: { title: '트랙' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // 최초 진입 시 토큰 유효성 확인 (async 완료 후 initialized 설정)
  if (!authStore.initialized) {
    if (authStore.isLoggedIn) {
      try {
        const { data } = await authApi.me()
        authStore.setUser({ username: data.username, role: data.role })
      } catch {
        authStore.logout()
      }
    }
    authStore.initialized = true
  }

  // Public routes
  if (to.meta.public) {
    if (authStore.isLoggedIn && to.path !== '/setup') {
      return '/workspace'
    }
    return true
  }

  // Protected routes: must be logged in
  if (!authStore.isLoggedIn) {
    try {
      const { data } = await authApi.checkSetup()
      if (data.needs_setup) return '/setup'
    } catch {
      // ignore
    }
    return '/login'
  }

  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'eztag'} - eztag`
})

export default router
