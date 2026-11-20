import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

// 모듈 레벨 파일 목록 캐시 (페이지 탐색 간 유지, 새로고침 시 초기화)
const _filesCache = new Map()   // path → { files, subfolders, warning, ts }
const FILES_TTL_MS = 3 * 60 * 1000  // 3분

// 디스크로 쪼개진 앨범 판정 — "Disc 1 / Disc 2", "CD1 / CD2", "디스크1" 등.
// 이런 폴더는 앨범 하나가 디스크별로 나뉜 것이므로 한 번에 보여주는 쪽이 맞다.
// Vol.N / Part N 은 별개 앨범인 경우가 많아 일부러 제외한다.
const DISC_FOLDER_RE = /^(disc|disk|cd|디스크)\s*[.\-_]?\s*\d{1,2}(\s*[-–—]\s*.+)?$/i

/** 하위 폴더가 "전부" 디스크 폴더이고 2개 이상일 때만 참. 하나라도 아니면 거짓 —
 *  'CD1 / Bonus / Scans' 같은 구성까지 합쳐버리면 안 된다. */
function isDiscSplitAlbum(subs) {
  if (!Array.isArray(subs) || subs.length < 2) return false
  return subs.every(f => DISC_FOLDER_RE.test(String(f?.name ?? '').trim()))
}

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
  // 사용자가 "이 폴더만 보기"를 누른 경우, 같은 폴더에서 다시 자동 합치기를 하지 않는다.
  // 폴더를 옮기면 해제된다.
  const suppressAutoCombine = ref(false)
  // 사이드바 폴더 트리 새로고침 신호. 폴더 이름/구조가 바뀌면 올린다 —
  // 트리는 App.vue 에 있고 변경은 Browser 쪽 패널에서 일어나서 직접 부를 수 없다.
  const treeRefreshSignal = ref(0)
  function requestTreeRefresh() { treeRefreshSignal.value++ }
  const folderGroups = ref([])         // [{ folder_path, folder_name, relative_path, files }]
  const files = ref([])
  const extraFiles = ref([])   // [{ filename, path, file_type, file_size, modified_time, is_eztag? }, ...]
  const albumDescription = ref(null)
  const hasEztagReport = ref(false)  // 폴더에 eztag 생성 HTML 파일 존재 여부
  const subfolders = ref([])   // [{ name, path }, ...] (meta=true 일 때만 has_children/has_audio/modified_time 포함)
  // 하위 폴더 목록 정렬 — 'name' | 'modified_time'
  // 하위 폴더 목록 검색어 (폴더를 옮기면 비운다)
  const folderFilterText = ref('')
  // 브레드크럼으로 상위 폴더에 올라갔을 때, 방금 내려왔던 하위 폴더를 표시해 준다.
  // (폴더가 많으면 어디에 있다 왔는지 찾기 어렵다)
  const highlightFolderPath = ref(null)
  const folderSortKey = ref(localStorage.getItem('eztag-folder-sort-key') || 'name')
  const folderSortOrder = ref(localStorage.getItem('eztag-folder-sort-order') || 'asc')
  const subfolderMetaLoading = ref(false)
  const loading = ref(false)
  const error = ref(null)
  const fileWarning = ref(null)
  const checkedPaths = ref(new Set())
  const breadcrumb = ref([])   // [{ name, path }, ...]

  // 정렬/필터 상태 — 정렬 기준은 폴더 정렬과 같이 localStorage 에 유지한다
  const sortKey = ref(localStorage.getItem('eztag-file-sort-key') || 'disc_no')   // 정렬 기준 필드명
  const sortOrder = ref(localStorage.getItem('eztag-file-sort-order') || 'asc')   // 'asc' | 'desc'

  // 파일 목록 정렬 기준 변경 — 같은 키를 다시 고르면 오름/내림을 토글한다
  function setSort(key) {
    if (sortKey.value === key) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKey.value = key
      sortOrder.value = 'asc'
    }
    try {
      localStorage.setItem('eztag-file-sort-key', sortKey.value)
      localStorage.setItem('eztag-file-sort-order', sortOrder.value)
    } catch {}
  }

  // 기준만 변경하고 방향은 유지한다 (정렬 바의 select 용 —
  // 방향 토글이 바로 옆에 있어서 임의로 오름차순으로 되돌리면 오작동처럼 보인다)
  function setSortKey(key) {
    sortKey.value = key
    try {
      localStorage.setItem('eztag-file-sort-key', sortKey.value)
    } catch {}
  }

  function setSortOrder(order) {
    sortOrder.value = order === 'desc' ? 'desc' : 'asc'
    try {
      localStorage.setItem('eztag-file-sort-order', sortOrder.value)
    } catch {}
  }

  const checkedFiles = computed(() =>
    files.value.filter(f => checkedPaths.value.has(f.path))
  )
  const isAllChecked = computed(() =>
    files.value.length > 0 && files.value.every(f => checkedPaths.value.has(f.path))
  )

  // 하위 폴더 정렬. 수정일은 meta=true 로 받아야 있으므로, 값이 없으면 이름순으로 폴백한다.
  const sortedSubfolders = computed(() => {
    const dir = folderSortOrder.value === 'desc' ? -1 : 1
    const q = folderFilterText.value.trim().toLowerCase()
    const list = q
      ? subfolders.value.filter(f => (f.name || '').toLowerCase().includes(q))
      : [...subfolders.value]
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

  // 문자열 비교 — 하위 폴더 정렬과 동일하게 로케일/숫자 인식으로 비교한다.
  // 단순 `<` 비교는 '10 - foo.mp3' 가 '2 - foo.mp3' 보다 앞에 오므로 파일명 정렬에서 특히 어긋난다.
  function _cmpText(a, b) {
    return String(a ?? '').localeCompare(String(b ?? ''), 'ko', { numeric: true, sensitivity: 'base' })
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
        cmp = _cmpText(a.title || a.filename, b.title || b.filename) * dir
      } else {
        // 태그가 비어 있는 파일(미태깅)은 오름/내림 어느 쪽에서도 뒤로 보낸다.
        // NUMERIC 분기의 Infinity 처리, sortedSubfolders 와 같은 규칙.
        const av = a[key], bv = b[key]
        const aEmpty = !String(av ?? '').trim()
        const bEmpty = !String(bv ?? '').trim()
        if (aEmpty && bEmpty) cmp = 0
        else if (aEmpty) cmp = 1
        else if (bEmpty) cmp = -1
        else cmp = _cmpText(av, bv) * dir
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
    const dir = sortOrder.value === 'asc' ? 1 : -1
    return [...files.value].sort(_makeSorter(sortKey.value, dir))
  })

  // 폴더 그룹별 필터링 + 정렬 (하위폴더 포함 로드 시)
  const displayGroups = computed(() => {
    if (!folderGroups.value.length) return []
    const dir = sortOrder.value === 'asc' ? 1 : -1
    const sorter = _makeSorter(sortKey.value, dir)
    return folderGroups.value
      .map(g => ({ ...g, files: [...g.files].sort(sorter) }))
      .filter(g => g.files.length > 0)
  })

  async function loadFiles(path, force = false) {
    // 새 폴더 요청이면 재시도 카운터 초기화
    if (selectedFolder.value?.path !== path) {
      _scanRetryCount = 0
    }
    // 이 함수는 폴더 하나의 파일만 읽는다. 재귀 상태를 남겨두면
    // displayGroups 가 예전 그룹을 계속 그려서 새 목록 위에 겹친다
    // (재귀 모드에서 새로고침/태그저장 시 발생했다).
    isRecursiveMode.value = false
    folderGroups.value = []
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

      // 디스크로 쪼개진 앨범(Disc 1/Disc 2, CD1/CD2 …)만 자동으로 합쳐서 보여준다.
      // 예전에는 "하위 폴더 5개 이하"로 판정해서 아티스트 폴더를 눌러도 전곡이
      // 쏟아졌다. 이제는 이름이 전부 디스크 패턴일 때만 합친다.
      // await 해야 한다 — 안 하면 아래 finally 가 먼저 돌아 스피너가 일찍 사라진다.
      if (!suppressAutoCombine.value && fileList.length === 0 && isDiscSplitAlbum(subs)) {
        await loadRecursiveFiles(path)
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

  /**
   * 현재 폴더를 다시 읽는다. 재귀 모드면 재귀 로드를 유지한다.
   * 호출처마다 isRecursiveMode / folderGroups.length 로 제각각 판정하던 것을 모았다.
   */
  async function reloadCurrent(path = null) {
    const target = path || selectedFolder.value?.path
    if (!target) return
    const wasRecursive = isRecursiveMode.value || folderGroups.value.length > 0
    invalidateFilesCache(target)
    if (wasRecursive) await loadRecursiveFiles(target)
    else await loadFiles(target, true)
  }

  /** "이 폴더만 보기" — 합쳐 보기를 끄고 선택한 폴더만 다시 읽는다. */
  async function exitRecursive() {
    const path = selectedFolder.value?.path
    if (!path) return
    suppressAutoCombine.value = true
    invalidateFilesCache(path)
    await loadFiles(path, true)
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
    folderFilterText.value = ''
    highlightFolderPath.value = null
    subfolders.value = []
    extraFiles.value = []
    albumDescription.value = null
    hasEztagReport.value = false
    isRecursiveMode.value = false
    folderGroups.value = []
    suppressAutoCombine.value = false
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
    folderFilterText.value = ''
    highlightFolderPath.value = null
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
    folderFilterText.value = ''
    highlightFolderPath.value = null
    subfolders.value = []
    extraFiles.value = []
    albumDescription.value = null
    hasEztagReport.value = false
    isRecursiveMode.value = false
    folderGroups.value = []
    suppressAutoCombine.value = false
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
    sortKey, sortOrder, breadcrumb, currentArea, mobileMenuOpen, wizardOpen, wizardPendingPreset,
    isRecursiveMode, folderGroups, suppressAutoCombine, treeRefreshSignal, requestTreeRefresh,
    folderSortKey, folderSortOrder, sortedSubfolders, subfolderMetaLoading, folderFilterText,
    highlightFolderPath,
    setFolderSort, loadSubfolderMeta, setSort, setSortKey, setSortOrder,
    loadFiles, selectFolder, selectFolderRecursive, loadRecursiveFiles, reloadCurrent, exitRecursive,
    selectFile, selectExtraFile, toggleCheck, toggleAll, setCheckedPaths,
    updateFile, updateFiles, invalidateFilesCache, resetFolder,
  }
})
