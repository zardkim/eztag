<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="modelValue">
      <div v-show="!hidden" class="fixed inset-0 z-[300] flex items-end sm:items-center justify-center" @click.self="tryClose">
        <div class="absolute inset-0 bg-black/50" @click="tryClose" />
        <div class="relative bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-md max-h-[90vh] flex flex-col" @click.stop>
          <!-- 헤더 -->
          <div class="shrink-0 flex items-center justify-between px-5 pt-5 pb-4 border-b border-gray-100 dark:border-gray-800">
            <p class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span class="text-xl">🪄</span>{{ t('wizard.title') }}
            </p>
            <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-lg leading-none" @click="tryClose">✕</button>
          </div>

          <!-- 설정 모드 -->
          <template v-if="phase === 'setup'">
            <div class="flex-1 overflow-y-auto px-5 py-4 space-y-2">
              <p class="text-xs text-gray-400 mb-3">{{ t('wizard.setupHint') }}</p>

              <!-- 단계 목록 (순서 변경 가능) -->
              <div
                v-for="(step, i) in steps"
                :key="step.id"
                class="flex items-center gap-2 rounded-xl px-3 py-2.5 transition-colors"
                :class="step.enabled !== false ? 'bg-gray-50 dark:bg-gray-800' : 'bg-gray-50/50 dark:bg-gray-800/30 opacity-50'"
              >
                <!-- 번호 -->
                <span class="w-5 h-5 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold flex items-center justify-center shrink-0">{{ i + 1 }}</span>
                <!-- 아이콘 + 이름 -->
                <span class="text-lg shrink-0">{{ stepIcon(step.id) }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ t('wizard.step.' + step.id) }}</p>
                  <!-- 자동태그: 소스 다중선택 -->
                  <div v-if="step.id === 'autoTag' && step.enabled !== false" class="mt-1.5 flex flex-wrap gap-1">
                    <button
                      v-for="p in availableProviders"
                      :key="p.key"
                      class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="(step.providerKeys || []).includes(p.key)
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="toggleProviderKey(step, p.key); saveSteps()"
                    >
                      <img :src="p.logo" :alt="p.label" class="w-3.5 h-3.5 rounded-full object-cover" />
                      {{ p.label }}
                    </button>
                  </div>
                  <!-- LRC: 소스 단일선택 -->
                  <div v-if="step.id === 'lrc' && step.enabled !== false" class="mt-1.5 flex gap-1">
                    <button
                      v-for="src in lrcSources"
                      :key="src.key"
                      class="px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="(step.lrcSources || [])[0] === src.key
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="setLrcSource(step, src.key); saveSteps()"
                    >{{ src.label }}</button>
                  </div>
                  <!-- 파일명변경: 프리셋 선택 -->
                  <div v-if="step.id === 'rename' && step.enabled !== false" class="mt-1.5 flex flex-wrap gap-1">
                    <button
                      v-for="p in renamePresets"
                      :key="p.pattern"
                      class="px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="!isCustomRename(step) && step.renamePattern === p.pattern
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="step.renamePattern = p.pattern; saveSteps()"
                    >{{ p.label }}</button>
                    <button
                      class="px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="isCustomRename(step)
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="toggleCustomRename(step)"
                    >{{ $t('wizard.renameManual') }}</button>
                    <div v-if="isCustomRename(step)" class="w-full mt-1 space-y-1">
                      <TagVarInput
                        :model-value="step.renamePattern"
                        @update:model-value="v => { step.renamePattern = v; saveSteps() }"
                        :variables="RENAME_VARS_WITH_DESC"
                        :builtin-presets="RENAME_PRESETS"
                        storage-key="eztag-wizard-rename"
                        accent-color="orange"
                        :placeholder="$t('wizard.renameCustomPlaceholder')"
                      />
                      <p class="text-[10px] text-gray-400">{{ $t('wizard.renameCustomHint') }}</p>
                    </div>
                  </div>
                </div>
                <!-- 활성/비활성 토글 -->
                <button
                  class="shrink-0 w-9 h-5 rounded-full transition-colors relative"
                  :class="step.enabled !== false ? 'bg-indigo-500' : 'bg-gray-300 dark:bg-gray-600'"
                  @click="step.enabled = step.enabled === false ? true : false"
                >
                  <span
                    class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all"
                    :class="step.enabled !== false ? 'left-[18px]' : 'left-0.5'"
                  />
                </button>
                <!-- 위/아래 버튼 -->
                <div class="flex flex-col gap-0.5 shrink-0">
                  <button
                    class="w-6 h-5 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-20"
                    :disabled="i === 0"
                    @click="moveStep(i, -1)"
                  >▲</button>
                  <button
                    class="w-6 h-5 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-20"
                    :disabled="i === steps.length - 1"
                    @click="moveStep(i, 1)"
                  >▼</button>
                </div>
              </div>
            </div>

            <!-- 실행 버튼 -->
            <div class="shrink-0 px-5 pb-6 pt-3 border-t border-gray-100 dark:border-gray-800">
              <button
                class="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-semibold rounded-xl transition-colors"
                :disabled="enabledCount === 0"
                @click="startWizard"
              >🪄 {{ t('wizard.start') }}</button>
            </div>
          </template>

          <!-- 실행 모드 -->
          <template v-else-if="phase === 'running'">
            <div class="flex-1 overflow-y-auto px-5 py-4">
              <!-- 단계별 상태 -->
              <div class="space-y-2 mb-4">
                <div
                  v-for="(step, i) in activeSteps"
                  :key="step.id"
                  class="flex items-start gap-2.5 px-3 py-2 rounded-xl transition-colors"
                  :class="stepStateClass(i)"
                >
                  <span class="text-base shrink-0 mt-0.5">{{ stepStateIcon(i) }}</span>
                  <div class="flex-1 min-w-0">
                    <!-- 단계 이름 -->
                    <p class="text-sm font-medium" :class="currentStep === i ? 'text-indigo-700 dark:text-indigo-300' : stepsDone[i] ? 'text-gray-500 dark:text-gray-400 line-through' : 'text-gray-700 dark:text-gray-300'">
                      {{ i + 1 }}. {{ t('wizard.step.' + step.id) }}
                    </p>

                    <!-- 현재 실행 중인 단계 -->
                    <template v-if="currentStep === i">
                      <!-- 상세 진행 (LRC/YouTube: 미니 진행바 + 통계) -->
                      <template v-if="stepProgress && stepProgress.total > 0">
                        <p class="text-[11px] text-indigo-500 dark:text-indigo-400 mt-0.5">{{ stepStatus }}</p>
                        <div class="mt-1.5 space-y-1">
                          <!-- 미니 진행바 -->
                          <div class="h-1 bg-indigo-100 dark:bg-indigo-900/40 rounded-full overflow-hidden">
                            <div
                              class="h-full bg-indigo-400 rounded-full transition-all duration-200"
                              :style="{ width: (stepProgress.current / stepProgress.total * 100) + '%' }"
                            />
                          </div>
                          <!-- 통계 행 -->
                          <div class="flex items-center justify-between">
                            <span class="text-[10px] text-indigo-500 dark:text-indigo-400 font-mono tabular-nums">{{ stepProgress.current }}/{{ stepProgress.total }}</span>
                            <!-- LRC 통계 -->
                            <div v-if="stepProgress.type === 'lrc'" class="flex gap-2 text-[10px]">
                              <span class="text-green-600 dark:text-green-400">✅ {{ stepProgress.ok }}</span>
                              <span class="text-red-400 dark:text-red-400">❌ {{ stepProgress.notFound }}</span>
                              <span v-if="stepProgress.noSync" class="text-amber-500">⚠️ {{ stepProgress.noSync }}</span>
                            </div>
                            <!-- YouTube 통계 -->
                            <div v-if="stepProgress.type === 'youtube'" class="flex gap-2 text-[10px]">
                              <span class="text-green-600 dark:text-green-400">✅ {{ stepProgress.found }}</span>
                              <span v-if="stepProgress.current - stepProgress.found > 0" class="text-red-400">❌ {{ stepProgress.current - stepProgress.found }}</span>
                            </div>
                          </div>
                          <!-- 현재 파일명 -->
                          <p v-if="stepProgress.currentFile" class="text-[10px] text-gray-400 dark:text-gray-500 truncate">{{ stepProgress.currentFile }}</p>
                        </div>
                      </template>
                      <!-- 단순 상태 텍스트 (autoTag/rename/albumCard) -->
                      <p v-else-if="stepStatus" class="text-xs text-indigo-500 dark:text-indigo-400 truncate mt-0.5">{{ stepStatus }}</p>
                    </template>

                    <!-- 완료된 단계 결과 -->
                    <div v-if="stepsDone[i] && stepsResults[i]" class="flex flex-wrap gap-x-2 gap-y-0.5 mt-0.5">
                      <!-- LRC 완료 결과 -->
                      <template v-if="stepsResults[i].type === 'lrc'">
                        <span class="text-[10px] text-green-600 dark:text-green-400">✅ {{ stepsResults[i].ok }}</span>
                        <span v-if="stepsResults[i].notFound" class="text-[10px] text-red-400">❌ {{ stepsResults[i].notFound }}</span>
                        <span v-if="stepsResults[i].noSync" class="text-[10px] text-amber-500">⚠️ {{ stepsResults[i].noSync }}</span>
                      </template>
                      <!-- YouTube 완료 결과 -->
                      <template v-if="stepsResults[i].type === 'youtube'">
                        <span class="text-[10px] text-green-600 dark:text-green-400">✅ {{ stepsResults[i].found }}</span>
                        <span v-if="stepsResults[i].total - stepsResults[i].found > 0" class="text-[10px] text-red-400">❌ {{ stepsResults[i].total - stepsResults[i].found }}</span>
                      </template>
                      <!-- rename 완료 결과 -->
                      <template v-if="stepsResults[i].type === 'rename'">
                        <span class="text-[10px] text-green-600 dark:text-green-400">✅ {{ stepsResults[i].total }}개</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 전체 진행 바 + 현재 단계 문구 -->
              <div class="mb-4">
                <!-- 단계 문구 (소프트웨어 설치처럼 "(N/M) 단계명" 표시) -->
                <p class="text-sm font-medium text-indigo-600 dark:text-indigo-400 mb-2">
                  <template v-if="isFinished">✅ {{ t('wizard.done') }}</template>
                  <template v-else-if="currentStep >= 0 && activeSteps[currentStep]">
                    ({{ currentStep + 1 }}/{{ activeSteps.length }}) {{ t('wizard.progressLabel.' + activeSteps[currentStep].id, stepStatus || t('wizard.statusRunning')) }}
                  </template>
                  <template v-else-if="stepStatus">{{ stepStatus }}</template>
                </p>
                <!-- 진행바 + % -->
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-indigo-500 rounded-full transition-all duration-500"
                      :style="{ width: progressPct + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-400 tabular-nums font-mono w-8 text-right shrink-0">{{ progressPct }}%</span>
                </div>
              </div>

              <!-- 인터랙티브 단계: 완료 + 건너뛰기 버튼 -->
              <div v-if="waitingNext && !isFinished" class="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl px-4 py-3 text-center space-y-2">
                <p class="text-xs text-indigo-600 dark:text-indigo-400">{{ t('wizard.interactiveHint') }}</p>
                <div class="flex gap-2 justify-center">
                  <button
                    class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl transition-colors"
                    @click="$emit('nextStep')"
                  >{{ t('wizard.next') }} ▶</button>
                  <button
                    class="px-5 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm text-gray-600 dark:text-gray-300 rounded-xl transition-colors"
                    @click="$emit('skipStep')"
                  >{{ t('wizard.skip') }}</button>
                </div>
              </div>

              <!-- 진행 중 단계: 건너뛰기 버튼 -->
              <div v-else-if="!isFinished && currentStep >= 0" class="text-center">
                <button
                  class="px-4 py-1.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 rounded-lg transition-colors"
                  @click="$emit('skipStep')"
                >{{ t('wizard.skip') }}</button>
              </div>

              <!-- 완료 -->
              <div v-if="isFinished" class="text-center py-2">
                <p class="text-2xl mb-1">🎉</p>
                <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('wizard.done') }}</p>
                <button
                  class="mt-3 px-5 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 rounded-xl transition-colors"
                  @click="$emit('close')"
                >{{ t('common.close') }}</button>
              </div>
            </div>
          </template>
        </div>
      </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import TagVarInput from './TagVarInput.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: Boolean,
  availableProviders: { type: Array, default: () => [] },
  currentStep: { type: Number, default: -1 },
  stepsDone: { type: Array, default: () => [] },
  stepStatus: { type: String, default: '' },
  stepProgress: { type: Object, default: null },   // { type, current, total, ok, notFound, noSync, errors, found, currentFile }
  stepsResults: { type: Array, default: () => [] }, // 완료된 단계별 최종 결과
  waitingNext: Boolean,
  isFinished: Boolean,
  phase: { type: String, default: 'setup' },  // 'setup' | 'running'
  hidden: Boolean,
})

const emit = defineEmits(['update:modelValue', 'start', 'nextStep', 'skipStep', 'close', 'abort'])

const lrcSources = [
  { key: 'alsong', label: '알송' },
  { key: 'bugs', label: 'Bugs' },
  { key: 'lrclib', label: 'LRCLIB' },
]

const renamePresets = computed(() => [
  { label: t('renameModal.presetTrackTitle'),            pattern: '%track% - %title%' },
  { label: t('renameModal.presetArtistTitle'),           pattern: '%artist% - %title%' },
  { label: t('renameModal.presetTrackArtistTitle'),      pattern: '%track% - %artist% - %title%' },
  { label: t('renameModal.presetArtistAlbumTrackTitle'), pattern: '%artist% - %album% - %track% - %title%' },
  { label: t('renameModal.presetDiscTrackTitle'),        pattern: '%disc%-%track% - %title%' },
])

function toggleProviderKey(step, key) {
  const keys = step.providerKeys || []
  step.providerKeys = keys.includes(key) ? keys.filter(k => k !== key) : [...keys, key]
}

function setLrcSource(step, key) {
  step.lrcSources = [key]
}

function isCustomRename(step) {
  return !renamePresets.value.some(p => p.pattern === step.renamePattern)
}

function toggleCustomRename(step) {
  if (!isCustomRename(step)) {
    step.renamePattern = ''
  }
  saveSteps()
}

// 아이콘 맵 (emoji 렌더링 안정화)
function stepIcon(id) {
  const icons = {
    autoTag:   '🏷️',
    lrc:       '🎵',
    rename:    '🔤',
    youtube:   '▶️',
    albumCard: '🎴',
  }
  return icons[id] || '•'
}

// 파일명 변수 삽입
const RENAME_VARS_WITH_DESC = computed(() => [
  { var: '%title%',           desc: t('renameModal.varTitle') },
  { var: '%artist%',          desc: t('renameModal.varArtist') },
  { var: '%albumartist%',     desc: t('renameModal.varAlbumArtist') },
  { var: '%album%',           desc: t('renameModal.varAlbum') },
  { var: '$num(%track%,2)',   desc: t('renameModal.varTrackNum2') },
  { var: '$num(%track%,3)',   desc: t('renameModal.varTrackNum3') },
  { var: '%track%',           desc: t('renameModal.varTrack') },
  { var: '%totaltracks%',     desc: t('renameModal.varTotalTracks') },
  { var: '%disc%',            desc: t('renameModal.varDisc') },
  { var: '%year%',            desc: t('renameModal.varYear') },
  { var: '%genre%',           desc: t('renameModal.varGenre') },
  { var: '%publisher%',       desc: t('renameModal.varPublisher') },
  { var: '%_filename%',       desc: t('renameModal.varFilename') },
  { var: '%_ext%',            desc: t('renameModal.varExt') },
])

const RENAME_PRESETS = computed(() => [
  { label: t('renameModal.presetTrackTitle'),            pattern: '%track% - %title%' },
  { label: t('renameModal.presetArtistTitle'),           pattern: '%artist% - %title%' },
  { label: t('renameModal.presetTrackArtistTitle'),      pattern: '%track% - %artist% - %title%' },
  { label: t('renameModal.presetArtistAlbumTrackTitle'), pattern: '%artist% - %album% - %track% - %title%' },
  { label: t('renameModal.presetDiscTrackTitle'),        pattern: '%disc%-%track% - %title%' },
])

// insertRenameVar은 TagVarInput 내부에서 처리되므로 제거됨

const STORAGE_KEY = 'eztag-wizard-steps'

const DEFAULT_STEPS = [
  { id: 'autoTag',   icon: '🏷️', providerKeys: [], enabled: true },
  { id: 'lrc',       icon: '🎵',  lrcSources: ['alsong'], enabled: true },
  { id: 'youtube',   icon: '▶️',  enabled: true },
  { id: 'rename',    icon: '🔤',  renamePattern: '', enabled: true },
  { id: 'albumCard', icon: '🎴',  enabled: true },
]

function _toProviderKeys(s, def) {
  if (Array.isArray(s.providerKeys)) return s.providerKeys
  if (s.providerKey) return [s.providerKey]
  return def.providerKeys ? [...def.providerKeys] : []
}
function _toLrcSources(s, def) {
  if (Array.isArray(s.lrcSources)) return s.lrcSources
  if (s.lrcSource) return [s.lrcSource]
  return def.lrcSources ? [...def.lrcSources] : ['alsong']
}

// localStorage에서 저장된 단계 순서/설정 로드 (없으면 DEFAULT_STEPS)
function loadSteps() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (!Array.isArray(saved)) return DEFAULT_STEPS.map(s => ({ ...s, providerKeys: [...(s.providerKeys || [])], lrcSources: [...(s.lrcSources || [])] }))
    const result = []
    for (const s of saved) {
      const def = DEFAULT_STEPS.find(d => d.id === s.id)
      if (def) result.push({ ...def, enabled: s.enabled ?? true, providerKeys: _toProviderKeys(s, def), lrcSources: _toLrcSources(s, def), renamePattern: s.renamePattern ?? def.renamePattern })
    }
    for (const def of DEFAULT_STEPS) {
      if (!result.find(r => r.id === def.id)) result.push({ ...def, providerKeys: [...(def.providerKeys || [])], lrcSources: [...(def.lrcSources || [])] })
    }
    return result
  } catch { return DEFAULT_STEPS.map(s => ({ ...s, providerKeys: [...(s.providerKeys || [])], lrcSources: [...(s.lrcSources || [])] })) }
}

function saveSteps(stepList) {
  const list = stepList ?? steps.value
  localStorage.setItem(STORAGE_KEY, JSON.stringify(
    list.map(s => ({ id: s.id, enabled: s.enabled ?? true, providerKeys: s.providerKeys ?? [], lrcSources: s.lrcSources ?? [], renamePattern: s.renamePattern }))
  ))
}

const steps = ref(loadSteps())
const activeSteps = ref([])  // 실행 중인 단계 (enabled만)

const enabledCount = computed(() => steps.value.filter(s => s.enabled !== false).length)

// 다이얼로그가 열릴 때 저장된 설정 불러오기 (실행 중이면 유지)
watch(() => props.modelValue, (v) => {
  if (v && props.phase === 'setup') {
    steps.value = loadSteps()
    if (props.availableProviders.length > 0) {
      const autoTagStep = steps.value.find(s => s.id === 'autoTag')
      if (autoTagStep && !autoTagStep.providerKey) autoTagStep.providerKey = props.availableProviders[0].key
    }
  }
})

const progressPct = computed(() => {
  const total = activeSteps.value.length || steps.value.filter(s => s.enabled !== false).length
  const done = props.stepsDone.filter(Boolean).length
  if (props.isFinished) return 100
  if (props.currentStep < 0) return 0
  return Math.round((done / total) * 100)
})

function moveStep(i, dir) {
  const j = i + dir
  if (j < 0 || j >= steps.value.length) return
  const arr = [...steps.value]
  ;[arr[i], arr[j]] = [arr[j], arr[i]]
  steps.value = arr
}

function startWizard() {
  saveSteps(steps.value)
  const enabled = steps.value.filter(s => s.enabled !== false)
  activeSteps.value = enabled.map(s => ({ ...s }))
  emit('start', activeSteps.value)
}

function tryClose() {
  if (props.phase === 'running' && !props.isFinished) {
    emit('abort')  // 실행 중 닫기 → 중단 요청
    return
  }
  emit('close')
}

function stepStateClass(i) {
  if (props.currentStep === i) return 'bg-indigo-50 dark:bg-indigo-900/20'
  if (props.stepsDone[i]) return 'bg-gray-50 dark:bg-gray-800/50 opacity-60'
  return ''
}

function stepStateIcon(i) {
  if (props.stepsDone[i]) return '✅'
  if (props.currentStep === i) return '⏳'
  return activeSteps.value[i]?.icon ?? ''
}
</script>
