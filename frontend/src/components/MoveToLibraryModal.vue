<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="$emit('close')"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[85vh] relative">

        <!-- 이동 중 오버레이 -->
        <div v-if="moving" class="absolute inset-0 bg-white/90 dark:bg-gray-900/90 rounded-2xl flex flex-col items-center justify-center z-20 gap-3">
          <div class="w-10 h-10 border-2 border-blue-200 dark:border-blue-800 border-t-blue-500 rounded-full animate-spin"></div>
          <p class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('browser.moveToLibrary.moving') }}</p>
          <p class="text-xs text-gray-400 font-mono truncate max-w-[260px]">{{ sourceFolderName }}</p>
        </div>

        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('browser.moveToLibrary.title') }}</h2>
          <button class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-1 rounded" @click="$emit('close')">✕</button>
        </div>

        <!-- Source info -->
        <div class="px-5 pt-3 pb-2 shrink-0">
          <div class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg px-3 py-2.5">
            <p class="text-xs text-orange-500 dark:text-orange-400 font-medium mb-0.5">{{ t('browser.moveToLibrary.sourceLabel') }}</p>
            <p class="text-sm text-orange-900 dark:text-orange-200 font-mono truncate">{{ sourceFolderName }}</p>
            <p class="text-xs text-orange-400 mt-0.5">{{ t('browser.moveFolder.fileCount', { n: sourceFileCount }) }}</p>
          </div>
        </div>

        <!-- Library breadcrumb -->
        <div class="px-3 py-2 flex items-center gap-1 text-xs text-gray-500 border-y border-gray-100 dark:border-gray-800 shrink-0 overflow-x-auto scrollbar-none">
          <button
            v-if="breadcrumb.length > 0"
            class="shrink-0 w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mr-0.5"
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
          <span v-if="breadcrumb.length === 0" class="text-gray-400 italic">{{ t('picker.libraryRoot') }}</span>
        </div>

        <!-- Folder list -->
        <div class="flex-1 overflow-y-auto min-h-0">
          <div v-if="loading" class="flex items-center justify-center py-8">
            <p class="text-sm text-gray-400">{{ t('common.loading') }}</p>
          </div>
          <div v-else-if="folders.length === 0" class="flex items-center justify-center py-8">
            <p class="text-sm text-gray-400 italic">{{ t('picker.noFiles') }}</p>
          </div>
          <div v-else class="px-3 py-2 space-y-0.5">
            <!-- 현재 위치를 선택지로 표시 -->
            <div
              v-if="breadcrumb.length > 0"
              class="flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition-colors"
              :class="selectedPath === currentPath
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
              @click="selectPath(currentPath)"
            >
              <span class="text-base shrink-0">📂</span>
              <span class="flex-1 text-sm truncate font-medium">[{{ t('browser.moveToLibrary.currentFolder') }}]</span>
              <span class="text-xs font-mono text-gray-400 truncate max-w-[200px]">{{ relativeCurrentPath }}</span>
            </div>
            <div v-if="breadcrumb.length > 0" class="border-t border-gray-100 dark:border-gray-800 my-1"></div>
            <div
              v-for="folder in folders"
              :key="folder.path"
              class="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <button class="flex-1 flex items-center gap-2 text-left min-w-0" @click="enterFolder(folder)">
                <span class="text-base shrink-0">{{ folder.has_children ? '📂' : '📁' }}</span>
                <span class="text-sm text-gray-700 dark:text-gray-300 truncate">{{ folder.name }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Selected destination -->
        <div v-if="selectedPath" class="px-5 py-2 shrink-0 border-t border-gray-100 dark:border-gray-800">
          <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-3 py-2">
            <p class="text-xs text-green-500 dark:text-green-400 font-medium mb-0.5">{{ t('browser.moveFolder.selectedDest') }}</p>
            <p class="text-sm text-green-900 dark:text-green-200 font-mono truncate">{{ relativeSelectedPath }}</p>
          </div>
        </div>

        <!-- Error -->
        <div v-if="moveError" class="px-5 pb-2 shrink-0">
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2 text-xs text-red-700 dark:text-red-400">
            {{ moveError }}
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-5 py-4 border-t border-gray-200 dark:border-gray-800 shrink-0">
          <button
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            @click="$emit('close')"
          >{{ t('browser.moveFolder.cancel') }}</button>
          <button
            class="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            :disabled="!selectedPath || moving"
            @click="doMove"
          >
            <span v-if="moving" class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
            {{ t('browser.moveToLibrary.move') }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { workspaceApi, browseApi } from '../api/index.js'

const props = defineProps({
  sourcePath: { type: String, required: true },
  sourceFileCount: { type: Number, default: 0 },
})
const emit = defineEmits(['close', 'moved'])

const { t } = useI18n()

const sourceFolderName = computed(() => {
  const parts = props.sourcePath.split('/')
  return parts[parts.length - 1] || props.sourcePath
})

const loading = ref(false)
const folders = ref([])
const breadcrumb = ref([])
const selectedPath = ref('')
const moving = ref(false)
const moveError = ref('')

const currentPath = computed(() =>
  breadcrumb.value.length > 0 ? breadcrumb.value[breadcrumb.value.length - 1].path : ''
)

const libraryRoot = computed(() => breadcrumb.value[0] ?? null)

function toRelativePath(absPath) {
  if (!libraryRoot.value) return absPath
  const root = libraryRoot.value
  const rootPath = root.path.endsWith('/') ? root.path : root.path + '/'
  if (absPath === root.path || absPath + '/' === rootPath) return root.name
  const rel = absPath.startsWith(rootPath) ? absPath.slice(rootPath.length) : absPath
  return root.name + (rel ? '/' + rel : '')
}

const relativeCurrentPath = computed(() => toRelativePath(currentPath.value))

const relativeSelectedPath = computed(() =>
  selectedPath.value ? toRelativePath(selectedPath.value) + '/' + sourceFolderName.value : ''
)

async function loadChildren(path) {
  loading.value = true
  try {
    const { data } = await workspaceApi.libraryChildren(path)
    folders.value = data.folders
  } catch (e) {
    folders.value = []
  } finally {
    loading.value = false
  }
}

async function loadRoots() {
  loading.value = true
  try {
    const { data } = await workspaceApi.libraryRoots()
    folders.value = data.roots
    breadcrumb.value = []
  } catch (e) {
    folders.value = []
  } finally {
    loading.value = false
  }
}

function enterFolder(folder) {
  breadcrumb.value.push({ name: folder.name, path: folder.path })
  selectedPath.value = ''
  loadChildren(folder.path)
}

function navigateTo(crumb, index) {
  if (index === breadcrumb.value.length - 1) return
  breadcrumb.value = breadcrumb.value.slice(0, index + 1)
  selectedPath.value = ''
  loadChildren(crumb.path)
}

function goUp() {
  if (breadcrumb.value.length === 0) return
  selectedPath.value = ''
  if (breadcrumb.value.length === 1) {
    breadcrumb.value = []
    loadRoots()
  } else {
    const parent = breadcrumb.value[breadcrumb.value.length - 2]
    breadcrumb.value = breadcrumb.value.slice(0, -1)
    loadChildren(parent.path)
  }
}

function selectPath(path) {
  selectedPath.value = path
  moveError.value = ''
}

async function doMove() {
  if (!selectedPath.value || moving.value) return
  moveError.value = ''
  moving.value = true
  try {
    const { data } = await browseApi.moveToLibrary({
      source_path: props.sourcePath,
      dest_path: selectedPath.value,
    })
    emit('moved', { dest: data.dest })
  } catch (e) {
    if (e.response?.status === 409) {
      moveError.value = t('browser.moveFolder.conflictWarning')
    } else {
      moveError.value = e.response?.data?.detail || e.message
    }
  } finally {
    moving.value = false
  }
}

onMounted(async () => {
  await loadRoots()
  if (folders.value.length === 1) {
    enterFolder(folders.value[0])
  }
})
</script>
