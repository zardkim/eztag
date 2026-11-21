import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './assets/main.css'
import { registerSW } from 'virtual:pwa-register'

// Apply saved theme before mount (prevents flash of wrong theme)
const savedTheme = localStorage.getItem('eztag-theme') || 'dark'
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark')
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')

// ── 서비스워커 업데이트 ──────────────────────────────────────
// vite-plugin-pwa 가 자동 주입하던 registerSW.js 는 "등록"만 한다.
// registerType:'autoUpdate' 로 새 서비스워커가 활성화돼도, 이미 떠 있는
// 화면은 메모리에 있는 예전 번들을 계속 쓴다. 그래서 PWA 를 완전히
// 재시작하기 전까지 옛 코드로 동작했다.
// → 새 버전이 준비되면 직접 새로고침한다.
registerSW({
  immediate: true,
  onNeedRefresh() {
    // 사용자가 태그 저장 중일 수 있으므로 잠깐 알리고 넘어간다
    try {
      const el = document.createElement('div')
      el.textContent = '새 버전으로 업데이트합니다…'
      el.style.cssText =
        'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:999999;' +
        'background:#1e293b;color:#fff;padding:10px 16px;border-radius:12px;font-size:13px;' +
        'box-shadow:0 8px 24px rgba(0,0,0,.3)'
      document.body.appendChild(el)
    } catch { /* ignore */ }
    setTimeout(() => window.location.reload(), 1200)
  },
  onRegisteredSW(_url, reg) {
    if (!reg) return
    // 오래 켜둔 PWA 도 새 버전을 집도록 주기적으로 확인한다
    setInterval(() => reg.update().catch(() => {}), 60 * 60 * 1000)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') reg.update().catch(() => {})
    })
  },
})
