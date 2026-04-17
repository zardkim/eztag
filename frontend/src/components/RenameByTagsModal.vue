<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-xl shadow-2xl w-full sm:max-w-3xl flex flex-col max-h-[92vh] sm:max-h-[90vh]">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
        <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('renameModal.title') }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1">✕</button>
      </div>

      <!-- 패턴 입력 -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
        <TagVarInput
          v-model="pattern"
          :variables="variables"
          :builtin-presets="builtinPresets"
          storage-key="eztag-rename"
          accent-color="blue"
          placeholder="%track% - %title%"
          ref="tagVarInputRef"
        />
      </div>

      <!-- 미리보기 테이블 -->
      <div class="flex-1 overflow-auto px-5 py-3">
        <div v-if="!pattern" class="text-center text-sm text-gray-400 py-8">{{ t('renameModal.patternHint') }}</div>
        <div v-else-if="previewLoading" class="text-center text-sm text-gray-400 py-8">{{ t('common.loading') }}…</div>
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
            :disabled="okCount === 0 || applying || previewLoading"
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import TagVarInput from './TagVarInput.vue'

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

const tagVarInputRef = ref(null)

// ── 패턴 상태 ─────────────────────────────────────────────
const initHistory = JSON.parse(localStorage.getItem('eztag-rename-patterns') || '[]')
const pattern = ref(initHistory[0] || '%track% - %title%')
const applying = ref(false)
const previewLoading = ref(false)

// ── 서버 기반 미리보기 ────────────────────────────────────
const previewRows = ref([])

let _previewTimer = null
async function loadPreview() {
  if (!pattern.value || !props.files.length) {
    previewRows.value = []
    return
  }
  previewLoading.value = true
  try {
    const paths = props.files.map(f => f.path)
    const res = await browseApi.renameByTagsPreview(paths, pattern.value)
    previewRows.value = res.data.results.map(r => ({
      ...r,
      same: !r.error && r.new_name === r.old_name,
    }))
  } catch (e) {
    console.error('[RenameByTagsModal] preview error:', e)
    previewRows.value = props.files.map(f => ({
      path: f.path,
      old_name: f._filename + (f._ext ? '.' + f._ext : ''),
      new_name: null,
      conflict: false,
      error: String(e),
      same: false,
    }))
  } finally {
    previewLoading.value = false
  }
}

function schedulePreview() {
  clearTimeout(_previewTimer)
  _previewTimer = setTimeout(loadPreview, 300)
}

watch(pattern, schedulePreview)

const okCount = computed(() => previewRows.value.filter(r => !r.error && !r.conflict && !r.same).length)
const conflictCount = computed(() => previewRows.value.filter(r => r.conflict).length)
const skipCount = computed(() => previewRows.value.filter(r => r.error).length)
const sameCount = computed(() => previewRows.value.filter(r => r.same).length)

async function applyRename() {
  if (okCount.value === 0 || applying.value) return
  applying.value = true
  try {
    const paths = previewRows.value.filter(r => !r.error && !r.conflict && !r.same).map(r => r.path)
    const res = await browseApi.renameByTags(paths, pattern.value)
    tagVarInputRef.value?.savePatternToHistory(pattern.value)
    emit('renamed', res.data)
  } catch (e) {
    console.error('[RenameByTagsModal] apply error:', e)
  } finally {
    applying.value = false
  }
}

onMounted(() => loadPreview())
onUnmounted(() => clearTimeout(_previewTimer))
</script>
