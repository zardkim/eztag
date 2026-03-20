<template>
  <div class="flex flex-col h-full min-h-0 select-none">

    <!-- 헤더 -->
    <div class="px-3 pt-3 pb-2 shrink-0">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">워크스페이스</span>
        <div class="flex gap-1">
          <!-- 새 세션 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-xs"
            title="새 세션 시작"
            @click="confirmNewSession"
          >↺</button>
        </div>
      </div>

      <!-- 세션 상태 배지 -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-gray-400">{{ workspaceStore.items.length }}개 파일</span>
        <span
          v-if="workspaceStore.pendingCount > 0"
          class="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 font-medium"
        >{{ workspaceStore.pendingCount }}개 변경됨</span>
      </div>
    </div>

    <!-- 폴더 열기 버튼 -->
    <div class="px-3 pb-2 shrink-0">
      <button
        class="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-dashed border-blue-300 dark:border-blue-700 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
        @click="showPicker = true"
      >
        <span>📂</span>
        <span>폴더 열기</span>
      </button>
    </div>

    <!-- 아이템 목록 -->
    <div class="flex-1 overflow-y-auto min-h-0 px-2">
      <!-- 빈 상태 -->
      <div v-if="workspaceStore.items.length === 0" class="flex flex-col items-center justify-center py-8 text-center px-2">
        <p class="text-2xl mb-2">📭</p>
        <p class="text-[11px] text-gray-400 leading-relaxed">폴더를 열어 파일을 워크스페이스에 추가하세요.</p>
      </div>

      <!-- 그룹핑된 파일 목록 -->
      <div v-else class="space-y-0.5 pb-2">
        <div
          v-for="item in workspaceStore.items"
          :key="item.id"
          class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors text-left group"
          :class="workspaceStore.selectedItemId === item.id
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
          @click="workspaceStore.selectItem(item.id)"
        >
          <!-- 상태 dot -->
          <span class="w-1.5 h-1.5 rounded-full shrink-0 mt-0.5"
            :class="item.has_changes ? 'bg-yellow-400' : item.status === 'applied' ? 'bg-green-400' : 'bg-gray-300 dark:bg-gray-600'"
          ></span>
          <span class="flex-1 text-[11px] truncate">{{ item.filename }}</span>
          <!-- 제거 버튼 -->
          <button
            class="shrink-0 w-4 h-4 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 text-xs"
            @click.stop="workspaceStore.removeItem(item.id)"
          >✕</button>
        </div>
      </div>
    </div>

    <!-- 전체 적용 버튼 -->
    <div class="px-3 py-2 border-t border-gray-200 dark:border-gray-800 shrink-0 space-y-1.5">
      <button
        class="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors"
        :class="workspaceStore.pendingCount > 0
          ? 'bg-blue-600 hover:bg-blue-500 text-white'
          : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'"
        :disabled="workspaceStore.pendingCount === 0 || workspaceStore.loading"
        @click="showApply = true"
      >
        <span>✅</span>
        <span>{{ workspaceStore.loading ? '적용 중...' : `전체 적용 (${workspaceStore.pendingCount})` }}</span>
      </button>

      <!-- 히스토리 토글 -->
      <button
        class="w-full flex items-center justify-between px-2 py-1 text-[11px] text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
        @click="showHistory = !showHistory"
      >
        <span>📋 히스토리</span>
        <span>{{ showHistory ? '▲' : '▼' }}</span>
      </button>
    </div>

    <!-- 히스토리 섹션 -->
    <div v-if="showHistory" class="shrink-0 border-t border-gray-200 dark:border-gray-800 max-h-48 overflow-y-auto">
      <div v-if="historyLoading" class="px-3 py-3 text-xs text-gray-400 text-center">불러오는 중...</div>
      <div v-else-if="history.length === 0" class="px-3 py-3 text-xs text-gray-400 text-center">히스토리 없음</div>
      <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
        <div
          v-for="s in history"
          :key="s.id"
          class="px-3 py-2 text-[10px] text-gray-500 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-start justify-between gap-2"
        >
          <div class="min-w-0">
            <p class="text-gray-700 dark:text-gray-300 font-medium truncate">{{ fmtDate(s.created_at) }}</p>
            <p class="truncate">{{ s.item_count }}개 파일 · {{ s.status }}</p>
          </div>
          <button
            class="shrink-0 text-red-300 hover:text-red-500 transition-colors"
            title="삭제"
            @click="deleteHistory(s.id)"
          >✕</button>
        </div>
      </div>
    </div>

    <!-- LibraryPickerModal -->
    <LibraryPickerModal
      v-if="showPicker"
      @close="showPicker = false"
      @added="showPicker = false"
    />

    <!-- ApplyPreviewModal -->
    <ApplyPreviewModal
      v-if="showApply"
      @close="showApply = false"
      @applied="showApply = false"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { workspaceApi } from '../api/index.js'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useToastStore } from '../stores/toast.js'
import LibraryPickerModal from './LibraryPickerModal.vue'
import ApplyPreviewModal from './ApplyPreviewModal.vue'

const workspaceStore = useWorkspaceStore()
const toastStore = useToastStore()

const showPicker = ref(false)
const showApply = ref(false)
const showHistory = ref(false)
const history = ref([])
const historyLoading = ref(false)

async function confirmNewSession() {
  if (workspaceStore.pendingCount > 0) {
    if (!confirm(`변경되지 않은 내용이 ${workspaceStore.pendingCount}개 있습니다.\n새 세션을 시작하면 현재 변경 사항이 사라집니다.\n계속하시겠습니까?`)) return
  }
  await workspaceStore.newSession()
  toastStore.success('새 세션이 시작되었습니다.')
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const { data } = await workspaceApi.getHistory({ page: 1, page_size: 10 })
    history.value = data.sessions
  } catch (e) {
    console.error(e)
  } finally {
    historyLoading.value = false
  }
}

async function deleteHistory(id) {
  try {
    await workspaceApi.deleteHistory(id)
    history.value = history.value.filter(s => s.id !== id)
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  }
}

function fmtDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

watch(showHistory, (v) => { if (v && history.value.length === 0) loadHistory() })
</script>
