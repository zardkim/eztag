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
                <span class="text-lg shrink-0">{{ step.icon }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ t('wizard.step.' + step.id) }}</p>
                  <!-- 자동태그: 소스 선택 -->
                  <div v-if="step.id === 'autoTag' && step.enabled !== false" class="mt-1.5 flex flex-wrap gap-1">
                    <button
                      v-for="p in availableProviders"
                      :key="p.key"
                      class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="step.providerKey === p.key
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="step.providerKey = p.key"
                    >
                      <img :src="p.logo" :alt="p.label" class="w-3.5 h-3.5 rounded-full object-cover" />
                      {{ p.label }}
                    </button>
                  </div>
                  <!-- LRC: 소스 선택 -->
                  <div v-if="step.id === 'lrc' && step.enabled !== false" class="mt-1.5 flex gap-1">
                    <button
                      v-for="src in lrcSources"
                      :key="src.key"
                      class="px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="step.lrcSource === src.key
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="step.lrcSource = src.key"
                    >{{ src.label }}</button>
                  </div>
                  <!-- 파일명변경: 프리셋 선택 -->
                  <div v-if="step.id === 'rename' && step.enabled !== false" class="mt-1.5 flex flex-wrap gap-1">
                    <button
                      v-for="p in renamePresets"
                      :key="p.pattern"
                      class="px-2 py-0.5 rounded-full text-[11px] transition-colors"
                      :class="step.renamePattern === p.pattern
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'"
                      @click="step.renamePattern = p.pattern"
                    >{{ p.label }}</button>
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
                  class="flex items-center gap-2.5 px-3 py-2 rounded-xl transition-colors"
                  :class="stepStateClass(i)"
                >
                  <span class="text-base shrink-0">{{ stepStateIcon(i) }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium" :class="currentStep === i ? 'text-indigo-700 dark:text-indigo-300' : stepsDone[i] ? 'text-gray-500 dark:text-gray-400 line-through' : 'text-gray-700 dark:text-gray-300'">
                      {{ i + 1 }}. {{ t('wizard.step.' + step.id) }}
                    </p>
                    <p v-if="currentStep === i && stepStatus" class="text-xs text-indigo-500 dark:text-indigo-400 truncate mt-0.5">{{ stepStatus }}</p>
                  </div>
                </div>
              </div>

              <!-- 진행 바 -->
              <div class="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden mb-4">
                <div
                  class="h-full bg-indigo-500 rounded-full transition-all duration-500"
                  :style="{ width: progressPct + '%' }"
                />
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
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: Boolean,
  availableProviders: { type: Array, default: () => [] },
  currentStep: { type: Number, default: -1 },
  stepsDone: { type: Array, default: () => [] },
  stepStatus: { type: String, default: '' },
  waitingNext: Boolean,
  isFinished: Boolean,
  phase: { type: String, default: 'setup' },  // 'setup' | 'running'
  hidden: Boolean,
})

const emit = defineEmits(['update:modelValue', 'start', 'nextStep', 'skipStep', 'close'])

const lrcSources = [
  { key: 'alsong', label: '알송' },
  { key: 'bugs', label: 'Bugs' },
  { key: 'lrclib', label: 'LRCLIB' },
]

const renamePresets = computed(() => [
  { label: t('wizard.renameManual'),                     pattern: '' },
  { label: t('renameModal.presetTrackTitle'),            pattern: '%track% - %title%' },
  { label: t('renameModal.presetArtistTitle'),           pattern: '%artist% - %title%' },
  { label: t('renameModal.presetTrackArtistTitle'),      pattern: '%track% - %artist% - %title%' },
  { label: t('renameModal.presetArtistAlbumTrackTitle'), pattern: '%artist% - %album% - %track% - %title%' },
  { label: t('renameModal.presetDiscTrackTitle'),        pattern: '%disc%-%track% - %title%' },
])

const STORAGE_KEY = 'eztag-wizard-steps'

const DEFAULT_STEPS = [
  { id: 'autoTag',   icon: '🏷',  providerKey: '', enabled: true },
  { id: 'lrc',       icon: '🎵',  lrcSource: 'alsong', enabled: true },
  { id: 'youtube',   icon: '▶️',  enabled: true },
  { id: 'rename',    icon: '🔤',  renamePattern: '', enabled: true },
  { id: 'albumCard', icon: '🎴',  enabled: true },
]

// localStorage에서 저장된 단계 순서/설정 로드 (없으면 DEFAULT_STEPS)
function loadSteps() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (!Array.isArray(saved)) return DEFAULT_STEPS.map(s => ({ ...s }))
    // 저장된 순서 기준으로 재조합, DEFAULT에 없는 id 제거, DEFAULT에만 있는 id 뒤에 추가
    const result = []
    for (const s of saved) {
      const def = DEFAULT_STEPS.find(d => d.id === s.id)
      if (def) result.push({ ...def, enabled: s.enabled ?? true, providerKey: s.providerKey ?? def.providerKey, lrcSource: s.lrcSource ?? def.lrcSource, renamePattern: s.renamePattern ?? def.renamePattern })
    }
    for (const def of DEFAULT_STEPS) {
      if (!result.find(r => r.id === def.id)) result.push({ ...def })
    }
    return result
  } catch { return DEFAULT_STEPS.map(s => ({ ...s })) }
}

function saveSteps(stepList) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(
    stepList.map(s => ({ id: s.id, enabled: s.enabled ?? true, providerKey: s.providerKey, lrcSource: s.lrcSource, renamePattern: s.renamePattern }))
  ))
}

const steps = ref(loadSteps())
const activeSteps = ref([])  // 실행 중인 단계 (enabled만)

const enabledCount = computed(() => steps.value.filter(s => s.enabled !== false).length)

// 공급자 목록 업데이트 시 기본 providerKey 설정
watch(() => props.availableProviders, (providers) => {
  if (providers.length > 0) {
    const autoTagStep = steps.value.find(s => s.id === 'autoTag')
    if (autoTagStep && !autoTagStep.providerKey) {
      autoTagStep.providerKey = providers[0].key
    }
  }
}, { immediate: true })

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
  if (props.phase === 'running' && !props.isFinished) return  // 실행 중에는 닫기 막음
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
