<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-3xl flex flex-col max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('renameModal.title') }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1">✕</button>
      </div>

      <!-- 패턴 입력 -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0 space-y-3">
        <!-- 패턴 입력 + 히스토리 콤보박스 + 프리셋 -->
        <div class="flex flex-col sm:flex-row gap-2">
          <!-- 입력란 + 히스토리 드롭다운 -->
          <div class="relative flex-1" ref="historyContainerRef">
            <input
              ref="patternInputRef"
              v-model="pattern"
              type="text"
              class="w-full px-3 py-2 pr-8 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="%track% - %title%"
              @focus="patternHistory.length > 0 && (showHistoryDropdown = true)"
            />
            <!-- 히스토리 토글 버튼 -->
            <button
              v-if="patternHistory.length > 0"
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs leading-none px-0.5"
              :class="showHistoryDropdown ? 'text-blue-500' : ''"
              @click.stop="showHistoryDropdown = !showHistoryDropdown"
              title="최근 사용한 형식"
            >▾</button>

            <!-- 히스토리 드롭다운 -->
            <div
              v-if="showHistoryDropdown && patternHistory.length > 0"
              class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 overflow-hidden"
            >
              <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('renameModal.recentPatterns') }}</span>
                <button
                  type="button"
                  class="text-[10px] text-gray-400 hover:text-red-500 transition-colors"
                  @click.stop="clearHistory"
                >{{ t('renameModal.clearHistory') }}</button>
              </div>
              <div class="max-h-48 overflow-y-auto py-1">
                <div
                  v-for="(p, i) in patternHistory"
                  :key="i"
                  class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 group transition-colors cursor-pointer"
                  @click.stop="selectHistory(p)"
                >
                  <span class="text-[10px] text-gray-400 shrink-0">🕐</span>
                  <span class="font-mono text-sm text-gray-700 dark:text-gray-300 truncate flex-1">{{ p }}</span>
                  <button
                    type="button"
                    class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 text-xs shrink-0 transition-all"
                    @click.stop="removeHistory(i)"
                    title="이 항목 삭제"
                  >✕</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 프리셋 선택 -->
          <select
            v-model="selectedPreset"
            @change="applyPreset"
            class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">{{ t('renameModal.presetPlaceholder') }}</option>
            <option v-for="p in presets" :key="p.pattern" :value="p.pattern">{{ p.label }}</option>
          </select>
        </div>

        <!-- 변수 버튼 -->
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="v in variables"
            :key="v.var"
            @click="insertVar(v.var)"
            class="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900 hover:text-blue-700 dark:hover:text-blue-300 border border-gray-200 dark:border-gray-600"
            :title="v.desc"
          >{{ v.var }}</button>
        </div>
      </div>

      <!-- 미리보기 테이블 -->
      <div class="flex-1 overflow-auto px-5 py-3">
        <div v-if="!pattern" class="text-center text-sm text-gray-400 py-8">{{ t('renameModal.patternHint') }}</div>
        <template v-else>
          <!-- 요약 -->
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-2 flex gap-3">
            <span class="text-green-600 dark:text-green-400">{{ t('renameModal.okCount', { n: okCount }) }}</span>
            <span v-if="conflictCount" class="text-yellow-600 dark:text-yellow-400">{{ t('renameModal.conflictCount', { n: conflictCount }) }}</span>
            <span v-if="skipCount" class="text-red-500">{{ t('renameModal.skipCount', { n: skipCount }) }}</span>
            <span v-if="sameCount" class="text-gray-400">{{ t('renameModal.sameCount', { n: sameCount }) }}</span>
          </div>

          <table class="w-full text-xs border-collapse">
            <thead>
              <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                <th class="text-left py-1.5 pr-3 font-medium w-[45%]">{{ t('renameModal.colOldName') }}</th>
                <th class="text-left py-1.5 pr-3 font-medium w-[45%]">{{ t('renameModal.colNewName') }}</th>
                <th class="text-center py-1.5 font-medium w-[10%]">{{ t('renameModal.colStatus') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in previewRows"
                :key="row.path"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"
              >
                <td class="py-1.5 pr-3 truncate max-w-0 text-gray-700 dark:text-gray-300" :title="row.old_name">{{ row.old_name }}</td>
                <td class="py-1.5 pr-3 truncate max-w-0" :class="row.error ? 'text-red-400' : row.conflict ? 'text-yellow-500' : row.same ? 'text-gray-400' : 'text-gray-900 dark:text-white'" :title="row.new_name || row.error">
                  {{ row.new_name || row.error || '-' }}
                </td>
                <td class="py-1.5 text-center">
                  <span v-if="row.error">❌</span>
                  <span v-else-if="row.conflict">⚠️</span>
                  <span v-else-if="row.same">—</span>
                  <span v-else>✅</span>
                </td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>

      <!-- 푸터 버튼 -->
      <div class="px-5 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3 shrink-0">
        <button @click="$emit('close')" class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
          {{ t('common.cancel') }}
        </button>
        <button
          @click="applyRename"
          :disabled="okCount === 0 || applying"
          class="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="applying">{{ t('renameModal.applying') }}</span>
          <span v-else>{{ t('renameModal.applyCount', { n: okCount }) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'

const { t } = useI18n()

const props = defineProps({
  files: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'renamed'])

const presets = computed(() => [
  { label: t('renameModal.presetTrackTitle'),            pattern: '%track% - %title%' },
  { label: t('renameModal.presetArtistTitle'),           pattern: '%artist% - %title%' },
  { label: t('renameModal.presetTrackArtistTitle'),      pattern: '%track% - %artist% - %title%' },
  { label: t('renameModal.presetArtistAlbumTrackTitle'), pattern: '%artist% - %album% - %track% - %title%' },
  { label: t('renameModal.presetDiscTrackTitle'),        pattern: '%disc%-%track% - %title%' },
])

const variables = computed(() => [
  { var: '%title%',        desc: t('renameModal.varTitle') },
  { var: '%artist%',       desc: t('renameModal.varArtist') },
  { var: '%albumartist%',  desc: t('renameModal.varAlbumArtist') },
  { var: '%album%',        desc: t('renameModal.varAlbum') },
  { var: '%track%',        desc: t('renameModal.varTrack') },
  { var: '%totaltracks%',  desc: t('renameModal.varTotalTracks') },
  { var: '%disc%',         desc: t('renameModal.varDisc') },
  { var: '%year%',         desc: t('renameModal.varYear') },
  { var: '%genre%',        desc: t('renameModal.varGenre') },
  { var: '%publisher%',    desc: t('renameModal.varPublisher') },
  { var: '%_filename%',    desc: t('renameModal.varFilename') },
  { var: '%_ext%',         desc: t('renameModal.varExt') },
])

// ── 패턴 히스토리 ──────────────────────────────────────────
const HISTORY_KEY = 'eztag-rename-patterns'
const MAX_HISTORY = 15

const patternHistory = ref(JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'))
const showHistoryDropdown = ref(false)
const historyContainerRef = ref(null)

function savePatternToHistory(pat) {
  if (!pat.trim()) return
  const arr = patternHistory.value.filter(p => p !== pat)
  arr.unshift(pat)
  patternHistory.value = arr.slice(0, MAX_HISTORY)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(patternHistory.value))
}

function selectHistory(pat) {
  pattern.value = pat
  showHistoryDropdown.value = false
  patternInputRef.value?.focus()
}

function removeHistory(i) {
  patternHistory.value.splice(i, 1)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(patternHistory.value))
}

function clearHistory() {
  patternHistory.value = []
  localStorage.removeItem(HISTORY_KEY)
  showHistoryDropdown.value = false
}

function onDocClick(e) {
  if (historyContainerRef.value && !historyContainerRef.value.contains(e.target)) {
    showHistoryDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick, true))
onUnmounted(() => document.removeEventListener('click', onDocClick, true))

// ── 패턴 상태 ─────────────────────────────────────────────
const pattern = ref(patternHistory.value[0] || '%track% - %title%')
const selectedPreset = ref('')
const patternInputRef = ref(null)
const applying = ref(false)

const INVALID_CHARS = /[\\/:*?"<>|]/g

function renderPattern(pat, fields) {
  const FIELD_MAP = {
    title: 'title',
    albumartist: 'album_artist',
    album: 'album_title',
    totaltracks: 'total_tracks',
    year: 'year',
    genre: 'genre',
    publisher: 'label',
  }
  return pat.replace(/%([^%]+)%/g, (m, v) => {
    v = v.toLowerCase()
    if (v === '_filename') return fields._filename || ''
    if (v === '_ext') return fields._ext || ''
    if (v === '_bitrate') return String(fields.bitrate || '')
    if (v === '_codec') return (fields.file_format || '').toUpperCase()
    if (v === 'artist') return fields.artist || ''
    if (v === 'track') {
      const n = fields.track_no
      if (n == null) return ''
      return String(parseInt(n) || 0).padStart(2, '0')
    }
    if (v === 'disc') {
      const d = fields.disc_no
      if (!d || d === 0) return ''
      return String(d)
    }
    const key = FIELD_MAP[v]
    if (key) return fields[key] != null ? String(fields[key]) : ''
    return m
  })
}

function sanitize(name) {
  name = name.replace(INVALID_CHARS, '_').replace(/ {2,}/g, ' ').replace(/^[ .]+|[ .]+$/g, '')
  return name || '_'
}

function buildName(pat, file) {
  const raw = renderPattern(pat, file)
  const name = sanitize(raw)
  const ext = file._ext || ''
  return ext ? `${name}.${ext}` : name
}

const previewRows = computed(() => {
  if (!pattern.value) return []
  return props.files.map(f => {
    const oldName = f._filename + (f._ext ? '.' + f._ext : '')
    try {
      const newName = buildName(pattern.value, f)
      const same = newName === oldName
      return { path: f.path, old_name: oldName, new_name: newName, conflict: false, error: null, same }
    } catch (e) {
      return { path: f.path, old_name: oldName, new_name: null, conflict: false, error: String(e), same: false }
    }
  })
})

const okCount = computed(() => previewRows.value.filter(r => !r.error && !r.conflict && !r.same).length)
const conflictCount = computed(() => previewRows.value.filter(r => r.conflict).length)
const skipCount = computed(() => previewRows.value.filter(r => r.error).length)
const sameCount = computed(() => previewRows.value.filter(r => r.same).length)

function applyPreset() {
  if (selectedPreset.value) {
    pattern.value = selectedPreset.value
    selectedPreset.value = ''
  }
}

function insertVar(v) {
  const el = patternInputRef.value
  if (!el) { pattern.value += v; return }
  const start = el.selectionStart ?? pattern.value.length
  const end = el.selectionEnd ?? pattern.value.length
  pattern.value = pattern.value.slice(0, start) + v + pattern.value.slice(end)
  const newPos = start + v.length
  el.focus()
  el.setSelectionRange(newPos, newPos)
}

async function applyRename() {
  if (okCount.value === 0 || applying.value) return
  applying.value = true
  try {
    const paths = previewRows.value.filter(r => !r.error && !r.conflict && !r.same).map(r => r.path)
    const res = await browseApi.renameByTags(paths, pattern.value)
    savePatternToHistory(pattern.value)
    emit('renamed', res.data)
  } catch (e) {
    console.error('[RenameByTagsModal] apply error:', e)
  } finally {
    applying.value = false
  }
}
</script>
