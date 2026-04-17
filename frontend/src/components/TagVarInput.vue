<template>
  <div class="space-y-2">
    <!-- Row 1: Pattern input + history + presets -->
    <div class="flex flex-col sm:flex-row gap-2">
      <!-- Input with history dropdown -->
      <div class="relative flex-1" ref="historyContainerRef">
        <input
          ref="inputRef"
          :value="modelValue"
          type="text"
          class="w-full px-3 py-2 pr-8 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none"
          :class="focusRingClass"
          :placeholder="placeholder"
          @input="e => emit('update:modelValue', e.target.value)"
          @focus="patternHistory.length > 0 && (showHistoryDropdown = true)"
          @click="saveCursor"
          @keyup="saveCursor"
        />
        <button
          v-if="patternHistory.length > 0"
          type="button"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs leading-none px-0.5"
          :class="showHistoryDropdown ? activeTextClass : ''"
          @click.stop="showHistoryDropdown = !showHistoryDropdown"
          :title="t('patternInput.recentPatterns')"
        >▾</button>

        <!-- 히스토리 드롭다운 -->
        <div
          v-if="showHistoryDropdown && patternHistory.length > 0"
          class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-xl z-50 overflow-hidden"
        >
          <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('patternInput.recentPatterns') }}</span>
            <button
              type="button"
              class="text-[10px] text-gray-400 hover:text-red-500 transition-colors"
              @click.stop="clearHistory"
            >{{ t('patternInput.clearHistory') }}</button>
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
                title="삭제"
              >✕</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 프리셋 드롭다운 (builtinPresets 또는 customPresets가 있을 때만) -->
      <div v-if="builtinPresets.length > 0 || storageKey" class="relative" ref="presetContainerRef">
        <button
          type="button"
          class="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors whitespace-nowrap"
          @click.stop="showPresetDropdown = !showPresetDropdown; showSavePreset = false"
        >
          <span>📋</span>
          <span>{{ t('patternInput.presets') }}</span>
          <span class="text-[10px] opacity-60 ml-0.5">▾</span>
        </button>

        <!-- 프리셋 패널 -->
        <div
          v-if="showPresetDropdown"
          class="absolute top-full right-0 mt-1 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-2xl z-50 overflow-hidden"
        >
          <!-- 기본 프리셋 -->
          <template v-if="builtinPresets.length > 0">
            <div class="px-3 py-1.5 border-b border-gray-100 dark:border-gray-700">
              <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('patternInput.builtinPresets') }}</span>
            </div>
            <div class="py-1">
              <button
                v-for="p in builtinPresets"
                :key="p.pattern"
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                @click.stop="applyPreset(p.pattern)"
              >
                <span class="flex-1 text-sm text-gray-700 dark:text-gray-300">{{ p.label }}</span>
                <span class="text-[10px] font-mono text-gray-400 truncate max-w-[120px]">{{ p.pattern }}</span>
              </button>
            </div>
          </template>

          <!-- 내 프리셋 -->
          <template v-if="storageKey && customPresets.length > 0">
            <div class="px-3 py-1.5 border-t border-gray-100 dark:border-gray-700">
              <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('patternInput.myPresets') }}</span>
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
                  @click.stop="applyPreset(p.pattern)"
                >
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate w-full">{{ p.label }}</span>
                  <span class="text-[10px] font-mono text-gray-400 truncate w-full">{{ p.pattern }}</span>
                </button>
                <button
                  type="button"
                  class="shrink-0 text-gray-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-all px-1"
                  @click.stop="removeCustomPreset(i)"
                  :title="t('patternInput.deletePreset')"
                >✕</button>
              </div>
            </div>
          </template>

          <!-- 현재 패턴 저장 (storageKey 있을 때만) -->
          <div v-if="storageKey" class="border-t border-gray-100 dark:border-gray-700 p-2">
            <button
              v-if="!showSavePreset"
              type="button"
              class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors"
              :class="savePresetBtnClass"
              :disabled="!modelValue?.trim()"
              @click.stop="showSavePreset = true; savePresetName = ''; nextTick(() => savePresetInputRef?.focus())"
            >
              <span>💾</span>
              <span>{{ t('patternInput.saveAsPreset') }}</span>
            </button>
            <div v-else class="flex gap-1.5" @click.stop>
              <input
                ref="savePresetInputRef"
                v-model="savePresetName"
                type="text"
                class="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none"
                :class="focusRingClass"
                :placeholder="t('patternInput.presetNamePlaceholder')"
                @keydown.enter="confirmSavePreset"
                @keydown.escape="showSavePreset = false"
              />
              <button
                type="button"
                class="px-3 py-1.5 text-sm text-white rounded-lg transition-colors disabled:opacity-50"
                :class="saveBtnClass"
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

    <!-- Row 2: 변수 삽입 버튼 -->
    <div v-if="variables.length > 0" class="flex flex-wrap gap-1.5">
      <button
        v-for="v in variables"
        :key="v.var"
        type="button"
        @click="insertVar(v.var)"
        class="px-2 py-0.5 text-xs rounded border border-gray-200 dark:border-gray-600 transition-colors font-mono"
        :class="varChipClass"
        :title="v.desc"
      >{{ v.var }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue:    { type: String,  default: '' },
  variables:     { type: Array,   default: () => [] }, // [{var, desc}]
  builtinPresets:{ type: Array,   default: () => [] }, // [{label, pattern}]
  storageKey:    { type: String,  default: '' },        // localStorage key prefix
  accentColor:   { type: String,  default: 'blue' },    // 'blue' | 'purple' | 'indigo' | 'orange'
  placeholder:   { type: String,  default: '' },
})

const emit = defineEmits(['update:modelValue', 'preset-applied'])

// ── 색상 클래스 ──────────────────────────────────────────────
const focusRingClass = computed(() => {
  const m = { blue: 'focus:ring-2 focus:ring-blue-500', purple: 'focus:ring-2 focus:ring-purple-500', indigo: 'focus:ring-2 focus:ring-indigo-500', orange: 'focus:ring-2 focus:ring-orange-400' }
  return m[props.accentColor] ?? m.blue
})
const activeTextClass = computed(() => {
  const m = { blue: 'text-blue-500', purple: 'text-purple-500', indigo: 'text-indigo-500', orange: 'text-orange-500' }
  return m[props.accentColor] ?? m.blue
})
const varChipClass = computed(() => {
  const bg = { blue: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900 hover:text-blue-700 dark:hover:text-blue-300', purple: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-purple-100 dark:hover:bg-purple-900 hover:text-purple-700 dark:hover:text-purple-300', indigo: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 hover:text-indigo-700 dark:hover:text-indigo-300', orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50' }
  return bg[props.accentColor] ?? bg.blue
})
const savePresetBtnClass = computed(() => {
  const m = { blue: 'text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20', purple: 'text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20', indigo: 'text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20', orange: 'text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20' }
  return m[props.accentColor] ?? m.blue
})
const saveBtnClass = computed(() => {
  const m = { blue: 'bg-blue-600 hover:bg-blue-700', purple: 'bg-purple-600 hover:bg-purple-700', indigo: 'bg-indigo-600 hover:bg-indigo-700', orange: 'bg-orange-500 hover:bg-orange-600' }
  return m[props.accentColor] ?? m.blue
})

// ── 커서 추적 ────────────────────────────────────────────────
const inputRef = ref(null)
let _cursor = null

function saveCursor() {
  const el = inputRef.value
  if (el) _cursor = { start: el.selectionStart, end: el.selectionEnd }
}

function insertVar(v) {
  const el = inputRef.value
  const val = props.modelValue || ''
  const start = _cursor?.start ?? val.length
  const end   = _cursor?.end   ?? start
  const newVal = val.slice(0, start) + v + val.slice(end)
  emit('update:modelValue', newVal)
  _cursor = { start: start + v.length, end: start + v.length }
  nextTick(() => {
    if (el) {
      el.focus()
      el.setSelectionRange(start + v.length, start + v.length)
    }
  })
}

// ── 히스토리 ─────────────────────────────────────────────────
const HISTORY_KEY   = computed(() => props.storageKey ? `${props.storageKey}-patterns` : '')
const MAX_HISTORY   = 15

const patternHistory    = ref(props.storageKey ? JSON.parse(localStorage.getItem(`${props.storageKey}-patterns`) || '[]') : [])
const showHistoryDropdown = ref(false)
const historyContainerRef = ref(null)

function savePatternToHistory(pat) {
  if (!pat?.trim() || !HISTORY_KEY.value) return
  const arr = patternHistory.value.filter(p => p !== pat)
  arr.unshift(pat)
  patternHistory.value = arr.slice(0, MAX_HISTORY)
  localStorage.setItem(HISTORY_KEY.value, JSON.stringify(patternHistory.value))
}

function selectHistory(pat) {
  emit('update:modelValue', pat)
  showHistoryDropdown.value = false
  inputRef.value?.focus()
  emit('preset-applied', pat)
}

function removeHistory(i) {
  patternHistory.value.splice(i, 1)
  localStorage.setItem(HISTORY_KEY.value, JSON.stringify(patternHistory.value))
}

function clearHistory() {
  patternHistory.value = []
  if (HISTORY_KEY.value) localStorage.removeItem(HISTORY_KEY.value)
  showHistoryDropdown.value = false
}

// ── 커스텀 프리셋 ─────────────────────────────────────────────
const CUSTOM_PRESETS_KEY = computed(() => props.storageKey ? `${props.storageKey}-presets` : '')

const customPresets     = ref(props.storageKey ? JSON.parse(localStorage.getItem(`${props.storageKey}-presets`) || '[]') : [])
const showPresetDropdown  = ref(false)
const showSavePreset      = ref(false)
const savePresetName      = ref('')
const savePresetInputRef  = ref(null)
const presetContainerRef  = ref(null)

function saveCustomPresets() {
  if (CUSTOM_PRESETS_KEY.value) {
    localStorage.setItem(CUSTOM_PRESETS_KEY.value, JSON.stringify(customPresets.value))
  }
}

function removeCustomPreset(i) {
  customPresets.value.splice(i, 1)
  saveCustomPresets()
}

function confirmSavePreset() {
  const name = savePresetName.value.trim()
  if (!name || !props.modelValue?.trim()) return
  const existing = customPresets.value.findIndex(p => p.label === name)
  if (existing !== -1) {
    customPresets.value[existing].pattern = props.modelValue
  } else {
    customPresets.value.push({ label: name, pattern: props.modelValue })
  }
  saveCustomPresets()
  showSavePreset.value = false
  savePresetName.value = ''
}

function applyPreset(pat) {
  emit('update:modelValue', pat)
  showPresetDropdown.value = false
  showSavePreset.value = false
  emit('preset-applied', pat)
}

// ── 외부 클릭으로 드롭다운 닫기 ─────────────────────────────
function onDocClick(e) {
  if (historyContainerRef.value && !historyContainerRef.value.contains(e.target)) {
    showHistoryDropdown.value = false
  }
  if (presetContainerRef.value && !presetContainerRef.value.contains(e.target)) {
    showPresetDropdown.value = false
    showSavePreset.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick, true))
onUnmounted(() => document.removeEventListener('click', onDocClick, true))

// 부모가 직접 히스토리 저장을 트리거할 수 있도록 expose
defineExpose({ savePatternToHistory })
</script>
