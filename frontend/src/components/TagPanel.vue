<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ $t('browser.tagPanel') }}</h3>
      <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1 shrink-0" @click="$emit('close')">✕</button>
    </div>

    <!-- File info -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 shrink-0">
      <p class="text-xs font-medium text-gray-900 dark:text-white truncate">{{ file.filename }}</p>
      <p class="text-xs text-gray-400 mt-0.5 break-all">{{ file.path }}</p>
      <div class="flex gap-3 mt-1.5 text-xs text-gray-400">
        <span v-if="file.file_format">{{ file.file_format }}</span>
        <span v-if="file.duration">{{ formatDuration(file.duration) }}</span>
        <span v-if="file.bitrate">{{ file.bitrate }}kbps</span>
      </div>
    </div>

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <!-- Current metadata form -->
      <div v-for="field in textFields" :key="field.key">
        <label class="text-xs text-gray-500 block mb-1">{{ $t(field.labelKey) }}</label>
        <input v-model="form[field.key]" class="field w-full text-sm" />
      </div>

      <!-- 장르 (datalist) -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">{{ $t('common.genre') }}</label>
        <input v-model="form.genre" list="genre-datalist-tagpanel" class="field w-full text-sm" autocomplete="off" />
        <datalist id="genre-datalist-tagpanel">
          <option v-for="g in GENRES" :key="g" :value="g" />
        </datalist>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div v-for="field in numberFields" :key="field.key">
          <label class="text-xs text-gray-500 block mb-1">{{ $t(field.labelKey) }}</label>
          <input v-model.number="form[field.key]" type="number" :min="field.min" :max="field.max" class="field w-full text-sm" />
        </div>
      </div>

      <div>
        <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.fields.lyrics') }}</label>
        <textarea v-model="form.lyrics" rows="4" class="field w-full text-xs font-mono resize-none"></textarea>
      </div>

      <!-- Spotify search section -->
      <div ref="spotifySection" class="border-t border-gray-200 dark:border-gray-700 pt-3 mt-1">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Spotify</span>
          <button
            class="text-xs px-2.5 py-1 bg-green-600 hover:bg-green-500 disabled:opacity-60 text-white rounded-lg transition-colors"
            :disabled="spotifyLoading"
            @click="searchSpotify"
          >
            {{ spotifyLoading ? $t('common.searching') : '🔍 ' + $t('browser.spotifySearch') }}
          </button>
        </div>

        <p v-if="spotifyError" class="text-xs text-red-500 mb-2">{{ spotifyError }}</p>

        <div v-if="spotifyResults.length > 0" class="space-y-3">
          <SpotifyResultCard
            v-for="result in spotifyResults"
            :key="result.spotify_id"
            :result="result"
            :applied="appliedId === result.spotify_id"
            @apply="fillFromSpotify"
          />
        </div>
      </div>
    </div>

    <!-- Footer buttons -->
    <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-800 flex gap-2 shrink-0">
      <button
        class="flex-1 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg transition-colors"
        :disabled="saving"
        @click="save"
      >
        {{ saving ? $t('common.saving') : (workspaceItem ? '임시 저장' : $t('common.save')) }}
      </button>
      <button
        class="px-3 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white border border-gray-200 dark:border-gray-700 rounded-lg transition-colors"
        @click="reset"
      >
        {{ $t('common.cancel') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi, metadataApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { useWorkspaceStore } from '../stores/workspace.js'
import SpotifyResultCard from './SpotifyResultCard.vue'
import { GENRES } from '../constants/genres.js'
import { useToastStore } from '../stores/toast.js'

const { t } = useI18n()
const toastStore = useToastStore()
const props = defineProps({
  file: Object,
  focusSpotify: { type: Boolean, default: false },
  workspaceItem: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])
const spotifySection = ref(null)

const browserStore = useBrowserStore()
const workspaceStore = useWorkspaceStore()
const saving = ref(false)
const spotifyLoading = ref(false)
const spotifyResults = ref([])
const spotifyError = ref('')
const appliedId = ref(null)
const pendingCoverUrl = ref(null)

const textFields = [
  { key: 'title',        labelKey: 'common.title' },
  { key: 'artist',       labelKey: 'common.artist' },
  { key: 'album_artist', labelKey: 'common.albumArtist' },
  { key: 'album_title',  labelKey: 'common.album' },
]
const numberFields = [
  { key: 'track_no', labelKey: 'trackEdit.fields.trackNo', min: 1, max: 999 },
  { key: 'disc_no',  labelKey: 'trackEdit.fields.discNo',  min: 1, max: 99 },
  { key: 'year',     labelKey: 'common.year',              min: 1900, max: 2099 },
]

const form = reactive({})

function initForm() {
  Object.assign(form, {
    title: props.file.title || '',
    artist: props.file.artist || '',
    album_artist: props.file.album_artist || '',
    album_title: props.file.album_title || '',
    genre: props.file.genre || '',
    track_no: props.file.track_no || null,
    disc_no: props.file.disc_no || null,
    year: props.file.year || null,
    lyrics: props.file.lyrics || '',
  })
  spotifyResults.value = []
  spotifyError.value = ''
  appliedId.value = null
  pendingCoverUrl.value = null
}

initForm()
watch(() => props.file, initForm, { deep: true })
watch(() => props.focusSpotify, async (val) => {
  if (val) {
    await nextTick()
    spotifySection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}, { immediate: true })

function reset() {
  initForm()
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

async function searchSpotify() {
  spotifyLoading.value = true
  spotifyError.value = ''
  spotifyResults.value = []
  appliedId.value = null

  const q = [form.title, form.artist].filter(Boolean).join(' ').trim()
  if (!q) {
    spotifyError.value = t('browser.spotifyNoQuery')
    spotifyLoading.value = false
    return
  }
  try {
    const { data } = await metadataApi.search({ q, type: 'track', limit: 5 })
    spotifyResults.value = data.results
    if (data.results.length === 0) spotifyError.value = t('metaSearch.empty')
  } catch {
    spotifyError.value = t('metaSearch.searchFailed')
  } finally {
    spotifyLoading.value = false
  }
}

function fillFromSpotify(result) {
  if (result.title != null)        form.title        = result.title
  if (result.artist != null)       form.artist       = result.artist
  if (result.album_artist != null) form.album_artist = result.album_artist
  if (result.album_title != null)  form.album_title  = result.album_title
  if (result.year != null)         form.year         = result.year
  if (result.track_no != null)     form.track_no     = result.track_no
  if (result.disc_no != null)      form.disc_no      = result.disc_no
  if (result.genre != null)        form.genre        = result.genre
  pendingCoverUrl.value = result.cover_url || null
  appliedId.value = result.spotify_id
}

async function save() {
  saving.value = true
  try {
    if (props.workspaceItem) {
      // Workspace staging mode: stage tags without writing to file
      const tags = {}
      for (const [k, v] of Object.entries(form)) {
        if (v !== '' && v !== null && v !== undefined) tags[k] = v
      }
      await workspaceStore.stageTags(props.workspaceItem.id, tags)
      emit('saved')
    } else {
      // Normal browser mode: write directly to file
      const payload = { path: props.file.path }
      for (const [k, v] of Object.entries(form)) {
        if (v !== '' && v !== null && v !== undefined) payload[k] = v
      }
      const hadPendingCover = !!pendingCoverUrl.value
      if (pendingCoverUrl.value) {
        payload.cover_url = pendingCoverUrl.value
        await metadataApi.applyByPath(payload)
        pendingCoverUrl.value = null
      } else {
        await browseApi.writeTags(payload)
      }
      const fileUpdate = { path: props.file.path, ...form }
      if (hadPendingCover) fileUpdate.has_cover = true
      browserStore.updateFile(fileUpdate)
      emit('saved')
    }
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    saving.value = false
  }
}
</script>
