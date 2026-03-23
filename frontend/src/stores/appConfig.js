import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppConfigStore = defineStore('appConfig', () => {
  const siteName    = ref(localStorage.getItem('eztag-site-name')    || 'eztag')
  const browserTitle = ref(localStorage.getItem('eztag-browser-title') || 'eztag')

  function apply(config) {
    const name  = config.site_name?.value    || 'eztag'
    const title = config.browser_title?.value || 'eztag'
    siteName.value     = name
    browserTitle.value = title
    localStorage.setItem('eztag-site-name',    name)
    localStorage.setItem('eztag-browser-title', title)
  }

  return { siteName, browserTitle, apply }
})
