<template>
  <div class="fixed inset-0 bg-black/60 z-[300] flex items-end sm:items-center justify-center p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-lg shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[80vh]">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
        <div>
          <h3 class="text-base font-semibold text-gray-900 dark:text-white">✅ 변경 사항 적용</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ pendingItems.length }}개 파일에 변경 사항을 실제 파일에 반영합니다.</p>
        </div>
        <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>

      <!-- 목록 -->
      <div class="flex-1 overflow-y-auto min-h-0 px-5 py-3 space-y-2">
        <div v-if="pendingItems.length === 0" class="text-center py-8">
          <p class="text-sm text-gray-400">변경된 파일이 없습니다.</p>
        </div>
        <div
          v-for="item in pendingItems"
          :key="item.id"
          class="bg-gray-50 dark:bg-gray-800 rounded-xl px-3 py-2.5"
        >
          <p class="text-xs font-medium text-gray-900 dark:text-white truncate mb-1.5">{{ item.filename }}</p>
          <!-- 태그 변경 항목 -->
          <div v-if="item.pending_tags && Object.keys(item.pending_tags).length > 0" class="space-y-1.5">
            <div
              v-for="(val, key) in item.pending_tags"
              :key="key"
              class="text-[11px]"
            >
              <span class="text-gray-400 block">{{ fieldLabel(key) }}</span>
              <div class="flex items-start gap-1.5 mt-0.5 flex-wrap">
                <span class="text-red-400 line-through truncate">{{ originalVal(item, key) }}</span>
                <span class="text-gray-300 dark:text-gray-600 shrink-0">→</span>
                <span class="text-green-600 dark:text-green-400 font-medium break-all">{{ val }}</span>
              </div>
            </div>
          </div>
          <!-- 파일명 변경 -->
          <div v-if="item.pending_rename" class="text-[11px] mt-1.5">
            <span class="text-gray-400 block">파일명</span>
            <div class="flex items-start gap-1.5 mt-0.5 flex-wrap">
              <span class="text-red-400 line-through truncate">{{ item.filename }}</span>
              <span class="text-gray-300 dark:text-gray-600 shrink-0">→</span>
              <span class="text-green-600 dark:text-green-400 font-medium break-all">{{ item.pending_rename }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-800 flex justify-end gap-2 shrink-0 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))]">
        <button
          class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
          :disabled="applying"
          @click="$emit('close')"
        >취소</button>
        <button
          class="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm rounded-lg transition-colors"
          :disabled="applying || pendingItems.length === 0"
          @click="doApply"
        >{{ applying ? '적용 중...' : `✅ ${pendingItems.length}개 파일에 적용` }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useToastStore } from '../stores/toast.js'

const emit = defineEmits(['close', 'applied'])
const workspaceStore = useWorkspaceStore()
const toastStore = useToastStore()

const applying = ref(false)

const pendingItems = computed(() =>
  workspaceStore.items.filter(i => i.has_changes)
)

const FIELD_LABELS = {
  title: '제목', artist: '아티스트', album_artist: '앨범 아티스트',
  album_title: '앨범', album: '앨범', genre: '장르', year: '연도',
  track_no: '트랙 번호', disc_no: '디스크', lyrics: '가사', label: '레이블',
  comment: '코멘트',
}

function fieldLabel(key) {
  return FIELD_LABELS[key] || key
}

function originalVal(item, key) {
  return item.original_tags?.[key] ?? '(없음)'
}

async function doApply() {
  applying.value = true
  try {
    const result = await workspaceStore.applySession()
    if (result.errors > 0) {
      toastStore.error(`${result.applied}개 적용, ${result.errors}개 오류`)
    } else {
      toastStore.success(`${result.applied}개 파일 적용 완료`)
    }
    emit('applied')
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    applying.value = false
  }
}
</script>
