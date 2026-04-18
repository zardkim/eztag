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
        <TagVarInput
          v-model="pattern"
          :variables="variables"
          :builtin-presets="builtinPresets"
          storage-key="eztag-tagfromname"
          accent-color="purple"
          :placeholder="t('tagFromName.patternPlaceholder')"
          ref="tagVarInputRef"
          @preset-applied="previewRows = []"
        />
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
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import TagVarInput from './TagVarInput.vue'

const { t } = useI18n()

const props = defineProps({
  files: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'tagged'])

const builtinPresets = computed(() => [
  { label: t('tagFromName.presetTrackTitle'),         pattern: '%track% - %title%' },
  { label: t('tagFromName.presetArtistTitle'),        pattern: '%artist% - %title%' },
  { label: t('tagFromName.presetTrackArtistTitle'),   pattern: '%track% - %artist% - %title%' },
  { label: t('tagFromName.presetDiscTrackTitle'),     pattern: '%disc%-%track% - %title%' },
  { label: t('tagFromName.presetArtistAlbumTitle'),   pattern: '%artist% - %album% - %title%' },
])

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

const selectedFields = ref(fieldOptions.value.map(f => f.key))

const tagVarInputRef = ref(null)
const initHistory = JSON.parse(localStorage.getItem('eztag-tagfromname-patterns') || '[]')
const pattern = ref(initHistory[0] || '%track% - %title%')

// 패턴 변경 시 미리보기 결과 초기화 (사용자가 직접 다시 미리보기 누르도록)
watch(pattern, () => { previewRows.value = [] })

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
    tagVarInputRef.value?.savePatternToHistory(pattern.value)
    emit('tagged', res.data)
  } catch (e) {
    console.error('[TagFromNameModal] apply error:', e)
  } finally {
    applying.value = false
  }
}
</script>
