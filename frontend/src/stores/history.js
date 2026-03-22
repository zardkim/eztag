/**
 * 전역 편집 히스토리 스토어 (undo / redo)
 *
 * 엔트리 구조:
 *   {
 *     label : string,               // 툴팁용 설명 ("태그 편집 (3개)", ...)
 *     ops   : [{                    // 파일별 연산 목록
 *       path  : string,
 *       before: { field: value|null },  // 변경 전 (null = 공백)
 *       after : { field: value|null },  // 변경 후
 *     }]
 *   }
 *
 * 적용 규칙: null/undefined/''/0 값인 필드는 clear_fields 로 전달
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

const MAX_HISTORY = 50

export const useHistoryStore = defineStore('history', () => {
  const stack  = ref([])   // 히스토리 엔트리 배열
  const cursor = ref(-1)   // 현재 위치 (-1 = 비어있음)
  const busy   = ref(false)

  const canUndo  = computed(() => cursor.value >= 0)
  const canRedo  = computed(() => cursor.value < stack.value.length - 1)
  const undoLabel = computed(() => canUndo.value  ? stack.value[cursor.value].label     : null)
  const redoLabel = computed(() => canRedo.value  ? stack.value[cursor.value + 1].label : null)

  /** 새 엔트리 추가 (redo 히스토리 삭제 후 push) */
  function push(entry) {
    stack.value = stack.value.slice(0, cursor.value + 1)
    stack.value.push(entry)
    if (stack.value.length > MAX_HISTORY) stack.value.shift()
    cursor.value = stack.value.length - 1
  }

  /** 파일에 state 적용 — null 값은 clear_fields 로 처리 */
  async function _applyState(ops, direction, browserStore) {
    for (const op of ops) {
      const state = direction === 'undo' ? op.before : op.after
      if (!state || !Object.keys(state).length) continue

      const toSet   = {}
      const toClear = []
      for (const [k, v] of Object.entries(state)) {
        if (v === null || v === undefined || v === '') toClear.push(k)
        else toSet[k] = v
      }

      await browseApi.batchWriteTags({ paths: [op.path], ...toSet, clear_fields: toClear })

      const storeUpdate = {
        ...toSet,
        ...Object.fromEntries(toClear.map(k => [k, null])),
      }
      browserStore.updateFiles([op.path], storeUpdate)
      if (browserStore.selectedFile?.path === op.path) {
        browserStore.selectFile({ ...browserStore.selectedFile, ...storeUpdate })
      }
    }
    // 현재 폴더 캐시 무효화 (다음 진입 시 최신 반영)
    const folder = browserStore.selectedFolder?.path
    if (folder) browserStore.invalidateFilesCache(folder)
  }

  async function undo(browserStore) {
    if (!canUndo.value || busy.value) return
    busy.value = true
    try {
      const entry = stack.value[cursor.value]
      await _applyState(entry.ops, 'undo', browserStore)
      cursor.value--
    } finally {
      busy.value = false
    }
  }

  async function redo(browserStore) {
    if (!canRedo.value || busy.value) return
    busy.value = true
    try {
      cursor.value++
      const entry = stack.value[cursor.value]
      await _applyState(entry.ops, 'redo', browserStore)
    } finally {
      busy.value = false
    }
  }

  function clear() {
    stack.value = []
    cursor.value = -1
  }

  return {
    stack, cursor, busy,
    canUndo, canRedo, undoLabel, redoLabel,
    push, undo, redo, clear,
  }
})
