import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('eztag-token') || null)
  const user = ref(null)
  const initialized = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t) {
    token.value = t
    if (t) {
      localStorage.setItem('eztag-token', t)
    } else {
      localStorage.removeItem('eztag-token')
    }
  }

  function setUser(u) {
    user.value = u
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('eztag-token')
  }

  return { token, user, isLoggedIn, initialized, setToken, setUser, logout }
})
