<template>
  <div class="flex flex-col bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
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

    <!-- 저장 / 취소 버튼 -->
    <div class="px-4 py-2.5 border-b border-gray-200 dark:border-gray-800 flex gap-2">
      <button
        class="flex-1 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg transition-colors"
        :disabled="saving"
        @click="save"
      >{{ saving ? $t('common.saving') : $t('common.save') }}</button>
      <button
        class="px-3 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white border border-gray-200 dark:border-gray-700 rounded-lg transition-colors"
        @click="reset"
      >{{ $t('common.cancel') }}</button>
    </div>

    <!-- Scrollable content -->
    <div class="px-4 py-3 space-y-3">
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

      <!-- 타이틀곡 / YouTube (DB 전용) -->
      <div class="border-t border-gray-200 dark:border-gray-700 pt-3 mt-1">
        <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-2">{{ $t('tagPanel.sectionMv') }}</span>

        <!-- 타이틀곡 토글 -->
        <label class="flex items-center gap-2 cursor-pointer mb-3">
          <div
            class="relative w-9 h-5 rounded-full transition-colors shrink-0"
            :class="isTitleTrack ? 'bg-orange-500' : 'bg-gray-300 dark:bg-gray-600'"
            @click="isTitleTrack = !isTitleTrack"
          >
            <span
              class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
              :class="isTitleTrack ? 'translate-x-4' : 'translate-x-0'"
            ></span>
          </div>
          <span class="text-xs text-gray-700 dark:text-gray-300">{{ $t('tagPanel.titleTrack') }}</span>
          <span v-if="isTitleTrack" class="text-[10px] font-bold text-orange-500 bg-orange-50 dark:bg-orange-900/20 px-1.5 py-0.5 rounded">{{ $t('tagPanel.titleBadge') }}</span>
        </label>

        <!-- YouTube URL + 자동 검색 -->
        <label class="text-xs text-gray-500 block mb-1">{{ $t('tagPanel.ytUrlLabel') }}</label>
        <div class="flex gap-1.5 mb-1">
          <input v-model="youtubeUrl" class="field flex-1 text-sm min-w-0" placeholder="https://youtu.be/..." />
          <button
            class="shrink-0 px-2.5 py-1 text-xs font-medium bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1"
            :disabled="ytSearchLoading"
            @click="searchYoutube"
            title="YouTube 자동 검색"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/></svg>
            {{ ytSearchLoading ? '...' : $t('tagPanel.ytSearch') }}
          </button>
        </div>

        <!-- 검색 오류 -->
        <p v-if="ytSearchError" class="text-[11px] text-red-500 mb-2">{{ ytSearchError }}</p>

        <!-- 검색 결과 -->
        <div v-if="ytSearchResults.length" class="space-y-1.5 mb-2">
          <div
            v-for="item in ytSearchResults"
            :key="item.video_id"
            class="flex items-center gap-2 p-1.5 rounded-lg border border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
            @click="selectYoutubeResult(item)"
          >
            <img v-if="item.thumbnail" :src="item.thumbnail" class="w-14 h-10 object-cover rounded shrink-0" />
            <div class="min-w-0 flex-1">
              <p class="text-xs font-medium text-gray-800 dark:text-gray-200 line-clamp-2 leading-tight">{{ item.title }}</p>
              <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ item.channel }}</p>
            </div>
          </div>
        </div>

        <!-- 현재 선택된 URL 미리보기 -->
        <div v-if="youtubeUrl" class="mb-2">
          <a :href="youtubeUrl" target="_blank" class="text-[11px] text-blue-500 hover:underline truncate block">{{ youtubeUrl }}</a>
        </div>

        <button
          class="w-full py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors disabled:opacity-50"
          :disabled="trackInfoSaving"
          @click="saveTrackInfo"
        >{{ trackInfoSaving ? $t('tagPanel.ytSaving') : $t('tagPanel.ytSaveBtn') }}</button>
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

  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi, metadataApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { useHistoryStore } from '../stores/history.js'
import SpotifyResultCard from './SpotifyResultCard.vue'
import { GENRES } from '../constants/genres.js'
import { useToastStore } from '../stores/toast.js'

const { t } = useI18n()
const toastStore = useToastStore()
const props = defineProps({
  file: Object,
  focusSpotify: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'saved'])
const spotifySection = ref(null)

const browserStore = useBrowserStore()
const historyStore = useHistoryStore()
const saving = ref(false)
const spotifyLoading = ref(false)
const spotifyResults = ref([])
const spotifyError = ref('')
const appliedId = ref(null)
const pendingCoverUrl = ref(null)

// 타이틀곡 / YouTube (DB 전용 필드)
const isTitleTrack = ref(false)
const youtubeUrl = ref('')
const trackInfoSaving = ref(false)
const ytSearchLoading = ref(false)
const ytSearchResults = ref([])
const ytSearchError = ref('')

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
  isTitleTrack.value = !!props.file.is_title_track
  youtubeUrl.value = props.file.youtube_url || ''
  ytSearchResults.value = []
  ytSearchError.value = ''
  spotifyResults.value = []
  spotifyError.value = ''
  appliedId.value = null
  pendingCoverUrl.value = null
}

async function saveTrackInfo() {
  trackInfoSaving.value = true
  try {
    const { data } = await browseApi.setTrackInfo({
      path: props.file.path,
      is_title_track: isTitleTrack.value,
      youtube_url: youtubeUrl.value,
    })
    browserStore.updateFile({
      path: props.file.path,
      is_title_track: data.is_title_track,
      youtube_url: data.youtube_url,
    })
    toastStore.success(t('tagPanel.ytSaved'))
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    trackInfoSaving.value = false
  }
}

async function searchYoutube() {
  const artist = form.artist || form.album_artist || ''
  const title = form.title || ''
  if (!artist && !title) return
  ytSearchLoading.value = true
  ytSearchResults.value = []
  ytSearchError.value = ''
  try {
    const { data } = await browseApi.searchYoutubeMV(artist, title)
    ytSearchResults.value = data.results
    if (!data.results.length) ytSearchError.value = t('tagPanel.ytNoResults')
  } catch (e) {
    if (e.response?.data?.detail === 'youtube_not_configured') {
      ytSearchError.value = t('tagPanel.ytNoApiKey')
    } else {
      ytSearchError.value = e.response?.data?.detail || t('tagPanel.ytSearchFailed')
    }
  } finally {
    ytSearchLoading.value = false
  }
}

function selectYoutubeResult(item) {
  youtubeUrl.value = item.url
  ytSearchResults.value = []
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
    // 변경 전 스냅샷 (히스토리용)
    const tagFields = Object.keys(form)
    const before = Object.fromEntries(tagFields.map(k => [k, props.file[k] ?? null]))

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

    // 전역 히스토리 등록
    const after = Object.fromEntries(tagFields.map(k => [k, form[k] ?? null]))
    historyStore.push({
      label: t('tagPanel.historyLabel', { filename: props.file.filename }),
      ops: [{ path: props.file.path, before, after }],
    })

    emit('saved')
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    saving.value = false
  }
}
</script>
