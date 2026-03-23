<template>
  <div class="fixed inset-0 z-[400] flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-xl shadow-2xl w-full sm:max-w-lg flex flex-col max-h-[85vh]">

      <!-- 헤더 -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('renameFolderModal.title') }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1">✕</button>
      </div>

      <!-- 모드 탭 -->
      <div class="px-5 pt-4 pb-0 shrink-0 flex gap-2">
        <button
          v-for="tab in tabs" :key="tab.key"
          class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
          :class="mode === tab.key
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'"
          @click="mode = tab.key"
        >{{ tab.label }}</button>
      </div>

      <!-- 입력 영역 -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0 space-y-3">

        <!-- 직접 입력 모드 -->
        <template v-if="mode === 'direct'">
          <input
            v-model="directName"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="folder.name"
            @keydown.enter="apply"
          />
        </template>

        <!-- 태그 기반 모드 -->
        <template v-else>
          <div class="flex gap-2">
            <!-- 패턴 입력 + 히스토리 -->
            <div class="relative flex-1" ref="historyContainerRef">
              <input
                ref="patternInputRef"
                v-model="pattern"
                class="w-full px-3 py-2 pr-8 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                :placeholder="t('renameFolderModal.patternPlaceholder')"
                @focus="patternHistory.length > 0 && (showHistoryDropdown = true)"
                @keydown.enter="apply"
              />
              <button
                v-if="patternHistory.length > 0"
                type="button"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs leading-none px-0.5"
                :class="showHistoryDropdown ? 'text-blue-500' : ''"
                @click.stop="showHistoryDropdown = !showHistoryDropdown"
              >▾</button>
              <!-- 히스토리 드롭다운 -->
              <div
                v-if="showHistoryDropdown && patternHistory.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 overflow-hidden"
              >
                <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('renameFolderModal.recentPatterns') }}</span>
                  <button type="button" class="text-[10px] text-gray-400 hover:text-red-500 transition-colors" @click.stop="clearHistory">{{ t('renameFolderModal.clearHistory') }}</button>
                </div>
                <div class="max-h-36 overflow-y-auto py-1">
                  <div
                    v-for="(p, i) in patternHistory" :key="i"
                    class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group transition-colors"
                    @click.stop="selectHistory(p)"
                  >
                    <span class="text-[10px] text-gray-400 shrink-0">🕐</span>
                    <span class="font-mono text-sm text-gray-700 dark:text-gray-300 truncate flex-1">{{ p }}</span>
                    <button type="button" class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 text-xs shrink-0 transition-all" @click.stop="removeHistory(i)">✕</button>
                  </div>
                </div>
              </div>
            </div>
            <!-- 프리셋 -->
            <select
              v-model="selectedPreset"
              @change="applyPreset"
              class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">{{ t('renameFolderModal.presetPlaceholder') }}</option>
              <option v-for="p in presets" :key="p.pattern" :value="p.pattern">{{ p.label }}</option>
            </select>
          </div>

          <!-- 변수 버튼 -->
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="v in variables" :key="v.var"
              @click="insertVar(v.var)"
              class="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900 hover:text-blue-700 dark:hover:text-blue-300 border border-gray-200 dark:border-gray-600 transition-colors"
              :title="v.desc"
            >{{ v.var }}</button>
          </div>

          <!-- 메타데이터 없음 경고 -->
          <p v-if="!firstTrack" class="text-xs text-yellow-600 dark:text-yellow-400">{{ t('renameFolderModal.noMetadata') }}</p>
        </template>
      </div>

      <!-- 미리보기 -->
      <div class="px-5 py-4 flex-1 min-h-0 space-y-2.5">
        <div class="flex items-start gap-3">
          <span class="text-[11px] text-gray-400 shrink-0 w-16 pt-0.5">{{ t('renameFolderModal.currentLabel') }}</span>
          <span class="text-xs text-gray-500 dark:text-gray-400 font-mono truncate">{{ folder.name }}</span>
        </div>
        <div class="flex items-start gap-3">
          <span class="text-[11px] text-gray-400 shrink-0 w-16 pt-0.5">{{ t('renameFolderModal.previewLabel') }}</span>
          <span
            class="text-xs font-mono font-medium truncate"
            :class="previewName && previewName !== folder.name ? 'text-green-600 dark:text-green-400' : 'text-gray-300 dark:text-gray-600'"
          >{{ previewName || '—' }}</span>
        </div>
      </div>

      <!-- 푸터 -->
      <div class="px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] border-t border-gray-200 dark:border-gray-700 shrink-0">
        <div class="flex gap-2">
          <button
            @click="$emit('close')"
            class="flex-1 py-3 text-sm rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >{{ t('common.cancel') }}</button>
          <button
            @click="apply"
            :disabled="!canApply || applying"
            class="flex-[2] py-3 text-sm rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >{{ applying ? t('renameFolderModal.applying') : t('renameFolderModal.apply') }}</button>
        </div>
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
  folder:     { type: Object, required: true },  // { name, path }
  firstTrack: { type: Object, default: null },   // browserStore.files[0]
})
const emit = defineEmits(['close', 'renamed'])

// ── 상태 ─────────────────────────────────────────────────────
const mode = ref('pattern')
const directName = ref(props.folder.name)
const pattern = ref('')
const selectedPreset = ref('')
const applying = ref(false)
const patternInputRef = ref(null)
const historyContainerRef = ref(null)
const showHistoryDropdown = ref(false)

const HISTORY_KEY = 'eztag-folder-rename-patterns'
const MAX_HISTORY = 10
const patternHistory = ref(JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'))

// ── 탭 / 프리셋 / 변수 ────────────────────────────────────────
const tabs = computed(() => [
  { key: 'pattern', label: t('renameFolderModal.tabPattern') },
  { key: 'direct',  label: t('renameFolderModal.tabDirect') },
])

const presets = computed(() => [
  { label: t('renameFolderModal.presetArtistAlbum'),      pattern: '%albumartist% - %album%' },
  { label: t('renameFolderModal.presetAlbumYear'),         pattern: '%album% (%year%)' },
  { label: t('renameFolderModal.presetArtistAlbumYear'),   pattern: '%albumartist% - %album% (%year%)' },
  { label: t('renameFolderModal.presetAlbum'),             pattern: '%album%' },
])

const variables = computed(() => [
  { var: '%albumartist%', desc: t('renameFolderModal.varAlbumArtist') },
  { var: '%artist%',      desc: t('renameFolderModal.varArtist') },
  { var: '%album%',       desc: t('renameFolderModal.varAlbum') },
  { var: '%year%',        desc: t('renameFolderModal.varYear') },
  { var: '%genre%',       desc: t('renameFolderModal.varGenre') },
  { var: '%label%',       desc: t('renameFolderModal.varLabel') },
])

// ── 패턴 렌더링 ───────────────────────────────────────────────
const INVALID_CHARS = /[\\/:*?"<>|]/g

function sanitize(name) {
  return (name || '').replace(INVALID_CHARS, '_').replace(/ {2,}/g, ' ').replace(/^[ .]+|[ .]+$/g, '') || '_'
}

function renderPattern(pat) {
  const tr = props.firstTrack || {}
  return pat.replace(/%([^%]+)%/g, (m, v) => {
    switch (v.toLowerCase()) {
      case 'albumartist': return tr.album_artist || tr.artist || ''
      case 'artist':      return tr.artist || ''
      case 'album':       return tr.album_title || ''
      case 'year':        return tr.year ? String(tr.year) : ''
      case 'genre':       return tr.genre || ''
      case 'label':       return tr.label || ''
      default:            return m
    }
  })
}

const previewName = computed(() => {
  if (mode.value === 'direct') {
    const name = directName.value.trim()
    return name ? sanitize(name) : ''
  }
  if (!pattern.value.trim()) return ''
  return sanitize(renderPattern(pattern.value))
})

const canApply = computed(() =>
  !!previewName.value && previewName.value !== props.folder.name
)

// ── 히스토리 관리 ─────────────────────────────────────────────
function saveToHistory(pat) {
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

// ── 프리셋 / 변수 삽입 ────────────────────────────────────────
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
  const end   = el.selectionEnd   ?? pattern.value.length
  pattern.value = pattern.value.slice(0, start) + v + pattern.value.slice(end)
  const newPos = start + v.length
  el.focus()
  el.setSelectionRange(newPos, newPos)
}

// ── 적용 ─────────────────────────────────────────────────────
async function apply() {
  if (!canApply.value || applying.value) return
  applying.value = true
  try {
    const newName = previewName.value
    const { data } = await browseApi.renameFolder(props.folder.path, newName)
    if (mode.value === 'pattern') saveToHistory(pattern.value)
    emit('renamed', data)
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  pattern.value = patternHistory.value[0] || '%albumartist% - %album%'
  document.addEventListener('click', onDocClick, true)
})
onUnmounted(() => document.removeEventListener('click', onDocClick, true))
</script>
