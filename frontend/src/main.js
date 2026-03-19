import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './assets/main.css'

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
