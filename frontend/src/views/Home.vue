<template>
  <div class="flex flex-col h-full overflow-y-auto bg-gray-50 dark:bg-gray-950">
    <div class="p-4 pb-2 pt-5">
      <h1 class="text-lg font-bold text-gray-900 dark:text-white">홈</h1>
    </div>

    <!-- 현재 열린 폴더 -->
    <div v-if="browserStore.selectedFolder" class="px-4 mb-4">
      <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">현재 폴더</div>
      <div
        class="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 rounded-2xl border border-blue-200 dark:border-blue-800 shadow-sm cursor-pointer active:scale-[.98] transition-transform"
        @click="router.push('/browser')"
      >
        <div class="w-11 h-11 rounded-xl bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-2xl shrink-0">📂</div>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ browserStore.selectedFolder.name }}</p>
          <p class="text-xs text-blue-500 dark:text-blue-400 mt-0.5">
            {{ browserStore.files.length }}개 파일 · 탭하여 편집
          </p>
        </div>
        <svg class="w-4 h-4 text-blue-400 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
        </svg>
      </div>
    </div>

    <!-- 최근 폴더 -->
    <div class="px-4 flex-1">
      <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">최근 폴더</div>

      <!-- 빈 상태 -->
      <div v-if="recentFolders.length === 0" class="py-16 flex flex-col items-center text-center">
        <div class="w-20 h-20 rounded-3xl bg-gray-100 dark:bg-gray-900 flex items-center justify-center text-4xl mb-4">📁</div>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">최근 작업한 폴더가 없습니다</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">하단 <strong class="text-gray-500 dark:text-gray-400">+</strong> 버튼으로 폴더를 열어보세요</p>
      </div>

      <!-- 폴더 목록 -->
      <div v-else class="space-y-2 pb-8">
        <div
          v-for="item in recentFolders"
          :key="item.path"
          class="flex items-center gap-3 p-3.5 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 active:scale-[.98] transition-all"
          @click="openFolder(item)"
        >
          <div class="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-xl shrink-0">📁</div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ item.name }}</p>
            <p class="text-xs text-gray-400 mt-0.5">{{ formatTime(item.timestamp) }}</p>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBrowserStore } from '../stores/browser.js'

const router = useRouter()
const browserStore = useBrowserStore()

const RECENT_KEY = 'eztag-recent-folders'

const recentFolders = computed(() => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  } catch {
    return []
  }
})

function openFolder(item) {
  browserStore.selectFolder({ name: item.name, path: item.path }, [{ name: item.name, path: item.path }])
  router.push('/browser')
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diffMin = Math.floor((now - d) / 60000)
  if (diffMin < 1) return '방금 전'
  if (diffMin < 60) return `${diffMin}분 전`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}시간 전`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 7) return `${diffDay}일 전`
  return d.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
}
</script>
