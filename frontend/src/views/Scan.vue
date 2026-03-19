<template>
  <div class="p-4 sm:p-6 max-w-3xl">
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">{{ $t('scan.title') }}</h2>

    <!-- Add Folder -->
    <div class="bg-white dark:bg-gray-900 rounded-xl p-4 sm:p-5 mb-6 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-3">{{ $t('scan.addFolder') }}</h3>
      <div class="flex flex-col sm:flex-row gap-2">
        <input
          v-model="newPath"
          :placeholder="$t('scan.pathPlaceholder')"
          class="field flex-1"
          @keydown.enter="addFolder"
        />
        <input
          v-model="newName"
          :placeholder="$t('scan.namePlaceholder')"
          class="field sm:w-36"
        />
        <button
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
          @click="addFolder"
        >{{ $t('common.add') }}</button>
      </div>
    </div>

    <!-- Folder List -->
    <div class="bg-white dark:bg-gray-900 rounded-xl p-4 sm:p-5 mb-6 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-3">
        {{ $t('scan.folders', { n: folders.length }) }}
      </h3>
      <div v-if="folders.length" class="space-y-2">
        <div
          v-for="folder in folders"
          :key="folder.id"
          class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5"
        >
          <div class="min-w-0 flex-1 mr-3">
            <p class="text-sm text-gray-900 dark:text-white truncate">{{ folder.name || folder.path }}</p>
            <p v-if="folder.name" class="text-xs text-gray-500 truncate">{{ folder.path }}</p>
          </div>
          <button
            class="text-red-500 hover:text-red-400 text-xs transition-colors shrink-0"
            @click="removeFolder(folder.id)"
          >{{ $t('common.delete') }}</button>
        </div>
      </div>
      <p v-else class="text-sm text-gray-400 dark:text-gray-600">{{ $t('scan.noFolders') }}</p>
    </div>

    <!-- Scan Control -->
    <div class="bg-white dark:bg-gray-900 rounded-xl p-4 sm:p-5 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-4">{{ $t('scan.control') }}</h3>

      <div class="flex flex-wrap gap-3 mb-4">
        <button
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="scanning
            ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-500 text-white'"
          :disabled="scanning"
          @click="startScan"
        >
          <span v-if="scanning" class="flex items-center gap-2">
            <span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            {{ $t('scan.scanning') }}
          </span>
          <span v-else>{{ $t('scan.startScan') }}</span>
        </button>
        <button
          class="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-sm text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          @click="cleanup"
        >{{ $t('scan.cleanup') }}</button>
      </div>

      <!-- Result -->
      <div v-if="lastResult" class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 grid grid-cols-3 gap-3 text-center">
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ lastResult.scanned }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.scanned') }}</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-green-500">{{ lastResult.added }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.added') }}</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-blue-500">{{ lastResult.updated }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.updated') }}</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-400">{{ lastResult.skipped }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.skipped') }}</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-red-500">{{ lastResult.errors }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.errors') }}</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-gray-600 dark:text-gray-300">{{ lastResult.duration }}s</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ $t('scan.results.duration') }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { scanApi } from '../api'
import { useToastStore } from '../stores/toast.js'

const { t } = useI18n()
const toastStore = useToastStore()

const folders = ref([])
const newPath = ref('')
const newName = ref('')
const scanning = ref(false)
const lastResult = ref(null)

async function loadFolders() {
  const { data } = await scanApi.getFolders()
  folders.value = data
}

async function addFolder() {
  if (!newPath.value.trim()) return
  try {
    await scanApi.addFolder({ path: newPath.value.trim(), name: newName.value.trim() || undefined })
    newPath.value = ''
    newName.value = ''
    await loadFolders()
    toastStore.success(t('scan.toast.added'))
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  }
}

async function removeFolder(id) {
  if (!await toastStore.confirm(t('scan.toast.confirmDelete'))) return
  await scanApi.removeFolder(id)
  await loadFolders()
  toastStore.success(t('scan.toast.removed'))
}

async function startScan() {
  if (scanning.value) return
  scanning.value = true
  try {
    const { data } = await scanApi.startScan()
    lastResult.value = data
    toastStore.success(t('scan.toast.scanComplete', { added: data.added, updated: data.updated }))
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    scanning.value = false
  }
}

async function cleanup() {
  const { data } = await scanApi.cleanup()
  toastStore.success(t('scan.toast.cleanupComplete', { n: data.removed }))
}

onMounted(async () => {
  await loadFolders()
  const { data } = await scanApi.getStatus()
  lastResult.value = data.last_result
  scanning.value = data.running
})
</script>
