<template>
  <div class="flex flex-col h-full overflow-y-auto bg-gray-50 dark:bg-gray-950">
    <div class="p-4 pb-3 pt-5">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white mb-3">{{ t('home.title') }}</h1>
      <div class="flex gap-2">
        <button
          class="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl bg-orange-500 hover:bg-orange-400 active:bg-orange-600 text-white text-sm font-semibold transition-colors"
          @click="showWorkspacePicker = true"
        >
          <span class="text-base">📂</span>
          <span>{{ t('sidebar.openWorkspace') }}</span>
        </button>
        <button
          class="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-sm font-semibold transition-colors"
          @click="showLibraryPicker = true"
        >
          <span class="text-base">📚</span>
          <span>{{ t('sidebar.openLibrary') }}</span>
        </button>
      </div>
    </div>

    <LibraryPickerModal
      v-if="showWorkspacePicker"
      :folder-mode="true"
      area="workspace"
      @close="showWorkspacePicker = false"
      @select-folder="onSelectWorkspaceFolder"
    />
    <LibraryPickerModal
      v-if="showLibraryPicker"
      :folder-mode="true"
      area="library"
      @close="showLibraryPicker = false"
      @select-folder="onSelectLibraryFolder"
    />

    <!-- 현재 열린 폴더 -->
    <div v-if="browserStore.selectedFolder" class="px-4 mb-4">
      <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">{{ t('home.currentFolder') }}</div>
      <div
        class="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 rounded-2xl border border-blue-200 dark:border-blue-800 shadow-sm cursor-pointer active:scale-[.98] transition-transform"
        @click="router.push('/browser')"
      >
        <div
          class="w-11 h-11 rounded-xl flex items-center justify-center text-2xl shrink-0"
          :class="browserStore.currentArea === 'workspace' ? 'bg-orange-100 dark:bg-orange-900/40' : 'bg-blue-100 dark:bg-blue-900/40'"
        >{{ browserStore.currentArea === 'workspace' ? '📂' : '📚' }}</div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1.5 mb-0.5">
            <span
              v-if="browserStore.currentArea === 'workspace'"
              class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400"
            >WS</span>
            <span
              v-else-if="browserStore.currentArea === 'library'"
              class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400"
            >LIB</span>
            <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ browserStore.selectedFolder.name }}</p>
          </div>
          <p
            class="text-xs mt-0"
            :class="browserStore.currentArea === 'workspace' ? 'text-orange-500 dark:text-orange-400' : 'text-blue-500 dark:text-blue-400'"
          >
            {{ t('home.fileCount', { n: browserStore.files.length }) }}
          </p>
        </div>
        <svg class="w-4 h-4 text-blue-400 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
        </svg>
      </div>
    </div>

    <!-- 최근 폴더 -->
    <div class="px-4 flex-1">
      <div class="flex items-center justify-between mb-2">
        <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ t('home.recentFolders') }}</div>
        <button
          v-if="recentFolders.length > 0"
          class="text-[10px] text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          @click="clearRecent"
        >{{ t('home.clearRecent') }}</button>
      </div>

      <!-- 빈 상태 -->
      <div v-if="recentFolders.length === 0" class="py-16 flex flex-col items-center text-center">
        <div class="w-20 h-20 rounded-3xl bg-gray-100 dark:bg-gray-900 flex items-center justify-center text-4xl mb-4">📁</div>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('home.emptyTitle') }}</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">{{ t('home.emptyHint') }}</p>
      </div>

      <!-- 폴더 목록 -->
      <div v-else class="space-y-2 pb-8">
        <div
          v-for="item in recentFolders"
          :key="item.path"
          class="flex items-center gap-3 p-3.5 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 active:scale-[.98] transition-all"
          @click="openFolder(item)"
        >
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
            :class="item.area === 'workspace' ? 'bg-orange-100 dark:bg-orange-900/40' : item.area === 'library' ? 'bg-blue-100 dark:bg-blue-900/40' : 'bg-gray-100 dark:bg-gray-800'"
          >{{ item.area === 'workspace' ? '📂' : item.area === 'library' ? '📚' : '📁' }}</div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5 mb-0.5">
              <span
                v-if="item.area === 'workspace'"
                class="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400"
              >WS</span>
              <span
                v-else-if="item.area === 'library'"
                class="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400"
              >LIB</span>
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ item.name }}</p>
            </div>
            <p class="text-xs text-gray-400">{{ formatTime(item.timestamp) }}</p>
          </div>
          <svg class="w-4 h-4 text-gray-300 dark:text-gray-600 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useBrowserStore } from '../stores/browser.js'
import LibraryPickerModal from '../components/LibraryPickerModal.vue'
import { configApi } from '../api/config.js'

const { t, locale } = useI18n()
const router = useRouter()
const browserStore = useBrowserStore()

const RECENT_KEY = 'eztag-recent-folders'
const showWorkspacePicker = ref(false)
const showLibraryPicker = ref(false)

const recentFolders = ref([])

async function loadRecent() {
  try {
    // 서버에서 우선 로드 (기기 간 동기화)
    const { data } = await configApi.get()
    const serverRaw = data.recent_folders?.value
    if (serverRaw) {
      const serverList = JSON.parse(serverRaw)
      recentFolders.value = serverList
      // 로컬도 최신 상태로 갱신
      localStorage.setItem(RECENT_KEY, serverRaw)
      return
    }
  } catch { /* ignore */ }
  // 서버에 없으면 로컬 fallback
  try {
    recentFolders.value = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  } catch {
    recentFolders.value = []
  }
}

function clearRecent() {
  recentFolders.value = []
  localStorage.removeItem(RECENT_KEY)
  configApi.update({ recent_folders: '[]' }).catch(() => {})
}

onMounted(loadRecent)

function openFolder(item) {
  browserStore.selectFolder({ name: item.name, path: item.path }, [{ name: item.name, path: item.path }], item.area || null)
  router.push('/browser')
}

function onSelectWorkspaceFolder(folder) {
  showWorkspacePicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'workspace')
  router.push('/browser')
}

function onSelectLibraryFolder(folder) {
  showLibraryPicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'library')
  router.push('/browser')
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diffMin = Math.floor((now - d) / 60000)
  if (diffMin < 1) return t('home.justNow')
  if (diffMin < 60) return t('home.minutesAgo', { n: diffMin })
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return t('home.hoursAgo', { n: diffHour })
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 7) return t('home.daysAgo', { n: diffDay })
  return d.toLocaleDateString(locale.value === 'ko' ? 'ko-KR' : 'en-US', { month: 'long', day: 'numeric' })
}
</script>
