<template>
  <div class="p-4 sm:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('albums.title') }}</h2>
        <p class="text-sm text-gray-500 mt-0.5">{{ $t('albums.count', { n: total }) }}</p>
      </div>
      <input
        v-model="search"
        :placeholder="$t('albums.search')"
        class="field w-full sm:w-56"
        @input="onSearch"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Grid -->
    <div v-else-if="albums.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
      <RouterLink
        v-for="album in albums"
        :key="album.id"
        :to="`/albums/${album.id}`"
        class="group bg-white dark:bg-gray-900 rounded-lg overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors shadow-sm"
      >
        <div class="aspect-square bg-gray-100 dark:bg-gray-800 flex items-center justify-center relative overflow-hidden">
          <img
            v-if="album.cover_path"
            :src="`/covers/${album.cover_path}`"
            :alt="album.title"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <span v-else class="text-4xl opacity-30">💿</span>
        </div>
        <div class="p-3">
          <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ album.title }}</p>
          <p class="text-xs text-gray-500 truncate mt-0.5">{{ album.album_artist || $t('common.unknownArtist') }}</p>
          <p class="text-xs text-gray-400 dark:text-gray-600 mt-0.5">
            {{ $t('albums.tracks', { n: album.track_count }) }}{{ album.year ? ` · ${album.year}` : '' }}
          </p>
        </div>
      </RouterLink>
    </div>

    <!-- Empty -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-gray-600">
      <span class="text-5xl mb-3">💿</span>
      <p class="text-lg">{{ $t('albums.empty') }}</p>
      <p class="text-sm mt-1 text-center px-4">{{ $t('albums.emptyHint') }}</p>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex flex-wrap justify-center gap-2 mt-8">
      <button
        v-for="p in totalPages"
        :key="p"
        class="w-8 h-8 rounded text-sm font-medium transition-colors"
        :class="p === page
          ? 'bg-blue-600 text-white'
          : 'bg-gray-200 text-gray-600 hover:bg-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="goPage(p)"
      >{{ p }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { albumsApi } from '../api'

const albums = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const page = ref(1)
const pageSize = 48

const totalPages = computed(() => Math.ceil(total.value / pageSize))

let searchTimer = null

async function loadAlbums() {
  loading.value = true
  try {
    const { data } = await albumsApi.list({ search: search.value || undefined, page: page.value, page_size: pageSize })
    albums.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadAlbums() }, 300)
}

function goPage(p) { page.value = p; loadAlbums() }

onMounted(loadAlbums)
</script>
