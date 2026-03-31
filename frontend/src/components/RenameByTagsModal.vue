<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-xl shadow-2xl w-full sm:max-w-3xl flex flex-col max-h-[92vh] sm:max-h-[90vh]">
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

          <!-- 프리셋 드롭다운 -->
          <div class="relative" ref="presetContainerRef">
            <button
              type="button"
              class="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors whitespace-nowrap"
              @click.stop="showPresetDropdown = !showPresetDropdown; showSavePreset = false"
            >
              <span>📋</span>
              <span>{{ t('renameModal.presetPlaceholder') }}</span>
              <span class="text-[10px] opacity-60 ml-0.5">▾</span>
            </button>

            <!-- 프리셋 드롭다운 패널 -->
            <div
              v-if="showPresetDropdown"
              class="absolute top-full right-0 mt-1 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-2xl z-50 overflow-hidden"
            >
              <!-- 기본 프리셋 -->
              <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('renameModal.builtinPresets') }}</span>
              </div>
              <div class="py-1">
                <button
                  v-for="p in builtinPresets"
                  :key="p.pattern"
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  @click.stop="applyPresetItem(p.pattern)"
                >
                  <span class="flex-1 text-sm text-gray-700 dark:text-gray-300">{{ p.label }}</span>
                  <span class="text-[10px] font-mono text-gray-400 truncate max-w-[120px]">{{ p.pattern }}</span>
                </button>
              </div>

              <!-- 내 프리셋 -->
              <template v-if="customPresets.length > 0">
                <div class="px-3 py-1.5 border-t border-gray-100 dark:border-gray-700">
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('renameModal.myPresets') }}</span>
                </div>
                <div class="py-1 max-h-40 overflow-y-auto">
                  <div
                    v-for="(p, i) in customPresets"
                    :key="i"
                    class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 group transition-colors"
                  >
                    <button
                      type="button"
                      class="flex-1 flex flex-col items-start text-left min-w-0"
                      @click.stop="applyPresetItem(p.pattern)"
                    >
                      <span class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate w-full">{{ p.label }}</span>
                      <span class="text-[10px] font-mono text-gray-400 truncate w-full">{{ p.pattern }}</span>
                    </button>
                    <button
                      type="button"
                      class="shrink-0 text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-all px-1"
                      @click.stop="removeCustomPreset(i)"
                      :title="t('renameModal.deletePreset')"
                    >✕</button>
                  </div>
                </div>
              </template>

              <!-- 현재 패턴 저장 -->
              <div class="border-t border-gray-100 dark:border-gray-700 p-2">
                <button
                  v-if="!showSavePreset"
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                  :disabled="!pattern.trim()"
                  @click.stop="showSavePreset = true; savePresetName = ''; nextTick(() => savePresetInputRef?.focus())"
                >
                  <span>💾</span>
                  <span>{{ t('renameModal.saveAsPreset') }}</span>
                </button>
                <div v-else class="flex gap-1.5" @click.stop>
                  <input
                    ref="savePresetInputRef"
                    v-model="savePresetName"
                    type="text"
                    class="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    :placeholder="t('renameModal.presetNamePlaceholder')"
                    @keydown.enter="confirmSavePreset"
                    @keydown.escape="showSavePreset = false"
                  />
                  <button
                    type="button"
                    class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    :disabled="!savePresetName.trim()"
                    @click.stop="confirmSavePreset"
                  >{{ t('common.save') }}</button>
                  <button
                    type="button"
                    class="px-2 py-1.5 text-sm text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg transition-colors"
                    @click.stop="showSavePreset = false"
                  >✕</button>
                </div>
              </div>
            </div>
          </div>
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

          <div class="space-y-1.5">
            <div
              v-for="row in previewRows"
              :key="row.path"
              class="flex items-start gap-2 rounded-lg px-3 py-2.5 text-xs"
              :class="row.error ? 'bg-red-50 dark:bg-red-900/10' : row.conflict ? 'bg-yellow-50 dark:bg-yellow-900/10' : row.same ? 'bg-gray-50 dark:bg-gray-700/30' : 'bg-green-50 dark:bg-green-900/10'"
            >
              <span class="mt-0.5 shrink-0 text-sm leading-none">
                <span v-if="row.error">❌</span>
                <span v-else-if="row.conflict">⚠️</span>
                <span v-else-if="row.same">—</span>
                <span v-else>✅</span>
              </span>
              <div class="flex-1 min-w-0">
                <div class="text-gray-500 dark:text-gray-400 truncate">{{ row.old_name }}</div>
                <div
                  v-if="!row.same"
                  class="mt-0.5 truncate font-medium"
                  :class="row.error ? 'text-red-500' : row.conflict ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-900 dark:text-white'"
                >→ {{ row.new_name || row.error || '-' }}</div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 푸터 버튼 -->
      <div class="px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] border-t border-gray-200 dark:border-gray-700 shrink-0">
        <div class="flex gap-2">
          <button
            @click="$emit('close')"
            class="flex-1 py-3 text-sm rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >{{ t('common.cancel') }}</button>
          <button
            @click="applyRename"
            :disabled="okCount === 0 || applying"
            class="flex-[2] py-3 text-sm rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            <span v-if="applying">{{ t('renameModal.applying') }}</span>
            <span v-else>{{ t('renameModal.applyCount', { n: okCount }) }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'

const { t } = useI18n()

const props = defineProps({
  files: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'renamed'])

const builtinPresets = computed(() => [
  { label: t('renameModal.presetTrackTitle'),            pattern: '%track% - %title%' },
  { label: t('renameModal.presetArtistTitle'),           pattern: '%artist% - %title%' },
  { label: t('renameModal.presetTrackArtistTitle'),      pattern: '%track% - %artist% - %title%' },
  { label: t('renameModal.presetArtistAlbumTrackTitle'), pattern: '%artist% - %album% - %track% - %title%' },
  { label: t('renameModal.presetDiscTrackTitle'),        pattern: '%disc%-%track% - %title%' },
])

// ── 사용자 정의 프리셋 ────────────────────────────────────
const CUSTOM_PRESETS_KEY = 'eztag-rename-custom-presets'
const customPresets = ref(JSON.parse(localStorage.getItem(CUSTOM_PRESETS_KEY) || '[]'))

function saveCustomPresets() {
  localStorage.setItem(CUSTOM_PRESETS_KEY, JSON.stringify(customPresets.value))
}

function removeCustomPreset(i) {
  customPresets.value.splice(i, 1)
  saveCustomPresets()
}

function confirmSavePreset() {
  const name = savePresetName.value.trim()
  if (!name || !pattern.value.trim()) return
  // 중복 이름이면 덮어쓰기
  const existing = customPresets.value.findIndex(p => p.label === name)
  if (existing !== -1) {
    customPresets.value[existing].pattern = pattern.value
  } else {
    customPresets.value.push({ label: name, pattern: pattern.value })
  }
  saveCustomPresets()
  showSavePreset.value = false
  savePresetName.value = ''
}

const variables = computed(() => [
  { var: '%title%',             desc: t('renameModal.varTitle') },
  { var: '%artist%',            desc: t('renameModal.varArtist') },
  { var: '%albumartist%',       desc: t('renameModal.varAlbumArtist') },
  { var: '%album%',             desc: t('renameModal.varAlbum') },
  { var: '$num(%track%,2)',     desc: t('renameModal.varTrackNum2') },
  { var: '$num(%track%,3)',     desc: t('renameModal.varTrackNum3') },
  { var: '%track%',             desc: t('renameModal.varTrack') },
  { var: '%totaltracks%',       desc: t('renameModal.varTotalTracks') },
  { var: '%disc%',              desc: t('renameModal.varDisc') },
  { var: '%year%',              desc: t('renameModal.varYear') },
  { var: '%genre%',             desc: t('renameModal.varGenre') },
  { var: '%publisher%',         desc: t('renameModal.varPublisher') },
  { var: '%_filename%',         desc: t('renameModal.varFilename') },
  { var: '%_ext%',              desc: t('renameModal.varExt') },
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

onMounted(() => {
  document.addEventListener('click', onDocClick, true)
  document.addEventListener('click', onDocClickPreset, true)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick, true)
  document.removeEventListener('click', onDocClickPreset, true)
})

// ── 프리셋 드롭다운 상태 ──────────────────────────────────
const showPresetDropdown = ref(false)
const showSavePreset = ref(false)
const savePresetName = ref('')
const savePresetInputRef = ref(null)
const presetContainerRef = ref(null)

function applyPresetItem(pat) {
  pattern.value = pat
  showPresetDropdown.value = false
  showSavePreset.value = false
}

function onDocClickPreset(e) {
  if (presetContainerRef.value && !presetContainerRef.value.contains(e.target)) {
    showPresetDropdown.value = false
    showSavePreset.value = false
  }
}

// ── 패턴 상태 ─────────────────────────────────────────────
const pattern = ref(patternHistory.value[0] || '%track% - %title%')
const patternInputRef = ref(null)
const applying = ref(false)

const INVALID_CHARS = /[\\/:*?"<>|]/g

const _FIELD_MAP = {
  title: 'title',
  artist: 'artist',
  albumartist: 'album_artist',
  album: 'album_title',
  totaltracks: 'total_tracks',
  year: 'year',
  genre: 'genre',
  publisher: 'label',
}

function resolveVar(v, fields) {
  v = v.toLowerCase()
  if (v === '_filename') return fields._filename || ''
  if (v === '_ext') return fields._ext || ''
  if (v === '_bitrate') return String(fields.bitrate || '')
  if (v === '_codec') return (fields.file_format || '').toUpperCase()
  if (v === 'track') {
    const n = fields.track_no
    if (n == null) return ''
    return String(parseInt(n) || 0)
  }
  if (v === 'disc') {
    const d = fields.disc_no
    if (!d || d === 0) return ''
    return String(d)
  }
  const key = _FIELD_MAP[v]
  if (key) return fields[key] != null ? String(fields[key]) : ''
  return ''
}

function renderPattern(pat, fields) {
  // 1단계: $num(%field%,N) 처리
  pat = pat.replace(/\$num\((%[^%]+%)\s*,\s*(\d+)\)/g, (m, inner, digits) => {
    const varName = inner.slice(1, -1)
    const raw = resolveVar(varName, fields)
    const n = parseInt(raw)
    if (isNaN(n)) return raw
    return String(n).padStart(parseInt(digits), '0')
  })
  // 2단계: 나머지 %field% 처리 (%track%은 기본 2자리 패딩)
  return pat.replace(/%([^%]+)%/g, (m, v) => {
    v = v.toLowerCase()
    if (v === 'track') {
      const raw = resolveVar(v, fields)
      if (!raw) return ''
      return raw.padStart(2, '0')
    }
    return resolveVar(v, fields) || m
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
