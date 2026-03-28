<template>
  <div v-if="album" class="flex flex-col h-full">
    <!-- Album Header -->
    <div class="bg-gradient-to-b from-gray-200 to-gray-50 dark:from-gray-800 dark:to-gray-950 p-4 sm:p-8 flex flex-col sm:flex-row gap-4 sm:gap-6 items-center sm:items-end">
      <div class="w-32 h-32 sm:w-40 sm:h-40 shrink-0 bg-gray-300 dark:bg-gray-700 rounded-xl overflow-hidden shadow-2xl flex items-center justify-center relative">
        <img
          v-if="album.cover_path"
          :src="`/covers/${album.cover_path}`"
          class="w-full h-full object-cover"
        />
        <label v-else class="cursor-pointer flex flex-col items-center gap-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors">
          <span class="text-4xl sm:text-5xl">💿</span>
          <span class="text-xs">{{ $t('albumDetail.coverUpload') }}</span>
          <input type="file" accept="image/*" class="hidden" @change="uploadCover" />
        </label>
        <label v-if="album.cover_path" class="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity cursor-pointer flex items-center justify-center text-xs text-white">
          {{ $t('albumDetail.coverChange') }}
          <input type="file" accept="image/*" class="hidden" @change="uploadCover" />
        </label>
      </div>
      <div class="flex-1 min-w-0 text-center sm:text-left">
        <p class="text-xs text-gray-500 uppercase tracking-widest mb-1">{{ $t('albumDetail.album') }}</p>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white truncate">{{ album.title }}</h1>
        <p class="text-gray-600 dark:text-gray-300 mt-1">{{ album.album_artist || $t('common.unknownArtist') }}</p>
        <p class="text-sm text-gray-500 mt-1">
          {{ $t('albumDetail.tracks', { n: album.track_count }) }}{{ album.year ? ` · ${album.year}` : '' }}{{ album.genre ? ` · ${album.genre}` : '' }}
        </p>
        <div class="flex flex-wrap gap-2 mt-3">
          <button
            class="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded-lg transition-colors"
            @click="openMetaSearch"
          >{{ $t('albumDetail.metaSearch') }}</button>
          <button
            class="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
            :disabled="exportingHtml"
            @click="exportHtml"
          >
            <span>🎴</span>
            <span>{{ exportingHtml ? $t('albumDetail.exporting') : $t('albumDetail.exportHtml') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Edit Bar -->
    <div v-if="selected.size > 0" class="bg-blue-50 dark:bg-blue-900/50 border-b border-blue-200 dark:border-blue-700 px-4 sm:px-6 py-3 flex items-center gap-4">
      <span class="text-sm text-blue-700 dark:text-blue-200">{{ $t('albumDetail.selected', { n: selected.size }) }}</span>
      <button class="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded" @click="openBatchEdit">
        {{ $t('albumDetail.batchEdit') }}
      </button>
      <button class="text-xs text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white ml-auto" @click="selected.clear()">
        {{ $t('albumDetail.clearSelect') }}
      </button>
    </div>

    <!-- Track List -->
    <div class="flex-1 overflow-auto px-2 sm:px-8 py-4">
      <div class="overflow-x-auto">
        <table class="w-full text-sm min-w-[400px]">
          <thead>
            <tr class="text-gray-500 text-xs border-b border-gray-200 dark:border-gray-800">
              <th class="w-8 pb-2 text-left">
                <input type="checkbox" class="rounded" @change="toggleAll" :checked="allSelected" />
              </th>
              <th class="w-8 pb-2 text-left">#</th>
              <th class="pb-2 text-left">{{ $t('common.title') }}</th>
              <th class="pb-2 text-left hidden md:table-cell">{{ $t('common.artist') }}</th>
              <th class="w-16 pb-2 text-right hidden sm:table-cell">{{ $t('common.duration') }}</th>
              <th class="w-12 pb-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="track in album.tracks"
              :key="track.id"
              class="group border-b border-gray-100 dark:border-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              :class="{ 'bg-gray-50 dark:bg-gray-800/30': selected.has(track.id) }"
            >
              <td class="py-2.5 pr-2">
                <input type="checkbox" class="rounded" :checked="selected.has(track.id)" @change="toggleSelect(track.id)" />
              </td>
              <td class="py-2.5 text-gray-400 dark:text-gray-600 pr-3">{{ track.track_no ?? '-' }}</td>
              <td class="py-2.5">
                <div class="flex items-center gap-2">
                  <span class="text-gray-900 dark:text-white truncate max-w-[140px] sm:max-w-xs">{{ track.title }}</span>
                  <span v-if="track.has_lyrics" class="text-xs text-purple-500 dark:text-purple-400" :title="$t('albumDetail.hasLyrics')">L</span>
                </div>
              </td>
              <td class="py-2.5 text-gray-600 dark:text-gray-400 hidden md:table-cell truncate max-w-xs">{{ track.artist }}</td>
              <td class="py-2.5 text-gray-400 dark:text-gray-600 text-right hidden sm:table-cell">{{ formatDuration(track.duration) }}</td>
              <td class="py-2.5 text-right">
                <button
                  class="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-all text-xs"
                  @click="editTrack(track)"
                >{{ $t('albumDetail.edit') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <TrackEditModal v-if="editingTrack" :track="editingTrack" @close="editingTrack = null" @saved="onTrackSaved" />
    <BatchEditModal v-if="showBatchEdit" :track-ids="[...selected]" @close="showBatchEdit = false" @saved="onBatchSaved" />
    <MetadataSearchModal v-if="showMetaSearch" :album="album" @close="showMetaSearch = false" @applied="loadAlbum" />
  </div>

  <div v-else-if="loading" class="flex justify-center py-20">
    <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { albumsApi, coversApi } from '../api'
import { downloadBlob } from '../utils/download.js'
import TrackEditModal from '../components/TrackEditModal.vue'
import BatchEditModal from '../components/BatchEditModal.vue'
import MetadataSearchModal from '../components/MetadataSearchModal.vue'

const route = useRoute()
const album = ref(null)
const loading = ref(false)
const selected = ref(new Set())
const editingTrack = ref(null)
const showBatchEdit = ref(false)
const showMetaSearch = ref(false)
const exportingHtml = ref(false)

function openMetaSearch() { showMetaSearch.value = true }

async function exportHtml() {
  if (exportingHtml.value || !album.value) return
  exportingHtml.value = true
  try {
    const { data } = await albumsApi.exportHtml(album.value.id)
    const name = `${album.value.title || 'album'} - ${album.value.album_artist || 'unknown'}.html`
    downloadBlob(data, name)
  } catch (e) {
    console.error('exportHtml error:', e)
  } finally {
    exportingHtml.value = false
  }
}

const allSelected = computed(() => album.value && selected.value.size === album.value.tracks.length)

function formatDuration(sec) {
  if (!sec) return '-'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function toggleSelect(id) {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}

function toggleAll(e) {
  selected.value = e.target.checked
    ? new Set(album.value.tracks.map(t => t.id))
    : new Set()
}

function editTrack(track) { editingTrack.value = track }
function openBatchEdit() { showBatchEdit.value = true }

async function loadAlbum() {
  loading.value = true
  try {
    const { data } = await albumsApi.get(route.params.id)
    album.value = data
  } finally {
    loading.value = false
  }
}

async function uploadCover(e) {
  const file = e.target.files[0]
  if (!file) return
  await coversApi.uploadAlbumCover(album.value.id, file)
  await loadAlbum()
}

function onTrackSaved(updated) {
  const idx = album.value.tracks.findIndex(t => t.id === updated.id)
  if (idx >= 0) album.value.tracks[idx] = updated
  editingTrack.value = null
}

function onBatchSaved() {
  showBatchEdit.value = false
  selected.value = new Set()
  loadAlbum()
}

onMounted(loadAlbum)
</script>
