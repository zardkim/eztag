<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-xl shadow-2xl w-full sm:max-w-3xl flex flex-col max-h-[92vh] sm:max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('tagFromName.title') }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1">✕</button>
      </div>

      <!-- 패턴 입력 -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0 space-y-3">
        <!-- 패턴 입력 + 프리셋 -->
        <div class="flex flex-col sm:flex-row gap-2">
          <!-- 입력란 + 히스토리 드롭다운 -->
          <div class="relative flex-1" ref="historyContainerRef">
            <input
              ref="patternInputRef"
              v-model="pattern"
              type="text"
              class="w-full px-3 py-2 pr-8 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              :placeholder="t('tagFromName.patternPlaceholder')"
              @focus="patternHistory.length > 0 && (showHistoryDropdown = true)"
            />
            <button
              v-if="patternHistory.length > 0"
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs leading-none px-0.5"
              :class="showHistoryDropdown ? 'text-purple-500' : ''"
              @click.stop="showHistoryDropdown = !showHistoryDropdown"
              :title="t('tagFromName.recentPatterns')"
            >▾</button>

            <!-- 히스토리 드롭다운 -->
            <div
              v-if="showHistoryDropdown && patternHistory.length > 0"
              class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 overflow-hidden"
            >
              <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('tagFromName.recentPatterns') }}</span>
                <button
                  type="button"
                  class="text-[10px] text-gray-400 hover:text-red-500 transition-colors"
                  @click.stop="clearHistory"
                >{{ t('tagFromName.clearHistory') }}</button>
              </div>
              <div class="max-h-48 overflow-y-auto py-1">
                <div
                  v-for="(h, i) in patternHistory"
                  :key="i"
                  class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 group transition-colors cursor-pointer"
                  @click.stop="selectHistory(h)"
                >
                  <span class="text-[10px] text-gray-400 shrink-0">🕐</span>
                  <span class="font-mono text-sm text-gray-700 dark:text-gray-300 truncate flex-1">{{ h }}</span>
                  <button
                    type="button"
                    class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 text-xs shrink-0 transition-all"
                    @click.stop="removeHistory(i)"
                    title="삭제"
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
              <span>{{ t('tagFromName.presetPlaceholder') }}</span>
              <span class="text-[10px] opacity-60 ml-0.5">▾</span>
            </button>

            <div
              v-if="showPresetDropdown"
              class="absolute top-full right-0 mt-1 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-2xl z-50 overflow-hidden"
            >
              <!-- 기본 프리셋 -->
              <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('tagFromName.builtinPresets') }}</span>
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
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('tagFromName.myPresets') }}</span>
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
                      :title="t('tagFromName.deletePreset')"
                    >✕</button>
                  </div>
                </div>
              </template>

              <!-- 현재 패턴 저장 -->
              <div class="border-t border-gray-100 dark:border-gray-700 p-2">
                <button
                  v-if="!showSavePreset"
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
                  :disabled="!pattern.trim()"
                  @click.stop="showSavePreset = true; savePresetName = ''; nextTick(() => savePresetInputRef?.focus())"
                >
                  <span>💾</span>
                  <span>{{ t('tagFromName.saveAsPreset') }}</span>
                </button>
                <div v-else class="flex gap-1.5" @click.stop>
                  <input
                    ref="savePresetInputRef"
                    v-model="savePresetName"
                    type="text"
                    class="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    :placeholder="t('tagFromName.presetNamePlaceholder')"
                    @keydown.enter="confirmSavePreset"
                    @keydown.escape="showSavePreset = false"
                  />
                  <button
                    type="button"
                    class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
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
            class="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-purple-100 dark:hover:bg-purple-900 hover:text-purple-700 dark:hover:text-purple-300 border border-gray-200 dark:border-gray-600"
            :title="v.desc"
          >{{ v.var }}</button>
        </div>

        <!-- 적용 필드 체크박스 -->
        <div>
          <div class="text-[11px] text-gray-500 dark:text-gray-400 mb-1.5">{{ t('tagFromName.fieldsLabel') }}</div>
          <div class="flex flex-wrap gap-x-4 gap-y-1">
            <label
              v-for="f in fieldOptions"
              :key="f.key"
              class="flex items-center gap-1.5 cursor-pointer"
            >
              <input
                type="checkbox"
                :value="f.key"
                v-model="selectedFields"
                class="w-3.5 h-3.5 rounded accent-purple-600"
              />
              <span class="text-xs text-gray-700 dark:text-gray-300">{{ f.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- 미리보기 -->
      <div class="flex-1 overflow-auto px-5 py-3">
        <div v-if="!pattern" class="text-center text-sm text-gray-400 py-8">{{ t('tagFromName.patternHint') }}</div>
        <template v-else-if="previewRows.length === 0">
          <div class="text-center text-sm text-gray-400 py-8">{{ t('tagFromName.noFiles') }}</div>
        </template>
        <template v-else>
          <!-- 요약 -->
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-2 flex gap-3">
            <span class="text-green-600 dark:text-green-400">{{ t('tagFromName.matchCount', { n: matchCount }) }}</span>
            <span v-if="noMatchCount" class="text-red-500">{{ t('tagFromName.noMatchCount', { n: noMatchCount }) }}</span>
          </div>

          <div class="space-y-1.5">
            <div
              v-for="row in previewRows"
              :key="row.path"
              class="rounded-lg px-3 py-2.5 text-xs"
              :class="row.error ? 'bg-red-50 dark:bg-red-900/10' : 'bg-green-50 dark:bg-green-900/10'"
            >
              <div class="flex items-start gap-2">
                <span class="mt-0.5 shrink-0 text-sm leading-none">
                  <span v-if="row.error">❌</span>
                  <span v-else>✅</span>
                </span>
                <div class="flex-1 min-w-0">
                  <div class="text-gray-500 dark:text-gray-400 truncate font-mono">{{ row.filename }}</div>
                  <div v-if="row.error" class="mt-0.5 text-red-500">{{ row.error }}</div>
                  <div v-else class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                    <span
                      v-for="(val, key) in filteredParsed(row.parsed)"
                      :key="key"
                      class="text-gray-700 dark:text-gray-300"
                    >
                      <span class="text-gray-400">{{ fieldLabel(key) }}:</span>
                      <span class="ml-0.5 font-medium">{{ val }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 푸터 -->
      <div class="px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] border-t border-gray-200 dark:border-gray-700 shrink-0">
        <div class="flex gap-2">
          <button
            @click="$emit('close')"
            class="flex-1 py-3 text-sm rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >{{ t('common.cancel') }}</button>
          <button
            @click="runPreview"
            :disabled="!pattern.trim() || previewing"
            class="flex-1 py-3 text-sm rounded-xl border border-purple-300 dark:border-purple-600 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="previewing">{{ t('tagFromName.previewing') }}</span>
            <span v-else>{{ t('tagFromName.preview') }}</span>
          </button>
          <button
            @click="applyTags"
            :disabled="matchCount === 0 || applying"
            class="flex-[2] py-3 text-sm rounded-xl bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            <span v-if="applying">{{ t('tagFromName.applying') }}</span>
            <span v-else>{{ t('tagFromName.applyCount', { n: matchCount }) }}</span>
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
const emit = defineEmits(['close', 'tagged'])

// ── 기본 프리셋 ───────────────────────────────────────────
const builtinPresets = computed(() => [
  { label: t('tagFromName.presetTrackTitle'),         pattern: '%track% - %title%' },
  { label: t('tagFromName.presetArtistTitle'),        pattern: '%artist% - %title%' },
  { label: t('tagFromName.presetTrackArtistTitle'),   pattern: '%track% - %artist% - %title%' },
  { label: t('tagFromName.presetDiscTrackTitle'),     pattern: '%disc%-%track% - %title%' },
  { label: t('tagFromName.presetArtistAlbumTitle'),   pattern: '%artist% - %album% - %title%' },
])

// ── 변수 버튼 목록 ────────────────────────────────────────
const variables = computed(() => [
  { var: '%track%',        desc: t('tagFromName.varTrack') },
  { var: '%disc%',         desc: t('tagFromName.varDisc') },
  { var: '%title%',        desc: t('tagFromName.varTitle') },
  { var: '%artist%',       desc: t('tagFromName.varArtist') },
  { var: '%album_artist%', desc: t('tagFromName.varAlbumArtist') },
  { var: '%album%',        desc: t('tagFromName.varAlbum') },
  { var: '%year%',         desc: t('tagFromName.varYear') },
  { var: '%genre%',        desc: t('tagFromName.varGenre') },
  { var: '%label%',        desc: t('tagFromName.varLabel') },
])

// ── 적용 필드 옵션 ────────────────────────────────────────
const fieldOptions = computed(() => [
  { key: 'track_no',    label: t('tagFromName.varTrack') },
  { key: 'disc_no',     label: t('tagFromName.varDisc') },
  { key: 'title',       label: t('tagFromName.varTitle') },
  { key: 'artist',      label: t('tagFromName.varArtist') },
  { key: 'album_artist',label: t('tagFromName.varAlbumArtist') },
  { key: 'album_title', label: t('tagFromName.varAlbum') },
  { key: 'year',        label: t('tagFromName.varYear') },
  { key: 'genre',       label: t('tagFromName.varGenre') },
  { key: 'label',       label: t('tagFromName.varLabel') },
])

function fieldLabel(key) {
  return fieldOptions.value.find(f => f.key === key)?.label || key
}

// 기본: 전체 선택
const selectedFields = ref(fieldOptions.value.map(f => f.key))

// ── 사용자 정의 프리셋 ─────────────────────────────────────
const CUSTOM_PRESETS_KEY = 'eztag-tagfromname-presets'
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

// ── 패턴 히스토리 ────────────────────────────────────────
const HISTORY_KEY = 'eztag-tagfromname-patterns'
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

function selectHistory(h) {
  pattern.value = h
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

function onDocClickHistory(e) {
  if (historyContainerRef.value && !historyContainerRef.value.contains(e.target)) {
    showHistoryDropdown.value = false
  }
}

// ── 프리셋 드롭다운 ───────────────────────────────────────
const showPresetDropdown = ref(false)
const showSavePreset = ref(false)
const savePresetName = ref('')
const savePresetInputRef = ref(null)
const presetContainerRef = ref(null)

function applyPresetItem(pat) {
  pattern.value = pat
  showPresetDropdown.value = false
  showSavePreset.value = false
  previewRows.value = []
}

function onDocClickPreset(e) {
  if (presetContainerRef.value && !presetContainerRef.value.contains(e.target)) {
    showPresetDropdown.value = false
    showSavePreset.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocClickHistory, true)
  document.addEventListener('click', onDocClickPreset, true)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClickHistory, true)
  document.removeEventListener('click', onDocClickPreset, true)
})

// ── 패턴 ────────────────────────────────────────────────
const pattern = ref(patternHistory.value[0] || '%track% - %title%')
const patternInputRef = ref(null)

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

// ── 미리보기 결과 ────────────────────────────────────────
const previewRows = ref([])
const previewing = ref(false)
const applying = ref(false)

const matchCount = computed(() => previewRows.value.filter(r => !r.error).length)
const noMatchCount = computed(() => previewRows.value.filter(r => r.error).length)

function filteredParsed(parsed) {
  if (!parsed) return {}
  if (selectedFields.value.length === 0) return parsed
  return Object.fromEntries(
    Object.entries(parsed).filter(([k]) => selectedFields.value.includes(k))
  )
}

async function runPreview() {
  if (!pattern.value.trim() || previewing.value) return
  previewing.value = true
  try {
    const paths = props.files.map(f => f.path)
    const res = await browseApi.tagFromNamePreview(paths, pattern.value)
    previewRows.value = res.data.results || []
  } catch (e) {
    console.error('[TagFromNameModal] preview error:', e)
  } finally {
    previewing.value = false
  }
}

async function applyTags() {
  if (matchCount.value === 0 || applying.value) return
  applying.value = true
  try {
    const paths = previewRows.value.filter(r => !r.error).map(r => r.path)
    const fields = selectedFields.value
    const res = await browseApi.tagFromNameApply(paths, pattern.value, fields)
    savePatternToHistory(pattern.value)
    emit('tagged', res.data)
  } catch (e) {
    console.error('[TagFromNameModal] apply error:', e)
  } finally {
    applying.value = false
  }
}
</script>
