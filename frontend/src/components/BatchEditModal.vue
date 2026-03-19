<template>
  <div class="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-lg shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white dark:bg-gray-900 z-10">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ $t('batchEdit.title', { n: trackIds.length }) }}</h3>
        <button class="text-gray-400 hover:text-gray-900 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>

      <form class="px-5 py-5 space-y-4" @submit.prevent="save">
        <p class="text-xs text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/30 rounded px-3 py-2">{{ $t('batchEdit.hint') }}</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.artist') }}</label>
            <input v-model="form.artist" class="field w-full" :placeholder="$t('common.noChange')" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.albumArtist') }}</label>
            <input v-model="form.album_artist" class="field w-full" :placeholder="$t('common.noChange')" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.album') }}</label>
            <input v-model="form.album_title" class="field w-full" :placeholder="$t('common.noChange')" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.genre') }}</label>
            <input v-model="form.genre" class="field w-full" :placeholder="$t('common.noChange')" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.year') }}</label>
            <input v-model.number="form.year" type="number" min="1900" max="2099" class="field w-full" :placeholder="$t('common.noChange')" />
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-2 pb-1">
          <button type="button" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white" @click="$emit('close')">{{ $t('common.cancel') }}</button>
          <button type="submit" class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60" :disabled="saving">
            {{ saving ? $t('common.saving') : $t('batchEdit.apply') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { tracksApi } from '../api'
import { useToastStore } from '../stores/toast.js'

const props = defineProps({ trackIds: Array })
const emit = defineEmits(['close', 'saved'])
const toastStore = useToastStore()

const saving = ref(false)
const form = reactive({ artist: '', album_artist: '', album_title: '', genre: '', year: null })

async function save() {
  const updates = {}
  if (form.artist) updates.artist = form.artist
  if (form.album_artist) updates.album_artist = form.album_artist
  if (form.album_title) updates.album_title = form.album_title
  if (form.genre) updates.genre = form.genre
  if (form.year) updates.year = form.year

  if (!Object.keys(updates).length) return

  saving.value = true
  try {
    await tracksApi.batchUpdate({ track_ids: props.trackIds, updates })
    emit('saved')
  } catch (e) {
    toastStore.error(e.response?.data?.detail || '저장 실패')
  } finally {
    saving.value = false
  }
}
</script>
