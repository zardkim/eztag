import { defineStore } from 'pinia'
import { ref } from 'vue'
import { albumsApi, artistsApi, tracksApi } from '../api'

export const useLibraryStore = defineStore('library', () => {
  const albums = ref([])
  const totalAlbums = ref(0)
  const artists = ref([])
  const totalArtists = ref(0)
  const loading = ref(false)

  async function fetchAlbums(params = {}) {
    loading.value = true
    try {
      const { data } = await albumsApi.list(params)
      albums.value = data.items
      totalAlbums.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchArtists(params = {}) {
    loading.value = true
    try {
      const { data } = await artistsApi.list(params)
      artists.value = data.items
      totalArtists.value = data.total
    } finally {
      loading.value = false
    }
  }

  return { albums, totalAlbums, artists, totalArtists, loading, fetchAlbums, fetchArtists }
})
