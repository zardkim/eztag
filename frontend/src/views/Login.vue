<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <!-- 언어 변경 버튼 -->
      <div class="flex justify-end mb-3">
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:text-gray-900 hover:bg-white dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          @click="toggleLanguage"
        >
          <span>🌐</span>
          <span>{{ locale === 'ko' ? '한국어' : 'English' }}</span>
        </button>
      </div>

      <div class="flex justify-center mb-8">
        <img
          src="/logo.svg"
          alt="eztag"
          class="h-14 w-auto dark:hidden"
        />
        <img
          src="/logo-dark.svg"
          alt="eztag"
          class="h-14 w-auto hidden dark:block"
        />
      </div>

      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-6">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-5">{{ $t('login.title') }}</h2>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('setup.username') }}</label>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              required
              class="field w-full"
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('setup.password') }}</label>
            <input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              required
              class="field w-full"
            />
          </div>

          <p v-if="errorMsg" class="text-red-500 text-xs">{{ errorMsg }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {{ loading ? $t('common.loading') : $t('login.submit') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { authApi } from '../api/index.js'
import { useAuthStore } from '../stores/auth.js'

const { t, locale } = useI18n()

function toggleLanguage() {
  const next = locale.value === 'ko' ? 'en' : 'ko'
  locale.value = next
  localStorage.setItem('eztag-lang', next)
}
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const errorMsg = ref('')
const form = reactive({ username: '', password: '' })

async function submit() {
  errorMsg.value = ''
  loading.value = true
  try {
    const { data } = await authApi.login(form)
    authStore.setToken(data.token)
    authStore.setUser({ username: data.username, role: data.role })
    router.replace('/browser')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || t('login.failed')
  } finally {
    loading.value = false
  }
}
</script>
