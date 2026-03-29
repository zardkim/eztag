<template>
  <div class="flex flex-col h-full">
    <!-- 파일 검색 입력 -->
    <div class="px-2 pt-2 pb-1 shrink-0">
      <input
        v-model="browserStore.filterText"
        class="w-full px-2.5 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        :placeholder="$t('browser.filterPlaceholder')"
      />
    </div>

    <div class="px-3 py-1.5 flex items-center justify-between">
      <span class="text-xs font-semibold text-gray-400 dark:text-gray-600 uppercase tracking-wider">{{ $t('browser.folders') }}</span>
      <button
        class="w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :class="loading ? 'animate-spin' : ''"
        title="폴더 목록 새로고침"
        :disabled="loading"
        @click="refreshRoots"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <div v-if="loading" class="px-3 py-2 text-xs text-gray-400">{{ $t('common.loading') }}</div>
    <div v-else-if="roots.length === 0" class="px-3 py-2 text-xs text-gray-400">{{ $t('browser.noFolders') }}</div>

    <div v-else class="flex-1 overflow-y-auto px-1 pb-2 space-y-0.5">
      <FolderNode
        v-for="node in roots"
        :key="node.path"
        :node="node"
        :depth="0"
        :selected-path="browserStore.selectedFolder?.path"
        :initial-children="node.children ?? null"
        @select="onFolderSelect($event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import FolderNode from './FolderNode.vue'
import { browseApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { sessionCache } from '../utils/cache.js'

const browserStore = useBrowserStore()
const router = useRouter()
const route = useRoute()
const roots = ref([])
const loading = ref(false)

const ROOTS_CACHE_KEY = 'roots'
const ROOTS_TTL = 5 * 60 * 1000  // 5분

function onFolderSelect(folder) {
  // 선택된 폴더의 하위 캐시 무효화 → 외부 변경사항 즉시 반영
  sessionCache.delete(`children:${folder.path}`)
  browserStore.selectFolder(folder)
  if (route.path !== '/browser') {
    router.push('/browser')
  }
}

async function loadRoots(force = false) {
  // 캐시 확인 (강제 새로고침이 아닐 때)
  if (!force) {
    const cached = sessionCache.get(ROOTS_CACHE_KEY)
    if (cached) {
      roots.value = cached
      return
    }
  }

  loading.value = true
  try {
    const { data } = await browseApi.getRoots(true, force)
    const result = data.length === 1 && data[0].children?.length > 0
      ? data[0].children
      : data
    roots.value = result
    sessionCache.set(ROOTS_CACHE_KEY, result, ROOTS_TTL)
  } catch {
    roots.value = []
  } finally {
    loading.value = false
  }
}

// 새로고침 버튼: 강제 재로드
async function refreshRoots() {
  sessionCache.delete(ROOTS_CACHE_KEY)
  sessionCache.deleteByPrefix('children:')
  await loadRoots(true)
}

onMounted(() => loadRoots())
</script>
