<template>
  <div class="fixed inset-0 bg-black/60 z-[300] flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-xl shadow-2xl flex flex-col max-h-[80vh]">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ folderMode ? $t('picker.titleFolder') : $t('picker.titleFile') }}</h3>
        <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>

      <!-- Breadcrumb -->
      <div class="px-3 py-2 flex items-center gap-1 text-xs text-gray-500 border-b border-gray-100 dark:border-gray-800 shrink-0 overflow-x-auto scrollbar-none">
        <!-- 상위 폴더 이동 버튼 -->
        <button
          v-if="breadcrumb.length > 0"
          class="shrink-0 w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mr-0.5"
          :title="$t('picker.parentFolder')"
          @click="goUp"
        >↑</button>
        <template v-for="(crumb, i) in breadcrumb" :key="crumb.path">
          <span v-if="i > 0" class="text-gray-300 dark:text-gray-700 shrink-0">/</span>
          <button
            class="hover:text-blue-600 dark:hover:text-blue-400 shrink-0 transition-colors"
            :class="i === breadcrumb.length - 1 ? 'text-gray-900 dark:text-white font-medium' : ''"
            @click="navigateTo(crumb, i)"
          >{{ crumb.name }}</button>
        </template>
        <span v-if="breadcrumb.length === 0" class="text-gray-400 italic">{{ $t('picker.libraryRoot') }}</span>
      </div>

      <!-- 로딩 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center py-10">
        <p class="text-sm text-gray-400">{{ $t('common.loading') }}</p>
      </div>

      <!-- 목록 -->
      <div v-else class="flex-1 overflow-y-auto min-h-0">
        <!-- 폴더 -->
        <div v-if="folders.length > 0" class="px-4 pt-3 pb-1">
          <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">{{ $t('picker.folderSection') }}</p>
          <div class="space-y-0.5">
            <div
              v-for="folder in folders"
              :key="folder.path"
              class="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 group transition-colors"
            >
              <button class="flex-1 flex items-center gap-2 text-left min-w-0" @click="enterFolder(folder)">
                <span class="text-yellow-400 shrink-0">{{ folder.has_children ? '📂' : '📁' }}</span>
                <span class="text-sm text-gray-700 dark:text-gray-300 truncate">{{ folder.name }}</span>
              </button>
              <!-- 폴더 모드: 이 폴더 열기 버튼 -->
              <button
                v-if="folderMode"
                class="shrink-0 text-xs px-2 py-1 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/60 transition-colors opacity-0 group-hover:opacity-100"
                @click.stop="$emit('select-folder', folder)"
              >{{ $t('picker.open') }}</button>
            </div>
          </div>
        </div>

        <!-- 오디오 파일 (폴더 모드에서는 숨김) -->
        <div v-if="files.length > 0 && !folderMode" class="px-4 pt-2 pb-3">
          <div class="flex items-center justify-between mb-1.5">
            <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ $t('picker.audioFiles', { n: files.length }) }}</p>
            <button
              class="text-xs px-2 py-0.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors"
              :disabled="adding"
              @click="addCurrentFolder"
            >{{ $t('picker.addFolder') }}</button>
          </div>
          <div class="space-y-0.5 max-h-48 overflow-y-auto">
            <div
              v-for="file in files"
              :key="file.path"
              class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg group transition-colors"
            >
              <span class="text-[10px] px-1 py-0.5 rounded font-mono uppercase shrink-0"
                :class="extBadge(file.ext)">{{ file.ext }}</span>
              <span class="flex-1 text-xs text-gray-600 dark:text-gray-400 truncate">{{ file.name }}</span>
              <button
                class="shrink-0 text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 transition-colors opacity-0 group-hover:opacity-100"
                :disabled="adding"
                @click="addFile(file)"
              >+</button>
            </div>
          </div>
        </div>

        <!-- 빈 폴더 -->
        <div v-if="!loading && folders.length === 0 && files.length === 0" class="flex flex-col items-center justify-center py-12 text-center px-6">
          <p class="text-3xl mb-2">📭</p>
          <p class="text-sm text-gray-400">{{ $t('picker.noFiles') }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
        <p v-if="folderMode" class="text-xs text-gray-400">{{ $t('picker.folderHint') }}</p>
        <template v-else>
          <p v-if="lastAdded" class="text-xs text-green-600 dark:text-green-400">✓ {{ lastAdded }}</p>
          <p v-else class="text-xs text-gray-400">{{ $t('picker.fileHint') }}</p>
        </template>
        <button
          class="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg transition-colors"
          @click="$emit('close')"
        >{{ $t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { workspaceApi } from '../api/index.js'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useToastStore } from '../stores/toast.js'

const { t } = useI18n()

const props = defineProps({
  folderMode: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'added', 'select-folder'])
const workspaceStore = useWorkspaceStore()
const toastStore = useToastStore()

const loading = ref(false)
const adding = ref(false)
const folders = ref([])
const files = ref([])
const breadcrumb = ref([])
const lastAdded = ref('')

async function loadChildren(path) {
  loading.value = true
  try {
    const { data } = await workspaceApi.libraryChildren(path)
    folders.value = data.folders
    files.value = data.files
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function loadRoots() {
  loading.value = true
  try {
    const { data } = await workspaceApi.libraryRoots()
    folders.value = data.roots
    files.value = []
    breadcrumb.value = []
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function enterFolder(folder) {
  breadcrumb.value.push({ name: folder.name, path: folder.path })
  loadChildren(folder.path)
}

function navigateTo(crumb, index) {
  if (index === breadcrumb.value.length - 1) return
  breadcrumb.value = breadcrumb.value.slice(0, index + 1)
  loadChildren(crumb.path)
}

function goUp() {
  if (breadcrumb.value.length === 0) return
  if (breadcrumb.value.length === 1) {
    breadcrumb.value = []
    loadRoots()
  } else {
    const parent = breadcrumb.value[breadcrumb.value.length - 2]
    breadcrumb.value = breadcrumb.value.slice(0, -1)
    loadChildren(parent.path)
  }
}

async function addCurrentFolder() {
  if (breadcrumb.value.length === 0) return
  const current = breadcrumb.value[breadcrumb.value.length - 1]
  await addFolder(current)
}

async function addFile(file) {
  adding.value = true
  try {
    const result = await workspaceStore.loadFiles([file.path])
    if (result.added > 0) {
      lastAdded.value = t('picker.fileAdded', { name: file.name })
      emit('added')
    } else {
      lastAdded.value = t('picker.alreadyAdded')
    }
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    adding.value = false
  }
}

function extBadge(ext) {
  const map = {
    mp3: 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    flac: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    m4a: 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    ogg: 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    aac: 'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',
  }
  return map[ext] || 'bg-gray-100 dark:bg-gray-700 text-gray-500'
}

onMounted(async () => {
  await loadRoots()
  // Library가 단일 루트면 자동으로 진입
  if (folders.value.length === 1) {
    enterFolder(folders.value[0])
  }
})
</script>
