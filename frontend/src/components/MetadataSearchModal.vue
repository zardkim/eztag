<template>
  <div class="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-2xl shadow-2xl flex flex-col max-h-[92vh] sm:max-h-[90vh]">

      <!-- Header -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ $t('metaSearch.title') }}</h3>
        <button class="text-gray-400 hover:text-gray-900 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>

      <!-- Search Bar -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
        <div class="flex gap-2">
          <input
            v-model="query"
            class="field flex-1"
            :placeholder="$t('metaSearch.searchPlaceholder')"
            @keydown.enter="search"
          />
          <select v-model="searchType" class="field shrink-0">
            <option value="album">{{ $t('metaSearch.albumType') }}</option>
            <option value="track">{{ $t('metaSearch.trackType') }}</option>
          </select>
          <button
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60 shrink-0"
            :disabled="searching"
            @click="search"
          >{{ searching ? $t('common.searching') : $t('common.search') }}</button>
        </div>
        <p v-if="error" class="text-xs text-red-500 mt-2">{{ error }}</p>
      </div>

      <!-- Results -->
      <div class="flex-1 overflow-y-auto px-5 py-4">
        <!-- Album results -->
        <div v-if="searchType === 'album' && results.length">
          <p class="text-xs text-gray-500 mb-3">{{ $t('metaSearch.albumResultsHint', { n: results.length }) }}</p>
          <div class="space-y-2">
            <div
              v-for="item in results"
              :key="item.spotify_id"
              class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              @click="loadAlbumTracks(item)"
            >
              <img v-if="item.cover_url" :src="item.cover_url" class="w-12 h-12 rounded object-cover shrink-0" />
              <div v-else class="w-12 h-12 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center shrink-0 text-xl">💿</div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ item.album_title }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.album_artist }}{{ item.year ? ` · ${item.year}` : '' }}</p>
                <p class="text-xs text-gray-400 dark:text-gray-600">{{ $t('metaSearch.tracks', { n: item.total_tracks }) }}</p>
              </div>
              <span class="text-xs text-gray-400 shrink-0">{{ $t('metaSearch.selectArrow') }}</span>
            </div>
          </div>
        </div>

        <!-- Album track list -->
        <div v-if="albumTracks.length">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-500">{{ $t('metaSearch.trackList', { album: selectedAlbum?.album_title }) }}</p>
            <button
              class="text-xs text-blue-500 hover:text-blue-400 disabled:opacity-50"
              :disabled="searching"
              @click="applyAlbumAll"
            >{{ searching ? '적용 중...' : $t('metaSearch.applyAll') }}</button>
          </div>
          <div class="space-y-1">
            <div
              v-for="t in albumTracks"
              :key="t.spotify_id"
              class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded px-3 py-2 text-sm"
            >
              <div class="min-w-0 flex-1">
                <span class="text-gray-400 w-6 inline-block text-xs">{{ t.track_no }}.</span>
                <span class="text-gray-900 dark:text-white">{{ t.title }}</span>
                <span class="text-gray-500 text-xs ml-2">{{ t.artist }}</span>
              </div>
              <button class="text-xs text-blue-500 hover:text-blue-400 shrink-0 ml-2" @click="applyToMatchingTrack(t)">{{ $t('metaSearch.apply') }}</button>
            </div>
          </div>
        </div>

        <!-- Track results -->
        <div v-if="searchType === 'track' && results.length">
          <p class="text-xs text-gray-500 mb-3">{{ $t('metaSearch.trackResults', { n: results.length }) }}</p>
          <div class="space-y-2">
            <div
              v-for="item in results"
              :key="item.spotify_id"
              class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
            >
              <img v-if="item.cover_url" :src="item.cover_url" class="w-10 h-10 rounded object-cover shrink-0" />
              <div class="min-w-0 flex-1">
                <p class="text-sm text-gray-900 dark:text-white truncate">{{ item.title }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.artist }} · {{ item.album_title }}{{ item.year ? ` · ${item.year}` : '' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty -->
        <div v-if="!searching && results.length === 0 && !albumTracks.length && searched" class="text-center py-12 text-gray-400 dark:text-gray-600">
          <p>{{ $t('metaSearch.empty') }}</p>
          <p class="text-xs mt-1">{{ $t('metaSearch.emptyHint') }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-800 shrink-0 flex justify-end">
        <button class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white" @click="$emit('close')">{{ $t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { metadataApi } from '../api/metadata.js'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'

const { t } = useI18n()
const browserStore = useBrowserStore()
const toastStore = useToastStore()

const props = defineProps({ album: Object })
const emit = defineEmits(['close', 'applied'])

const query = ref('')
const searchType = ref('album')
const results = ref([])
const albumTracks = ref([])
const selectedAlbum = ref(null)
const searching = ref(false)
const searched = ref(false)
const error = ref('')

onMounted(() => {
  query.value = `${props.album?.album_artist || ''} ${props.album?.title || ''}`.trim()
})

async function search() {
  if (!query.value.trim()) return
  searching.value = true
  error.value = ''
  albumTracks.value = []
  selectedAlbum.value = null
  searched.value = true
  try {
    const { data } = await metadataApi.search({ q: query.value, type: searchType.value, provider: 'spotify' })
    results.value = data.results
  } catch (e) {
    error.value = e.response?.data?.detail || t('metaSearch.searchFailed')
    results.value = []
  } finally {
    searching.value = false
  }
}

async function loadAlbumTracks(albumItem) {
  selectedAlbum.value = albumItem
  results.value = []
  try {
    const { data } = await metadataApi.getAlbumTracks(albumItem.spotify_id)
    albumTracks.value = data.tracks
  } catch (e) {
    error.value = e.response?.data?.detail || t('metaSearch.tracksFailed')
  }
}

async function applyToMatchingTrack(spotifyTrack) {
  const localTrack = props.album?.tracks?.find(t => t.track_no === spotifyTrack.track_no && (t.disc_no || 1) === (spotifyTrack.disc_no || 1))
  if (!localTrack) {
    toastStore.warning(t('metaSearch.noLocalTrack', { n: spotifyTrack.track_no }))
    return
  }
  // 태그 적용 (Spotify cover_url 포함 — 단건은 백엔드에서 직접 처리)
  const res = await metadataApi.apply(localTrack.id, spotifyTrack)
  if (localTrack.file_path && res.data?.has_cover) {
    browserStore.updateFiles([localTrack.file_path], { has_cover: true })
  }
  browserStore.invalidateFilesCache()
  emit('applied')
}

function _normalizeTitle(s) {
  return (s || '').toLowerCase().replace(/[^a-z0-9가-힣]/g, '').trim()
}

async function applyAlbumAll() {
  if (!albumTracks.value.length || !props.album?.tracks?.length) return
  if (!await toastStore.confirm(t('metaSearch.confirmApplyAll', { n: albumTracks.value.length }))) return

  const localTracks = props.album.tracks
  const spotifyTracks = albumTracks.value
  const unmatched = []
  let applied = 0

  searching.value = true
  error.value = ''

  // 커버 URL은 첫 번째 트랙에서 추출 (앨범 공통)
  const coverUrl = spotifyTracks[0]?.cover_url || null

  try {
    for (const st of spotifyTracks) {
      // 1차: track_no + disc_no 매칭
      let local = localTracks.find(tr =>
        tr.track_no === st.track_no && (tr.disc_no || 1) === (st.disc_no || 1)
      )
      // 2차: 제목 정규화 매칭
      if (!local) {
        const stNorm = _normalizeTitle(st.title)
        local = localTracks.find(tr => _normalizeTitle(tr.title) === stNorm)
      }
      // 3차: 트랙 수가 같으면 순서(index) 매칭
      if (!local && spotifyTracks.length === localTracks.length) {
        local = localTracks[spotifyTracks.indexOf(st)]
      }

      if (local) {
        try {
          // 태그만 적용 (커버는 아래에서 1회 일괄 처리)
          const { cover_url: _, ...tagData } = st
          await metadataApi.apply(local.id, tagData)
          applied++
        } catch (e) {
          unmatched.push(`${st.track_no || '?'}. ${st.title} (저장 실패)`)
        }
      } else {
        unmatched.push(`${st.track_no || '?'}. ${st.title} (매칭 실패)`)
      }
    }

    // 커버 1회 다운로드 → 앨범 전체 적용
    if (coverUrl && props.album?.id && applied > 0) {
      try {
        const coverRes = await metadataApi.applyAlbumCover(props.album.id, coverUrl)
        // 각 트랙의 file-cover URL로 browse store 즉시 갱신
        if (coverRes.data?.ok && props.album?.tracks?.length) {
          const embeddedPaths = props.album.tracks
            .filter(t => t.file_path)
            .map(t => t.file_path)
          if (embeddedPaths.length) {
            browserStore.updateFiles(embeddedPaths, { has_cover: true })
          }
        }
      } catch (e) {
        unmatched.push(`앨범 커버 적용 실패: ${e.response?.data?.detail || e.message}`)
      }
    }
  } finally {
    searching.value = false
  }

  let msg = t('metaSearch.appliedCount', { n: applied })
  if (unmatched.length) msg += `\n미적용 ${unmatched.length}건:\n` + unmatched.join('\n')
  toastStore.info(msg, 6000)
  // Browse 뷰 파일 캐시 무효화 (다음 조회 시 서버에서 최신 커버 반영)
  browserStore.invalidateFilesCache()
  emit('applied')
  emit('close')
}
</script>
