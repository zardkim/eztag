import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

// 모듈 레벨 파일 목록 캐시 (페이지 탐색 간 유지, 새로고침 시 초기화)
const _filesCache = new Map()   // path → { files, subfolders, warning, ts }
const FILES_TTL_MS = 3 * 60 * 1000  // 3분

// 직접 오디오 파일이 없는 폴더를 열었을 때 자동으로 하위 전체를 읽을지 판단하는 한계값.
// 원래 의도는 "Disc 1 / Disc 2" 처럼 앨범이 디스크별로 쪼개진 경우였는데(v0.8.25),
// 제한이 없어서 아티스트 폴더(앨범 수십 개)를 눌러도 전곡을 재귀로 읽어버렸다.
// 오디오를 가진 하위 폴더가 이보다 많으면 재귀하지 않고 하위 폴더 그리드를 보여준다.
const AUTO_RECURSE_MAX_SUBFOLDERS = 5

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
  const subfolders = ref([])   // [{ name, path }, ...] (meta=true 일 때만 has_children/has_audio/modified_time 포함)
  // 하위 폴더 목록 정렬 — 'name' | 'modified_time'
  const folderSortKey = ref(localStorage.getItem('eztag-folder-sort-key') || 'name')
  const folderSortOrder = ref(localStorage.getItem('eztag-folder-sort-order') || 'asc')
  const subfolderMetaLoading = ref(false)
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

  // 하위 폴더 정렬. 수정일은 meta=true 로 받아야 있으므로, 값이 없으면 이름순으로 폴백한다.
  const sortedSubfolders = computed(() => {
    const dir = folderSortOrder.value === 'desc' ? -1 : 1
    const list = [...subfolders.value]
    if (folderSortKey.value === 'modified_time') {
      return list.sort((a, b) => {
        const av = a.modified_time ?? null
        const bv = b.modified_time ?? null
        if (av === null && bv === null) return a.name.localeCompare(b.name, 'ko') * dir
        if (av === null) return 1      // 값 없는 항목은 항상 뒤로
        if (bv === null) return -1
        return (av - bv) * dir
      })
    }
    return list.sort((a, b) => a.name.localeCompare(b.name, 'ko', { numeric: true }) * dir)
  })

  /**
   * 하위 폴더의 수정일을 채운다 (meta=true 재요청).
   * 자식 수만큼 추가 syscall 이 발생하므로, 사용자가 수정일 정렬을 고를 때만 부른다.
   */
  async function loadSubfolderMeta() {
    const path = selectedFolder.value?.path
    if (!path || subfolders.value.length === 0) return
    if (subfolders.value.some(f => f.modified_time !== undefined)) return  // 이미 받아둠
    subfolderMetaLoading.value = true
    try {
      const { data } = await browseApi.getChildren(path, false, true)
      const byPath = new Map((data || []).map(d => [d.path, d]))
      subfolders.value = subfolders.value.map(f => ({ ...f, ...(byPath.get(f.path) || {}) }))
    } catch {
      // 실패해도 이름순 폴백으로 계속 동작한다
    } finally {
      subfolderMetaLoading.value = false
    }
  }

  function setFolderSort(key) {
    if (folderSortKey.value === key) {
      folderSortOrder.value = folderSortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      folderSortKey.value = key
      folderSortOrder.value = 'asc'
    }
    try {
      localStorage.setItem('eztag-folder-sort-key', folderSortKey.value)
      localStorage.setItem('eztag-folder-sort-order', folderSortOrder.value)
    } catch {}
    if (key === 'modified_time') loadSubfolderMeta()
  }

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

      // 직접 오디오 파일이 없고 오디오가 있는 하위 폴더가 "몇 개뿐"이면 자동으로 재귀 로드.
      // 많으면(아티스트 폴더 등) 재귀하지 않고 하위 폴더 그리드를 보여준다 —
      // 사용자는 그리드에서 들어가거나 "하위 폴더 전체 보기"로 직접 재귀할 수 있다.
      // has_audio 는 더 이상 기본 응답에 없다(N+1 제거) — 하위 폴더 개수로 판정한다.
      // Disc 1/Disc 2 는 2개, 아티스트 폴더는 수십 개라 실질적으로 동일하게 갈린다.
      if (fileList.length === 0 && subs.length > 0 && subs.length <= AUTO_RECURSE_MAX_SUBFOLDERS) {
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

  function resetFolder() {
    // 선택 폴더 초기화 — 태깅 버튼 진입 시 이전 startup 폴더 제거용
    if (_scanPollTimer) { clearTimeout(_scanPollTimer); _scanPollTimer = null }
    _scanRetryCount = 0
    selectedFolder.value = null
    selectedFile.value = null
    selectedExtraFile.value = null
    files.value = []
    subfolders.value = []
    extraFiles.value = []
    breadcrumb.value = []
    checkedPaths.value = new Set()
    filterText.value = ''
    folderGroups.value = []
    isRecursiveMode.value = false
    albumDescription.value = null
    hasEztagReport.value = false
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
    folderSortKey, folderSortOrder, sortedSubfolders, subfolderMetaLoading,
    setFolderSort, loadSubfolderMeta,
    loadFiles, selectFolder, selectFolderRecursive, loadRecursiveFiles,
    selectFile, selectExtraFile, toggleCheck, toggleAll, setCheckedPaths,
    updateFile, updateFiles, invalidateFilesCache, resetFolder,
  }
})
