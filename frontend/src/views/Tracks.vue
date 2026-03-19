<template>
  <div class="p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('tracks.title') }}</h2>
        <p class="text-sm text-gray-500 mt-0.5">{{ $t('tracks.count', { n: total }) }}</p>
      </div>
      <input
        v-model="search"
        :placeholder="$t('tracks.search')"
        class="field w-full sm:w-72"
        @input="onSearch"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else-if="tracks.length">
      <div class="overflow-x-auto -mx-4 sm:mx-0">
        <table class="w-full text-sm min-w-[480px]">
          <thead>
            <tr class="text-gray-500 text-xs border-b border-gray-200 dark:border-gray-800">
              <th class="pb-2 text-left px-4 sm:px-0">{{ $t('common.title') }}</th>
              <th class="pb-2 text-left hidden md:table-cell">{{ $t('common.artist') }}</th>
              <th class="pb-2 text-left hidden lg:table-cell">{{ $t('common.album') }}</th>
              <th class="w-12 pb-2 text-right hidden sm:table-cell">{{ $t('common.duration') }}</th>
              <th class="w-16 pb-2 text-right pr-4 sm:pr-0">{{ $t('tracks.headers.format') }}</th>
              <th class="w-16 pb-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="track in tracks"
              :key="track.id"
              class="group border-b border-gray-100 dark:border-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <td class="py-2.5 px-4 sm:px-0">
                <div class="flex items-center gap-2">
                  <span class="text-gray-900 dark:text-white truncate max-w-[140px] sm:max-w-xs">{{ track.title }}</span>
                  <span v-if="track.has_lyrics" class="text-xs text-purple-500 dark:text-purple-400">L</span>
                </div>
              </td>
              <td class="py-2.5 text-gray-600 dark:text-gray-400 hidden md:table-cell truncate max-w-xs">{{ track.artist }}</td>
              <td class="py-2.5 text-gray-500 hidden lg:table-cell truncate max-w-xs">{{ track.album_title }}</td>
              <td class="py-2.5 text-gray-400 dark:text-gray-600 text-right hidden sm:table-cell">{{ formatDuration(track.duration) }}</td>
              <td class="py-2.5 text-right pr-4 sm:pr-0">
                <span class="text-xs bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 px-1.5 py-0.5 rounded uppercase">{{ track.file_format }}</span>
              </td>
              <td class="py-2.5 text-right">
                <button
                  class="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white text-xs transition-all"
                  @click="editTrack(track)"
                >{{ $t('common.edit') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex flex-wrap justify-center gap-2 mt-6">
        <button
          v-for="p in pageNumbers"
          :key="p"
          class="w-8 h-8 rounded text-sm font-medium transition-colors"
          :class="p === page
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-600 hover:bg-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="goPage(p)"
        >{{ p }}</button>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-600">
      <span class="text-5xl mb-3">🎵</span>
      <p class="text-lg">{{ $t('tracks.empty') }}</p>
    </div>

    <TrackEditModal v-if="editingTrack" :track="editingTrack" @close="editingTrack = null" @saved="onTrackSaved" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { tracksApi } from '../api'
import TrackEditModal from '../components/TrackEditModal.vue'

const tracks = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const page = ref(1)
const pageSize = 100
const editingTrack = ref(null)

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const pageNumbers = computed(() => {
  const all = []
  for (let i = 1; i <= totalPages.value; i++) all.push(i)
  return all.slice(Math.max(0, page.value - 4), page.value + 3)
})

function formatDuration(sec) {
  if (!sec) return '-'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

let searchTimer = null

async function loadTracks() {
  loading.value = true
  try {
    const { data } = await tracksApi.list({ search: search.value || undefined, page: page.value, page_size: pageSize })
    tracks.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadTracks() }, 300)
}

function goPage(p) { page.value = p; loadTracks() }
function editTrack(track) { editingTrack.value = track }

function onTrackSaved(updated) {
  const idx = tracks.value.findIndex(t => t.id === updated.id)
  if (idx >= 0) tracks.value[idx] = updated
  editingTrack.value = null
}

onMounted(loadTracks)
</script>
