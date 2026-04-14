import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { browseApi } from '../api/index.js'

// 루프에서 사용할 파일 배열 (Vue 반응성 오버헤드 방지)
let _lrcFiles = null
let _youtubeFiles = null

export const useJobStore = defineStore('job', () => {
  const lrcJob = ref(null)
  const youtubeJob = ref(null)

  const hasRunning = computed(() => !!(lrcJob.value?.running || youtubeJob.value?.running))

  // ── LRC 백그라운드 작업 ──────────────────────────────────────
  async function startLrcJob({ files, source, apiMode, routePath, routeLabel, folderPath, sourceLabel }) {
    if (lrcJob.value?.running) return

    _lrcFiles = files
    lrcJob.value = {
      running: true, done: false,
      source, apiMode, routePath, routeLabel, folderPath,
      sourceLabel: sourceLabel || source,
      current: 0, total: files.length,
      ok: 0, notFound: 0, noSync: 0, errors: 0,
      currentFile: '',
      lastOkPath: null,
      okPaths: [],
    }

    try {
      for (let i = 0; i < _lrcFiles.length; i++) {
        if (!lrcJob.value) break
        const f = _lrcFiles[i]
        lrcJob.value.current = i + 1

        let displayName, data
        if (apiMode === 'library') {
          const p = typeof f === 'string' ? f : f.path
          displayName = p.split('/').pop()
          lrcJob.value.currentFile = displayName
          const res = await browseApi.libraryFetchLyrics([p], source)
          data = res.data
        } else {
          displayName = f.filename || f.path.split('/').pop()
          lrcJob.value.currentFile = displayName
          const res = await browseApi.fetchLyrics(
            [{ path: f.path, title: f.title || '', artist: f.artist || f.album_artist || '', album: f.album_title || '' }],
            source
          )
          data = res.data
        }

        const r = (data.results || [])[0]
        if (r?.status === 'ok') {
          const filePath = typeof f === 'string' ? f : f.path
          lrcJob.value.ok++
          lrcJob.value.lastOkPath = filePath
          lrcJob.value.okPaths = [...lrcJob.value.okPaths, filePath]
        } else if (!r) {
          // 결과 없음 — 오류로 처리
          lrcJob.value.errors++
        } else if (r.status === 'not_found') {
          lrcJob.value.notFound++
        } else if (r.status === 'no_sync') {
          lrcJob.value.noSync++
        } else {
          lrcJob.value.errors++
        }
      }
    } catch {
      // 루프 레벨 오류는 무시
    } finally {
      if (lrcJob.value) {
        lrcJob.value.running = false
        lrcJob.value.done = true
        lrcJob.value.currentFile = ''
      }
      _lrcFiles = null
    }
  }

  function cancelLrcJob() { lrcJob.value = null; _lrcFiles = null }
  function clearLrcJob() { if (!lrcJob.value?.running) lrcJob.value = null }

  // ── YouTube 백그라운드 작업 ──────────────────────────────────
  async function startYoutubeJob({ files, routePath, routeLabel, folderPath }) {
    if (youtubeJob.value?.running) return

    _youtubeFiles = files
    youtubeJob.value = {
      running: true, done: false,
      routePath, routeLabel, folderPath,
      current: 0, total: files.length,
      found: 0, currentFile: '',
      lastFoundResult: null,
      notConfigured: false,
      results: [],
    }

    try {
      for (let i = 0; i < _youtubeFiles.length; i++) {
        if (!youtubeJob.value) break
        const f = _youtubeFiles[i]
        youtubeJob.value.currentFile = f.title || f.filename || f.path?.split('/')?.pop() || ''

        try {
          const { data } = await browseApi.searchYoutubeMV(f.artist || '', f.title || f.filename || '')
          const results = Array.isArray(data) ? data : (data.results || [])
          if (results.length > 0) {
            const url = results[0].url
            await browseApi.setTrackInfo({ path: f.path, youtube_url: url, is_title_track: !!f.is_title_track })
            youtubeJob.value.found++
            youtubeJob.value.lastFoundResult = { path: f.path, url, is_title_track: !!f.is_title_track }
            youtubeJob.value.results.push({ path: f.path, title: f.title || f.filename, url, found: true })
          } else {
            youtubeJob.value.results.push({ path: f.path, title: f.title || f.filename, url: null, found: false })
          }
        } catch (e) {
          if (e.response?.data?.detail === 'youtube_not_configured') {
            youtubeJob.value.running = false
            youtubeJob.value.done = true
            youtubeJob.value.notConfigured = true
            return
          }
          youtubeJob.value.results.push({ path: f.path, title: f.title || f.filename, url: null, found: false })
        } finally {
          if (youtubeJob.value && !youtubeJob.value.notConfigured) {
            youtubeJob.value.current++
          }
        }
      }
    } catch {
      // 루프 레벨 오류는 무시
    } finally {
      if (youtubeJob.value && !youtubeJob.value.notConfigured) {
        youtubeJob.value.running = false
        youtubeJob.value.done = true
        youtubeJob.value.currentFile = ''
      }
      _youtubeFiles = null
    }
  }

  function cancelYoutubeJob() { youtubeJob.value = null; _youtubeFiles = null }
  function clearYoutubeJob() { if (!youtubeJob.value?.running) youtubeJob.value = null }

  return {
    lrcJob, youtubeJob, hasRunning,
    startLrcJob, cancelLrcJob, clearLrcJob,
    startYoutubeJob, cancelYoutubeJob, clearYoutubeJob,
  }
})
