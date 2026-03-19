<template>
  <div class="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-xl shadow-2xl overflow-hidden max-h-[95vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white dark:bg-gray-900 z-10">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ $t('trackEdit.title') }}</h3>
        <button class="text-gray-400 hover:text-gray-900 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>

      <form class="px-5 py-5 space-y-4" @submit.prevent="save">
        <div>
          <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.filePath') }}</label>
          <p class="text-xs text-gray-600 dark:text-gray-400 break-all bg-gray-50 dark:bg-gray-800 rounded px-2 py-1.5">{{ track.file_path }}</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.fields.title') }}</label>
            <input v-model="form.title" class="field w-full" required />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.artist') }}</label>
            <input v-model="form.artist" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.albumArtist') }}</label>
            <input v-model="form.album_artist" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.album') }}</label>
            <input v-model="form.album_title" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.fields.trackNo') }}</label>
            <input v-model.number="form.track_no" type="number" min="1" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.fields.discNo') }}</label>
            <input v-model.number="form.disc_no" type="number" min="1" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.year') }}</label>
            <input v-model.number="form.year" type="number" min="1900" max="2099" class="field w-full" />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">{{ $t('common.genre') }}</label>
            <input v-model="form.genre" class="field w-full" />
          </div>
        </div>

        <div>
          <label class="text-xs text-gray-500 block mb-1">{{ $t('trackEdit.fields.lyrics') }}</label>
          <textarea v-model="form.lyrics" rows="5" class="field w-full resize-none font-mono text-xs"></textarea>
        </div>

        <div class="flex justify-end gap-3 pt-2 pb-1">
          <button type="button" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white" @click="$emit('close')">{{ $t('common.cancel') }}</button>
          <button type="submit" class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60" :disabled="saving">
            {{ saving ? $t('common.saving') : $t('common.save') }}
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

const props = defineProps({ track: Object })
const emit = defineEmits(['close', 'saved'])
const toastStore = useToastStore()

const saving = ref(false)
const form = reactive({
  title: props.track.title,
  artist: props.track.artist || '',
  album_artist: props.track.album_artist || '',
  album_title: props.track.album_title || '',
  track_no: props.track.track_no,
  disc_no: props.track.disc_no,
  year: props.track.year,
  genre: props.track.genre || '',
  lyrics: props.track.lyrics || '',
})

async function save() {
  saving.value = true
  try {
    const { data } = await tracksApi.update(props.track.id, form)
    emit('saved', data)
  } catch (e) {
    toastStore.error(e.response?.data?.detail || '저장 실패')
  } finally {
    saving.value = false
  }
}
</script>
