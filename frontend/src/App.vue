<template>
  <!-- 초기화 전: 빈 화면으로 깜빡임 방지 -->
  <div v-if="!authStore.initialized" class="min-h-screen bg-gray-50 dark:bg-gray-950" />

  <!-- Public pages: setup / login -->
  <div v-else-if="isPublicRoute" class="min-h-screen bg-gray-50 dark:bg-gray-950">
    <RouterView />
  </div>

  <!-- Authenticated layout: 로그인 상태일 때만 렌더링 -->
  <div v-else-if="authStore.isLoggedIn" class="h-screen flex overflow-hidden bg-gray-50 dark:bg-gray-950">

    <!-- ── Mobile top bar ── -->
    <header class="lg:hidden fixed top-0 inset-x-0 h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center px-4 z-30 gap-3">
      <button
        class="text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors p-1"
        @click="drawerOpen = !drawerOpen"
        aria-label="메뉴"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <span class="text-base font-bold text-gray-900 dark:text-white tracking-tight flex-1">🎵 eztag</span>
      <button
        class="text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors p-1"
        @click="themeStore.toggle()"
      >
        <span v-if="themeStore.theme === 'dark'">☀️</span>
        <span v-else>🌙</span>
      </button>
    </header>

    <!-- ── Mobile overlay ── -->
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="drawerOpen" class="lg:hidden fixed inset-0 bg-black/50 z-40" @click="drawerOpen = false" />
    </Transition>

    <!-- ── Sidebar ── -->
    <aside
      class="fixed inset-y-0 left-0 z-50 w-60 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col
             transition-all duration-300 ease-in-out
             lg:relative lg:translate-x-0 lg:z-auto lg:shrink-0"
      :class="[
        drawerOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        sidebarCollapsed ? 'lg:w-14' : 'lg:w-60',
      ]"
    >
      <!-- Logo + 폴딩 버튼 -->
      <div class="px-3 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0 min-w-0">
        <!-- 로고: 펼침 상태 -->
        <div v-if="!sidebarCollapsed" class="flex items-center justify-between w-full min-w-0">
          <div class="min-w-0">
            <h1 class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">🎵 eztag</h1>
            <p class="text-xs text-gray-400 mt-0.5">Music Tag Manager</p>
            <p class="text-[10px] text-gray-300 dark:text-gray-600 font-mono mt-0.5">v{{ appVersion }}</p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <!-- 테마 버튼 -->
            <button
              class="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
              @click="themeStore.toggle()"
            >
              <span class="text-sm" v-if="themeStore.theme === 'dark'">☀️</span>
              <span class="text-sm" v-else>🌙</span>
            </button>
            <!-- 폴딩 버튼 -->
            <button
              class="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
              title="사이드바 접기"
              @click="toggleSidebar"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 로고: 접힘 상태 (아이콘만) -->
        <div v-else class="flex flex-col items-center w-full gap-2">
          <span class="text-xl">🎵</span>
          <!-- 펼치기 버튼 -->
          <button
            class="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
            title="사이드바 펼치기"
            @click="toggleSidebar"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Workspace Sidebar / Folder Tree (접힘 시 숨김) -->
      <div class="flex-1 overflow-hidden flex flex-col min-h-0" :class="sidebarCollapsed ? 'hidden lg:hidden' : ''">
        <WorkspaceSidebar v-if="route.path === '/workspace'" />
        <FolderTree v-else />
      </div>

      <!-- Bottom nav -->
      <nav class="shrink-0 px-2 py-2 border-t border-gray-200 dark:border-gray-800 space-y-0.5">
        <RouterLink
          v-for="item in bottomNav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          :class="sidebarCollapsed ? 'justify-center' : ''"
          :title="sidebarCollapsed ? $t(item.labelKey) : ''"
          active-class="bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white"
          @click="drawerOpen = false"
        >
          <span class="text-base shrink-0">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed">{{ $t(item.labelKey) }}</span>
        </RouterLink>

        <!-- Get LRC -->
        <RouterLink
          to="/get-lrc"
          class="flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          :class="sidebarCollapsed ? 'justify-center' : ''"
          :title="sidebarCollapsed ? 'Get LRC' : ''"
          active-class="bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white"
          @click="drawerOpen = false"
        >
          <span class="text-base shrink-0">📝</span>
          <span v-if="!sidebarCollapsed">Get LRC</span>
        </RouterLink>

        <!-- 언어 선택 -->
        <button
          class="w-full flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          :class="sidebarCollapsed ? 'justify-center' : ''"
          :title="sidebarCollapsed ? (locale === 'ko' ? '한국어' : 'English') : ''"
          @click="toggleLanguage"
        >
          <span class="text-base shrink-0">🌐</span>
          <span v-if="!sidebarCollapsed" class="flex-1 text-left">{{ locale === 'ko' ? '한국어' : 'English' }}</span>
        </button>

        <!-- 유저 메뉴 -->
        <div class="relative" ref="userMenuRef">
          <button
            class="w-full flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
            :class="sidebarCollapsed ? 'justify-center' : ''"
            :title="sidebarCollapsed ? (authStore.user?.username || '') : ''"
            @click="userMenuOpen = !userMenuOpen"
          >
            <span class="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
              {{ (authStore.user?.username || '?')[0].toUpperCase() }}
            </span>
            <span v-if="!sidebarCollapsed" class="flex-1 text-left truncate">{{ authStore.user?.username }}</span>
            <span v-if="!sidebarCollapsed" class="text-gray-300 dark:text-gray-600 text-[10px]">▾</span>
          </button>

          <!-- 드롭다운 -->
          <Transition
            enter-from-class="opacity-0 translate-y-1"
            leave-to-class="opacity-0 translate-y-1"
            enter-active-class="transition duration-100"
            leave-active-class="transition duration-100"
          >
            <div
              v-if="userMenuOpen"
              class="absolute bottom-full left-0 right-0 mb-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 py-1 overflow-hidden"
              :class="sidebarCollapsed ? 'w-36 left-full ml-2 bottom-0' : ''"
            >
              <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
                <p class="text-xs font-semibold text-gray-900 dark:text-white truncate">{{ authStore.user?.username }}</p>
                <p class="text-[10px] text-gray-400">{{ authStore.user?.role }}</p>
              </div>
              <button
                class="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                @click="openPasswordModal"
              >
                🔑 비밀번호 변경
              </button>
              <button
                class="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left"
                @click="logout"
              >
                🚪 {{ $t('auth.logout') }}
              </button>
            </div>
          </Transition>
        </div>
      </nav>

    </aside>

    <!-- ── Main content ── -->
    <main class="flex-1 overflow-hidden flex flex-col pt-14 lg:pt-0 min-w-0">
      <RouterView />
    </main>

    <!-- ── 전역 토스트 ── -->
    <ToastContainer />

    <!-- ── 비밀번호 변경 모달 ── -->
    <Transition enter-from-class="opacity-0" leave-to-class="opacity-0" enter-active-class="transition duration-150" leave-active-class="transition duration-150">
      <div v-if="showPasswordModal" class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4" @click.self="showPasswordModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl p-6">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">🔑 비밀번호 변경</h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-gray-500 block mb-1">현재 비밀번호</label>
              <input
                v-model="passwordForm.current"
                type="password"
                class="field w-full"
                placeholder="현재 비밀번호 입력"
                @keyup.enter="changePassword"
              />
            </div>
            <div>
              <label class="text-xs text-gray-500 block mb-1">새 비밀번호</label>
              <input
                v-model="passwordForm.next"
                type="password"
                class="field w-full"
                placeholder="새 비밀번호 (4자 이상)"
                @keyup.enter="changePassword"
              />
            </div>
            <div>
              <label class="text-xs text-gray-500 block mb-1">새 비밀번호 확인</label>
              <input
                v-model="passwordForm.confirm"
                type="password"
                class="field w-full"
                placeholder="새 비밀번호 재입력"
                @keyup.enter="changePassword"
              />
            </div>
            <p v-if="passwordError" class="text-xs text-red-500">{{ passwordError }}</p>
          </div>
          <div class="flex justify-end gap-2 mt-5">
            <button class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors" @click="showPasswordModal = false">취소</button>
            <button
              class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60"
              :disabled="passwordSaving"
              @click="changePassword"
            >{{ passwordSaving ? '변경 중...' : '변경' }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useThemeStore } from './stores/theme.js'
import { useAuthStore } from './stores/auth.js'
import { useWorkspaceStore } from './stores/workspace.js'
import { authApi } from './api/index.js'
import { configApi } from './api/config.js'
import FolderTree from './components/FolderTree.vue'
import WorkspaceSidebar from './components/WorkspaceSidebar.vue'
import ToastContainer from './components/ToastContainer.vue'

/* global __APP_VERSION__ */
const appVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.3.0'

const { locale } = useI18n()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()
const route = useRoute()
const router = useRouter()
const drawerOpen = ref(false)
const sidebarCollapsed = ref(localStorage.getItem('eztag-sidebar-collapsed') === 'true')

// ── 언어 변경 ──────────────────────────────────────
async function toggleLanguage() {
  const next = locale.value === 'ko' ? 'en' : 'ko'
  locale.value = next
  localStorage.setItem('eztag-lang', next)
  try {
    await configApi.update({ app_language: next })
  } catch (e) {
    console.warn('언어 설정 저장 실패:', e)
  }
}

// ── 유저 메뉴 ──────────────────────────────────────
const userMenuOpen = ref(false)
const userMenuRef = ref(null)

function onClickOutside(e) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    userMenuOpen.value = false
  }
}

// ── 비밀번호 변경 ───────────────────────────────────
const showPasswordModal = ref(false)
const passwordSaving = ref(false)
const passwordError = ref('')
const passwordForm = reactive({ current: '', next: '', confirm: '' })

function openPasswordModal() {
  userMenuOpen.value = false
  passwordForm.current = ''
  passwordForm.next = ''
  passwordForm.confirm = ''
  passwordError.value = ''
  showPasswordModal.value = true
}

function validatePassword(pwd) {
  if (pwd.length < 8) return '비밀번호는 8자 이상이어야 합니다'
  if (!/[!@#$%^&*()\-_=+[\]{}|;:'",.<>?/\\`~]/.test(pwd)) return '비밀번호에 특수문자(!@#$ 등)가 포함되어야 합니다'
  return null
}

async function changePassword() {
  passwordError.value = ''
  if (!passwordForm.current || !passwordForm.next || !passwordForm.confirm) {
    passwordError.value = '모든 항목을 입력해 주세요'
    return
  }
  const pwErr = validatePassword(passwordForm.next)
  if (pwErr) { passwordError.value = pwErr; return }
  if (passwordForm.next !== passwordForm.confirm) {
    passwordError.value = '새 비밀번호가 일치하지 않습니다'
    return
  }
  passwordSaving.value = true
  try {
    await authApi.changePassword({ current_password: passwordForm.current, new_password: passwordForm.next })
    showPasswordModal.value = false
  } catch (e) {
    passwordError.value = e.response?.data?.detail || '비밀번호 변경에 실패했습니다'
  } finally {
    passwordSaving.value = false
  }
}

// ───────────────────────────────────────────────────
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('eztag-sidebar-collapsed', String(sidebarCollapsed.value))
}

onMounted(() => {
  themeStore.apply()
  document.addEventListener('click', onClickOutside, true)
  if (authStore.isLoggedIn) {
    workspaceStore.loadCurrentSession()
  }
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
})

const isPublicRoute = computed(() => ['/setup', '/login'].includes(route.path))

const bottomNav = [
  { to: '/workspace', icon: '🗂️', labelKey: 'nav.workspace' },
  { to: '/browser',   icon: '📁', labelKey: 'nav.browser' },
  { to: '/settings',  icon: '⚙️', labelKey: 'nav.settings' },
]

function logout() {
  userMenuOpen.value = false
  authStore.logout()
  router.replace('/login')
}
</script>
