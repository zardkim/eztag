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
  const wizardOpen = ref(false)      // 마법사 다이얼로그 열림 상태
  const wizardPendingPreset = ref(null)  // 모바일 하단바에서 선택한 프리셋 (null=설정모드, object=즉시실행)
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
  const sortKey = ref('disc_no')     // 정렬 기준 필드명
  const sortOrder = ref('asc')       // 'asc' | 'desc'
  const filterText = ref('')

  const checkedFiles = computed(() =>
    files.value.filter(f => checkedPaths.value.has(f.path))
  )
  const isAllChecked = computed(() =>
    files.value.length > 0 && files.value.every(f => checkedPaths.value.has(f.path))
  )

  // 파일 정렬 비교함수 생성
  function _makeSorter(key, dir) {
    const NUMERIC = new Set(['disc_no', 'track_no', 'year', 'bitrate', 'sample_rate', 'duration', 'modified_time', 'file_size'])
    return (a, b) => {
      let cmp = 0
      if (NUMERIC.has(key)) {
        const av = a[key] ?? (dir > 0 ? Infinity : -Infinity)
        const bv = b[key] ?? (dir > 0 ? Infinity : -Infinity)
        cmp = (av - bv) * dir
        if (isNaN(cmp)) cmp = 0  // 둘 다 null이면 Infinity-Infinity=NaN → 0으로 정규화해 보조 정렬 적용
      } else if (key === 'title') {
        const av = (a.title || a.filename || '').toLowerCase()
        const bv = (b.title || b.filename || '').toLowerCase()
        cmp = av < bv ? -dir : av > bv ? dir : 0
      } else {
        const av = (a[key] || '').toLowerCase()
        const bv = (b[key] || '').toLowerCase()
        cmp = av < bv ? -dir : av > bv ? dir : 0
      }
      if (cmp === 0 && key === 'disc_no') {
        const at = a.track_no ?? Infinity
        const bt = b.track_no ?? Infinity
        return at - bt
      }
      if (cmp === 0 && key === 'track_no') {
        const ad = a.disc_no ?? Infinity
        const bd = b.disc_no ?? Infinity
        return (ad - bd) * dir
      }
      return cmp
    }
  }

  // 필터링 + 정렬된 파일 목록
  const displayFiles = computed(() => {
    let list = files.value

    const q = filterText.value.trim().toLowerCase()
    if (q) {
      list = list.filter(f =>
        (f.title || f.filename || '').toLowerCase().includes(q) ||
        (f.artist || '').toLowerCase().includes(q) ||
        (f.album_title || '').toLowerCase().includes(q)
      )
    }

    const dir = sortOrder.value === 'asc' ? 1 : -1
    return [...list].sort(_makeSorter(sortKey.value, dir))
  })

  // 폴더 그룹별 필터링 + 정렬 (하위폴더 포함 로드 시)
  const displayGroups = computed(() => {
    if (!folderGroups.value.length) return []
    const q = filterText.value.trim().toLowerCase()
    const dir = sortOrder.value === 'asc' ? 1 : -1
    const sorter = _makeSorter(sortKey.value, dir)
    return folderGroups.value.map(g => {
      let gfiles = q
        ? g.files.filter(f =>
            (f.title || f.filename || '').toLowerCase().includes(q) ||
            (f.artist || '').toLowerCase().includes(q) ||
            (f.album_title || '').toLowerCase().includes(q)
          )
        : [...g.files]
      return { ...g, files: gfiles.sort(sorter) }
    }).filter(g => g.files.length > 0)
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
        // 파일 목록 즉시 표시 후, 백그라운드에서 스캔 완료 대기
        _scanRetryCount++
        _scanPollTimer = setTimeout(() => {
          _scanPollTimer = null
          if (selectedFolder.value?.path === path) {
            _pollRefreshFiles(path)
          }
        }, 1500)
      } else {
        _scanRetryCount = 0
      }

      // 직접 오디오 파일이 없고 오디오가 있는 하위 폴더가 있으면 자동으로 재귀 로드
      if (fileList.length === 0 && subs.some(s => s.has_audio)) {
        loadRecursiveFiles(path)
        return
      }

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

  async function _pollRefreshFiles(path) {
    try {
      const [filesRes, childrenRes] = await Promise.all([
        browseApi.getFiles(path, true),
        browseApi.getChildren(path, true).catch(() => ({ data: [] })),
      ])
      if (selectedFolder.value?.path !== path) return
      const fileList  = Array.isArray(filesRes.data) ? filesRes.data : (filesRes.data.files ?? [])
      const extraList = filesRes.data.extra_files ?? []
      const warning   = filesRes.data.warning ?? null
      const subs      = Array.isArray(childrenRes.data) ? childrenRes.data : []
      files.value = fileList
      extraFiles.value = extraList
      fileWarning.value = warning
      subfolders.value = subs
      const hasUnscanned = fileList.some(f => f.scanned === false)
      if (hasUnscanned && _scanRetryCount < 4) {
        _scanRetryCount++
        _scanPollTimer = setTimeout(() => {
          if (selectedFolder.value?.path === path) _pollRefreshFiles(path)
        }, 1500)
      } else {
        _scanRetryCount = 0
        if (!warning) {
          _filesCache.set(path, { files: fileList, extraFiles: extraList, albumDescription: albumDescription.value, hasEztagReport: hasEztagReport.value, subfolders: subs, warning, ts: Date.now() })
        }
      }
    } catch (_) { /* 사일런트 실패 */ }
  }

  function invalidateFilesCache(path) {
    if (path) {
      _filesCache.delete(path)
    } else {
      _filesCache.clear()
    }
  }

  async function loadRecursiveFiles(path, isRetry = false) {
    loading.value = true
    error.value = null
    fileWarning.value = null
    if (!isRetry) {
      checkedPaths.value = new Set()
      files.value = []
      subfolders.value = []
      extraFiles.value = []
      folderGroups.value = []
    }
    try {
      const { data } = await browseApi.recursiveFiles(path)
      folderGroups.value = data.groups
      const fileList = data.groups.flatMap(g => g.files)
      files.value = fileList
      extraFiles.value = data.extra_files ?? []
      isRecursiveMode.value = true
      if (!isRetry) selectedFile.value = null

      // 미스캔 파일이 있으면 즉시 표시 후 백그라운드에서 갱신 (최대 4회)
      const hasUnscanned = fileList.some(f => f.scanned === false)
      if (hasUnscanned && _scanRetryCount < 4) {
        _scanRetryCount++
        if (_scanPollTimer) clearTimeout(_scanPollTimer)
        _scanPollTimer = setTimeout(() => {
          _scanPollTimer = null
          if (selectedFolder.value?.path === path && isRecursiveMode.value) {
            loadRecursiveFiles(path, true)
          }
        }, 1500)
      } else {
        _scanRetryCount = 0
      }
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

  function _patchInGroups(path, updates) {
    for (const g of folderGroups.value) {
      const idx = g.files.findIndex(f => f.path === path)
      if (idx !== -1) {
        g.files[idx] = { ...g.files[idx], ...updates }
        break
      }
    }
  }

  function updateFile(updated) {
    const idx = files.value.findIndex(f => f.path === updated.path)
    if (idx !== -1) {
      files.value[idx] = { ...files.value[idx], ...updated }
      if (selectedFile.value?.path === updated.path) {
        selectedFile.value = files.value[idx]
      }
    }
    _patchInGroups(updated.path, updated)
  }

  function updateFiles(paths, updates) {
    for (const path of paths) {
      const idx = files.value.findIndex(f => f.path === path)
      if (idx !== -1) {
        files.value[idx] = { ...files.value[idx], ...updates }
      }
      _patchInGroups(path, updates)
    }
  }

  return {
    selectedFolder, selectedFile, selectedExtraFile, files, extraFiles, albumDescription, hasEztagReport, subfolders, displayFiles, displayGroups,
    loading, error, fileWarning,
    checkedPaths, checkedFiles, isAllChecked,
    sortKey, sortOrder, filterText, breadcrumb, currentArea, mobileMenuOpen, wizardOpen, wizardPendingPreset,
    isRecursiveMode, folderGroups,
    loadFiles, selectFolder, selectFolderRecursive, loadRecursiveFiles,
    selectFile, selectExtraFile, toggleCheck, toggleAll, setCheckedPaths,
    updateFile, updateFiles, invalidateFilesCache,
  }
})
