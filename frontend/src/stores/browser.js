import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

// 모듈 레벨 파일 목록 캐시 (페이지 탐색 간 유지, 새로고침 시 초기화)
const _filesCache = new Map()   // path → { files, subfolders, warning, ts }
const FILES_TTL_MS = 3 * 60 * 1000  // 3분

export const useBrowserStore = defineStore('browser', () => {
  const selectedFolder = ref(null)
  const selectedFile = ref(null)
  const files = ref([])
  const extraFiles = ref([])   // [{ filename, path, file_type, file_size, modified_time }, ...]
  const albumDescription = ref(null)
  const subfolders = ref([])   // [{ name, path, has_children, has_audio }, ...]
  const loading = ref(false)
  const error = ref(null)
  const fileWarning = ref(null)
  const checkedPaths = ref(new Set())
  const breadcrumb = ref([])   // [{ name, path }, ...]

  // 정렬/필터 상태
  const sortKey = ref('filename')   // 'track_no' | 'filename' | 'artist' | 'album_title'
  const sortOrder = ref('asc')       // 'asc' | 'desc'
  const filterText = ref('')

  const checkedFiles = computed(() =>
    files.value.filter(f => checkedPaths.value.has(f.path))
  )
  const isAllChecked = computed(() =>
    files.value.length > 0 && files.value.every(f => checkedPaths.value.has(f.path))
  )

  // 필터링 + 정렬된 파일 목록
  const displayFiles = computed(() => {
    let list = files.value

    // 텍스트 필터
    const q = filterText.value.trim().toLowerCase()
    if (q) {
      list = list.filter(f =>
        (f.title || f.filename || '').toLowerCase().includes(q) ||
        (f.artist || '').toLowerCase().includes(q) ||
        (f.album_title || '').toLowerCase().includes(q)
      )
    }

    // 정렬
    const key = sortKey.value
    const dir = sortOrder.value === 'asc' ? 1 : -1
    list = [...list].sort((a, b) => {
      if (key === 'track_no') {
        return ((a.track_no ?? 9999) - (b.track_no ?? 9999)) * dir
      }
      const av = (a[key] || '').toLowerCase()
      const bv = (b[key] || '').toLowerCase()
      return av < bv ? -dir : av > bv ? dir : 0
    })

    return list
  })

  async function loadFiles(path, force = false) {
    // 캐시 확인
    if (!force) {
      const entry = _filesCache.get(path)
      if (entry && Date.now() - entry.ts < FILES_TTL_MS) {
        files.value = entry.files
        extraFiles.value = entry.extraFiles ?? []
        albumDescription.value = entry.albumDescription ?? null
        subfolders.value = entry.subfolders
        fileWarning.value = entry.warning
        selectedFile.value = null
        return
      }
    }

    loading.value = true
    error.value = null
    fileWarning.value = null
    checkedPaths.value = new Set()
    try {
      const [filesRes, childrenRes] = await Promise.all([
        browseApi.getFiles(path, force),
        browseApi.getChildren(path).catch(() => ({ data: [] })),
      ])
      const fileList  = Array.isArray(filesRes.data) ? filesRes.data : (filesRes.data.files ?? [])
      const extraList = filesRes.data.extra_files ?? []
      const warning   = filesRes.data.warning ?? null
      const subs      = Array.isArray(childrenRes.data) ? childrenRes.data : []
      const desc      = filesRes.data.album_description ?? null

      files.value = fileList
      extraFiles.value = extraList
      albumDescription.value = desc
      fileWarning.value = warning
      subfolders.value = subs
      selectedFile.value = null

      // 캐시 저장 (오류 없을 때만)
      if (!warning) {
        _filesCache.set(path, { files: fileList, extraFiles: extraList, albumDescription: desc, subfolders: subs, warning, ts: Date.now() })
      }
    } catch (e) {
      error.value = e.response?.data?.detail || '파일 목록을 불러올 수 없습니다.'
      files.value = []
      subfolders.value = []
    } finally {
      loading.value = false
    }
  }

  function invalidateFilesCache(path) {
    if (path) {
      _filesCache.delete(path)
    } else {
      _filesCache.clear()
    }
  }

  function selectFolder(folder, crumb = null) {
    selectedFolder.value = folder
    selectedFile.value = null
    checkedPaths.value = new Set()
    filterText.value = ''
    subfolders.value = []
    extraFiles.value = []
    albumDescription.value = null
    if (folder) {
      // crumb이 명시적으로 전달되면 사용, 없으면 현재 breadcrumb에 추가
      if (crumb !== null) {
        breadcrumb.value = crumb
      } else {
        // 이미 breadcrumb에 있으면 그 위치로 절단, 없으면 추가
        const idx = breadcrumb.value.findIndex(b => b.path === folder.path)
        if (idx !== -1) {
          breadcrumb.value = breadcrumb.value.slice(0, idx + 1)
        } else {
          breadcrumb.value = [...breadcrumb.value, { name: folder.name, path: folder.path }]
        }
      }
      loadFiles(folder.path)
    } else {
      files.value = []
      breadcrumb.value = []
    }
  }

  function selectFile(file) {
    selectedFile.value = file
  }

  function toggleCheck(file) {
    const next = new Set(checkedPaths.value)
    if (next.has(file.path)) {
      next.delete(file.path)
    } else {
      next.add(file.path)
    }
    checkedPaths.value = next
  }

  function setCheckedPaths(set) {
    checkedPaths.value = set
  }

  function toggleAll() {
    // displayFiles 기준으로 전체 선택/해제
    const visible = displayFiles.value.map(f => f.path)
    const allChecked = visible.length > 0 && visible.every(p => checkedPaths.value.has(p))
    const next = new Set(checkedPaths.value)
    if (allChecked) {
      visible.forEach(p => next.delete(p))
    } else {
      visible.forEach(p => next.add(p))
    }
    checkedPaths.value = next
  }

  function updateFile(updated) {
    const idx = files.value.findIndex(f => f.path === updated.path)
    if (idx !== -1) {
      files.value[idx] = { ...files.value[idx], ...updated }
      if (selectedFile.value?.path === updated.path) {
        selectedFile.value = files.value[idx]
      }
    }
  }

  function updateFiles(paths, updates) {
    for (const path of paths) {
      const idx = files.value.findIndex(f => f.path === path)
      if (idx !== -1) {
        files.value[idx] = { ...files.value[idx], ...updates }
      }
    }
  }

  return {
    selectedFolder, selectedFile, files, extraFiles, albumDescription, subfolders, displayFiles,
    loading, error, fileWarning,
    checkedPaths, checkedFiles, isAllChecked,
    sortKey, sortOrder, filterText, breadcrumb,
    loadFiles, selectFolder, selectFile, toggleCheck, toggleAll, setCheckedPaths,
    updateFile, updateFiles, invalidateFilesCache,
  }
})
