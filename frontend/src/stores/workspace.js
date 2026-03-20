import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workspaceApi } from '../api/index.js'

export const useWorkspaceStore = defineStore('workspace', () => {
  // ── 상태 ────────────────────────────────────────────────
  const session = ref(null)          // 현재 세션 객체
  const items = ref([])              // WorkspaceItem[]
  const loading = ref(false)
  const selectedItemId = ref(null)   // 선택된 아이템 id

  // ── computed ─────────────────────────────────────────────
  const selectedItem = computed(() =>
    items.value.find(i => i.id === selectedItemId.value) || null
  )

  const pendingCount = computed(() =>
    items.value.filter(i => i.has_changes).length
  )

  const sessionId = computed(() => session.value?.id || null)

  // Browser.vue 호환용: files 형식으로 변환
  const files = computed(() =>
    items.value.map(item => {
      const tags = { ...(item.original_tags || {}), ...(item.pending_tags || {}) }
      return {
        path: item.file_path,
        filename: item.filename,
        title: tags.title || item.filename,
        artist: tags.artist || '',
        album_title: tags.album || tags.album_title || '',
        album_artist: tags.album_artist || '',
        track_no: tags.track_no || null,
        disc_no: tags.disc_no || null,
        year: tags.year || null,
        genre: tags.genre || '',
        label: tags.label || '',
        duration: tags.duration || null,
        bitrate: tags.bitrate || null,
        sample_rate: tags.sample_rate || null,
        file_format: tags.file_format || item.filename.split('.').pop()?.toLowerCase() || '',
        has_cover: tags.has_cover || false,
        has_lrc: false,
        comment: tags.comment || '',
        // 워크스페이스 전용
        _workspace_item_id: item.id,
        _has_changes: item.has_changes,
        _status: item.status,
        _apply_error: item.apply_error,
      }
    })
  )

  // ── 액션 ─────────────────────────────────────────────────

  async function loadCurrentSession() {
    loading.value = true
    try {
      const { data } = await workspaceApi.getCurrentSession()
      session.value = data
      items.value = data.items || []
    } catch (e) {
      console.error('loadCurrentSession error', e)
    } finally {
      loading.value = false
    }
  }

  async function newSession() {
    loading.value = true
    try {
      const { data } = await workspaceApi.newSession()
      session.value = data
      items.value = data.items || []
      selectedItemId.value = null
    } finally {
      loading.value = false
    }
  }

  async function loadFolder(folderPath, recursive = false) {
    loading.value = true
    try {
      const { data } = await workspaceApi.loadFolder(folderPath, recursive)
      session.value = data.session
      items.value = data.session.items || []
      return { added: data.added, skipped: data.skipped }
    } finally {
      loading.value = false
    }
  }

  async function loadFiles(filePaths) {
    loading.value = true
    try {
      const { data } = await workspaceApi.loadFiles(filePaths)
      session.value = data.session
      items.value = data.session.items || []
      return { added: data.added, skipped: data.skipped, errors: data.errors }
    } finally {
      loading.value = false
    }
  }

  async function stageTags(itemId, tags) {
    const { data } = await workspaceApi.stageTags(itemId, tags)
    _updateItem(data)
    return data
  }

  async function stageRename(itemId, newName) {
    const { data } = await workspaceApi.stageRename(itemId, newName)
    _updateItem(data)
    return data
  }

  async function unstageTags(itemId) {
    const { data } = await workspaceApi.unstageTags(itemId)
    _updateItem(data)
  }

  async function applyItem(itemId) {
    const { data } = await workspaceApi.applyItem(itemId)
    if (data.item) _updateItem(data.item)
    return data
  }

  async function applySession() {
    if (!sessionId.value) return
    loading.value = true
    try {
      const { data } = await workspaceApi.applySession(sessionId.value)
      // 아이템 상태 갱신
      await loadCurrentSession()
      return data
    } finally {
      loading.value = false
    }
  }

  async function removeItem(itemId) {
    await workspaceApi.removeItem(itemId)
    items.value = items.value.filter(i => i.id !== itemId)
    if (selectedItemId.value === itemId) selectedItemId.value = null
  }

  async function clearItems() {
    await workspaceApi.clearItems()
    items.value = []
    selectedItemId.value = null
  }

  function selectItem(itemId) {
    selectedItemId.value = itemId
  }

  function _updateItem(updated) {
    const idx = items.value.findIndex(i => i.id === updated.id)
    if (idx !== -1) items.value[idx] = updated
  }

  return {
    session,
    items,
    loading,
    selectedItemId,
    selectedItem,
    pendingCount,
    sessionId,
    files,
    loadCurrentSession,
    newSession,
    loadFolder,
    loadFiles,
    stageTags,
    stageRename,
    unstageTags,
    applyItem,
    applySession,
    removeItem,
    clearItems,
    selectItem,
  }
})
