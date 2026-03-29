import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

// 모듈 레벨 파일 목록 캐시 (페이지 탐색 간 유지, 새로고침 시 초기화)
const _filesCache = new Map()   // path → { files, subfolders, warning, ts }
const FILES_TTL_MS = 3 * 60 * 1000  // 3분

// 백그라운드 스캔 완료 대기 타이머 (모듈 레벨 — store 인스턴스 외부)
let _scanPollTimer = null
let _scanRetryCount = 0

export const useBrowserStore = defineStore('browser', () => {
  const selectedFolder = ref(null)
  const selectedFile = ref(null)
  const currentArea = ref(null)  // 'workspace' | 'library' | null
  const mobileMenuOpen = ref(false)  // 모바일 액션 바텀시트 열림 상태
  const isRecursiveMode = ref(false)  // 하위폴더 전체 보기 모드
  const folderGroups = ref([])         // [{ folder_path, folder_name, relative_path, files }]
  const files = ref([])
  const extraFiles = ref([])   // [{ filename, path, file_type, file_size, modified_time, is_eztag? }, ...]
  const albumDescription = ref(null)
  const hasEztagReport = ref(false)  // 폴더에 eztag 생성 HTML 파일 존재 여부
  const subfolders = ref([])   // [{ name, path, has_children, has_audio }, ...]
  const loading = ref(false)
  const error = ref(null)
  const fileWarning = ref(null)
  const checkedPaths = ref(new Set())
  const breadcrumb = ref([])   // [{ name, path }, ...]

  // 정렬/필터 상태
  const sortKey = ref('track_no')   // 정렬 기준 필드명
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
    const NUMERIC = new Set(['disc_no', 'track_no', 'year', 'bitrate', 'sample_rate', 'duration', 'modified_time', 'file_size'])
    list = [...list].sort((a, b) => {
      if (NUMERIC.has(key)) {
        const av = a[key] ?? (dir > 0 ? Infinity : -Infinity)
        const bv = b[key] ?? (dir > 0 ? Infinity : -Infinity)
        return (av - bv) * dir
      }
      if (key === 'title') {
        const av = (a.title || a.filename || '').toLowerCase()
        const bv = (b.title || b.filename || '').toLowerCase()
        return av < bv ? -dir : av > bv ? dir : 0
      }
      const av = (a[key] || '').toLowerCase()
      const bv = (b[key] || '').toLowerCase()
      return av < bv ? -dir : av > bv ? dir : 0
    })

    return list
  })

  async function loadFiles(path, force = false) {
    // 새 폴더 요청이면 재시도 카운터 초기화
    if (selectedFolder.value?.path !== path) {
      _scanRetryCount = 0
    }
    // 캐시 확인
    if (!force) {
      const entry = _filesCache.get(path)
      if (entry && Date.now() - entry.ts < FILES_TTL_MS) {
        files.value = entry.files
        extraFiles.value = entry.extraFiles ?? []
        albumDescription.value = entry.albumDescription ?? null
        hasEztagReport.value = entry.hasEztagReport ?? false
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
        browseApi.getChildren(path, force).catch(() => ({ data: [] })),
      ])
      const fileList  = Array.isArray(filesRes.data) ? filesRes.data : (filesRes.data.files ?? [])
      const extraList = filesRes.data.extra_files ?? []
      const warning   = filesRes.data.warning ?? null
      const subs      = Array.isArray(childrenRes.data) ? childrenRes.data : []
      const desc      = filesRes.data.album_description ?? null
      const hasEztag  = filesRes.data.has_eztag_report ?? false

      files.value = fileList
      extraFiles.value = extraList
      albumDescription.value = desc
      hasEztagReport.value = hasEztag
      fileWarning.value = warning
      subfolders.value = subs
      selectedFile.value = null

      if (_scanPollTimer) {
        clearTimeout(_scanPollTimer)
        _scanPollTimer = null
      }

      const hasUnscanned = fileList.some(f => f.scanned === false)
      if (hasUnscanned && _scanRetryCount < 4) {
        // 아직 스캔 미완료: 로딩 상태 유지하며 1초 후 재조회 (최대 4회 = 4초)
        _scanRetryCount++
        _scanPollTimer = setTimeout(() => {
          _scanPollTimer = null
          if (selectedFolder.value?.path === path) {
            loadFiles(path, true)
          }
        }, 1000)
        return  // loading=true 유지, 파일 목록 미표시
      }

      // 스캔 완료(또는 최대 재시도 초과) — 한 번에 표시
      _scanRetryCount = 0

      // 캐시 저장 (오류 없을 때만)
      if (!warning) {
        _filesCache.set(path, { files: fileList, extraFiles: extraList, albumDescription: desc, hasEztagReport: hasEztag, subfolders: subs, warning, ts: Date.now() })
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

  async function loadRecursiveFiles(path) {
    loading.value = true
    error.value = null
    fileWarning.value = null
    checkedPaths.value = new Set()
    files.value = []
    subfolders.value = []
    extraFiles.value = []
    folderGroups.value = []
    try {
      const { data } = await browseApi.recursiveFiles(path)
      folderGroups.value = data.groups
      // 기존 함수 호환용 flat 목록
      files.value = data.groups.flatMap(g => g.files)
      isRecursiveMode.value = true
      selectedFile.value = null
    } catch (e) {
      error.value = e.response?.data?.detail || '파일 목록을 불러올 수 없습니다.'
      files.value = []
      folderGroups.value = []
    } finally {
      loading.value = false
    }
  }

  function selectFolderRecursive(folder, crumb = null, area = null) {
    if (_scanPollTimer) { clearTimeout(_scanPollTimer); _scanPollTimer = null }
    _scanRetryCount = 0
    selectedFolder.value = folder
    selectedFile.value = null
    selectedExtraFile.value = null
    if (area) currentArea.value = area
    checkedPaths.value = new Set()
    filterText.value = ''
    subfolders.value = []
    extraFiles.value = []
    albumDescription.value = null
    hasEztagReport.value = false
    isRecursiveMode.value = false
    folderGroups.value = []
    if (crumb !== null) {
      breadcrumb.value = crumb
    } else {
      breadcrumb.value = [{ name: folder.name, path: folder.path }]
    }
    _filesCache.delete(folder.path)
    loadRecursiveFiles(folder.path)
  }

  function selectFolder(folder, crumb = null, area = null) {
    // 폴더 변경 시 이전 폴더의 스캔 완료 대기 타이머 취소, 재시도 카운터 초기화
    if (_scanPollTimer) {
      clearTimeout(_scanPollTimer)
      _scanPollTimer = null
    }
    _scanRetryCount = 0
    selectedFolder.value = folder
    selectedFile.value = null
    selectedExtraFile.value = null
    if (area) currentArea.value = area
    checkedPaths.value = new Set()
    filterText.value = ''
    subfolders.value = []
    extraFiles.value = []
    albumDescription.value = null
    hasEztagReport.value = false
    isRecursiveMode.value = false
    folderGroups.value = []
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
      // 명시적 폴더 선택 시 캐시 무효화 → 외부 변경사항 즉시 반영
      _filesCache.delete(folder.path)
      loadFiles(folder.path)
    } else {
      files.value = []
      breadcrumb.value = []
    }
  }

  const selectedExtraFile = ref(null)

  function selectFile(file) {
    selectedFile.value = file
    selectedExtraFile.value = null
  }

  function selectExtraFile(file) {
    selectedExtraFile.value = file
    selectedFile.value = null
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
    selectedFolder, selectedFile, selectedExtraFile, files, extraFiles, albumDescription, hasEztagReport, subfolders, displayFiles,
    loading, error, fileWarning,
    checkedPaths, checkedFiles, isAllChecked,
    sortKey, sortOrder, filterText, breadcrumb, currentArea, mobileMenuOpen,
    isRecursiveMode, folderGroups,
    loadFiles, selectFolder, selectFolderRecursive, loadRecursiveFiles,
    selectFile, selectExtraFile, toggleCheck, toggleAll, setCheckedPaths,
    updateFile, updateFiles, invalidateFilesCache,
  }
})
