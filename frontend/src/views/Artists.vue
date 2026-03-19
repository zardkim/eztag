<template>
  <div class="p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('artists.title') }}</h2>
        <p class="text-sm text-gray-500 mt-0.5">{{ $t('artists.count', { n: total }) }}</p>
      </div>
      <input
        v-model="search"
        :placeholder="$t('artists.search')"
        class="field w-full sm:w-56"
        @input="onSearch"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else-if="artists.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
      <div
        v-for="artist in artists"
        :key="artist.id"
        class="bg-white dark:bg-gray-900 rounded-xl p-4 sm:p-5 flex flex-col items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer shadow-sm"
        @click="$router.push({ path: '/albums', query: { artist_id: artist.id } })"
      >
        <div class="w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-600 to-purple-700 rounded-full flex items-center justify-center text-xl sm:text-2xl font-bold text-white">
          {{ artist.name[0] }}
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white text-center truncate w-full">{{ artist.name }}</p>
        <p class="text-xs text-gray-500">{{ $t('artists.albums', { n: artist.album_count }) }}</p>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-600">
      <span class="text-5xl mb-3">🎤</span>
      <p class="text-lg">{{ $t('artists.empty') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { artistsApi } from '../api'

const artists = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
let searchTimer = null

async function loadArtists() {
  loading.value = true
  try {
    const { data } = await artistsApi.list({ search: search.value || undefined, page_size: 200 })
    artists.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadArtists, 300)
}

onMounted(loadArtists)
</script>
