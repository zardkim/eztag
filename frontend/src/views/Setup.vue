<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">🎵 eztag</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ $t('setup.subtitle') }}</p>
      </div>

      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-6">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-5">{{ $t('setup.title') }}</h2>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('setup.username') }}</label>
            <input
              v-model="form.username"
              type="text"
              autocomplete="username"
              required
              class="field w-full"
              :placeholder="$t('setup.usernamePlaceholder')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('setup.password') }}</label>
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              required
              minlength="8"
              class="field w-full"
              :placeholder="$t('setup.passwordPlaceholder')"
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('setup.passwordConfirm') }}</label>
            <input
              v-model="form.passwordConfirm"
              type="password"
              autocomplete="new-password"
              required
              class="field w-full"
              :placeholder="$t('setup.passwordConfirmPlaceholder')"
            />
          </div>

          <p v-if="errorMsg" class="text-red-500 text-xs">{{ errorMsg }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {{ loading ? $t('common.saving') : $t('setup.createAccount') }}
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

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const errorMsg = ref('')
const form = reactive({ username: '', password: '', passwordConfirm: '' })

function validatePassword(pwd) {
  if (pwd.length < 8) return '비밀번호는 8자 이상이어야 합니다'
  if (!/[!@#$%^&*()\-_=+[\]{}|;:'",.<>?/\\`~]/.test(pwd)) return '비밀번호에 특수문자(!@#$ 등)가 포함되어야 합니다'
  return null
}

async function submit() {
  errorMsg.value = ''
  const pwErr = validatePassword(form.password)
  if (pwErr) { errorMsg.value = pwErr; return }
  if (form.password !== form.passwordConfirm) {
    errorMsg.value = t('setup.passwordMismatch')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.setup({ username: form.username, password: form.password })
    authStore.setToken(data.token)
    authStore.setUser({ username: data.username, role: data.role })
    router.replace('/browser')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || t('common.error')
  } finally {
    loading.value = false
  }
}
</script>
