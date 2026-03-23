<template>
  <!-- Backdrop -->
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60" @click.self="onClose">
    <div class="w-full sm:max-w-md bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">

      <!-- Header -->
      <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('aiCover.modalTitle') }}</h3>
        <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1" @click="onClose">✕</button>
      </div>

      <div class="overflow-y-auto flex-1 p-4 space-y-4">

        <!-- Mood selector -->
        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ t('aiCover.moodLabel') }}
          </label>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <button
              v-for="m in moods"
              :key="m"
              class="px-3 py-1 text-xs rounded-full border transition-colors"
              :class="selectedMood === m
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-blue-400'"
              @click="selectedMood = m"
            >{{ t(`aiCover.moods.${m}`) }}</button>
          </div>
        </div>

        <!-- Hint input -->
        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ t('aiCover.hintLabel') }}
          </label>
          <input
            v-model="hint"
            type="text"
            :placeholder="t('aiCover.hintPlaceholder')"
            class="mt-1.5 w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Generate button -->
        <button
          class="w-full py-2.5 text-sm font-semibold rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white transition-colors"
          :disabled="generating"
          @click="generate"
        >
          {{ generating ? t('aiCover.generating') : t('aiCover.generateBtn') }}
        </button>

        <!-- Error -->
        <div v-if="errorMsg" class="text-xs text-red-500 dark:text-red-400 text-center">{{ errorMsg }}</div>

        <!-- Preview -->
        <div v-if="previewUrl">
          <div class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
            {{ t('aiCover.sectionPreview') }}
          </div>
          <div class="relative rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 aspect-square">
            <img :src="previewUrl" class="w-full h-full object-cover" />
          </div>

          <!-- Prompt used -->
          <details v-if="promptUsed" class="mt-2">
            <summary class="text-xs text-gray-400 cursor-pointer hover:text-gray-600 dark:hover:text-gray-200">
              {{ t('aiCover.promptLabel') }}
            </summary>
            <p class="mt-1 text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed break-words">{{ promptUsed }}</p>
          </details>

          <!-- Apply buttons -->
          <div class="mt-3 flex gap-2">
            <button
              v-if="filePath"
              class="flex-1 py-2 text-sm font-medium rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white transition-colors"
              :disabled="applying"
              @click="applyToFile"
            >{{ applying ? t('aiCover.applying') : t('aiCover.applyBtn') }}</button>
            <button
              v-if="folderPath"
              class="flex-1 py-2 text-sm font-medium rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white transition-colors"
              :disabled="applying"
              @click="applyToFolder"
            >{{ applying ? t('aiCover.applying') : t('aiCover.applyFolderBtn') }}</button>
            <button
              class="px-3 py-2 text-sm text-gray-500 hover:text-gray-800 dark:hover:text-white border border-gray-200 dark:border-gray-700 rounded-xl transition-colors"
              @click="discardPreview"
            >{{ t('aiCover.discardBtn') }}</button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { aiCoverApi } from '../api/index.js'

const props = defineProps({
  // 단일 파일 적용 시
  filePath: { type: String, default: null },
  // 폴더 전체 적용 시
  folderPath: { type: String, default: null },
  // 초기 트랙 메타데이터 (알아서 감지)
  trackInfo: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'applied'])
const { t } = useI18n()

const moods = ['energetic', 'emotional', 'retro', 'kpop', 'jazz', 'hiphop', 'drive', 'healing', 'dark']
const selectedMood = ref('energetic')
const hint = ref('')
const generating = ref(false)
const applying = ref(false)
const errorMsg = ref('')
const previewUrl = ref('')
const promptUsed = ref('')
const generationId = ref('')

async function generate() {
  generating.value = true
  errorMsg.value = ''
  previewUrl.value = ''
  promptUsed.value = ''
  generationId.value = ''

  try {
    const payload = {
      mood: selectedMood.value,
      hint: hint.value || undefined,
    }
    if (props.filePath) payload.path = props.filePath
    if (props.folderPath) {
      payload.folder_name = props.folderPath.split('/').filter(Boolean).pop()
    }
    // trackInfo fields
    const ti = props.trackInfo || {}
    if (ti.album_title) payload.album_title = ti.album_title
    if (ti.artist) payload.artist = ti.artist
    if (ti.genre) payload.genre = ti.genre
    if (ti.year) payload.year = ti.year

    const res = await aiCoverApi.generate(payload)
    generationId.value = res.data.generation_id
    previewUrl.value = res.data.preview_url
    promptUsed.value = res.data.prompt_used
  } catch (e) {
    const detail = e.response?.data?.detail || ''
    if (detail === 'ai_cover_not_configured') {
      errorMsg.value = t('aiCover.notConfigured')
    } else if (detail === 'ai_cover_disabled') {
      errorMsg.value = t('aiCover.disabled')
    } else {
      errorMsg.value = t('aiCover.generateFailed')
    }
  } finally {
    generating.value = false
  }
}

async function applyToFile() {
  if (!props.filePath || !generationId.value) return
  applying.value = true
  try {
    await aiCoverApi.apply(props.filePath, generationId.value)
    generationId.value = ''
    emit('applied')
    emit('close')
  } catch {
    errorMsg.value = t('aiCover.applyFailed')
  } finally {
    applying.value = false
  }
}

async function applyToFolder() {
  if (!props.folderPath || !generationId.value) return
  applying.value = true
  try {
    const res = await aiCoverApi.applyFolder(props.folderPath, generationId.value)
    const applied = res.data.applied || 0
    generationId.value = ''
    emit('applied', applied)
    emit('close')
  } catch {
    errorMsg.value = t('aiCover.applyFailed')
  } finally {
    applying.value = false
  }
}

async function discardPreview() {
  if (generationId.value) {
    await aiCoverApi.deletePreview(generationId.value).catch(() => {})
    generationId.value = ''
  }
  previewUrl.value = ''
  promptUsed.value = ''
}

function onClose() {
  discardPreview()
  emit('close')
}

onUnmounted(() => {
  if (generationId.value) {
    aiCoverApi.deletePreview(generationId.value).catch(() => {})
  }
})
</script>
