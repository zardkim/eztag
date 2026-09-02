<template>
  <div class="h-full flex flex-col min-h-0 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
    <!-- 헤더 -->
    <div class="px-3 py-2 min-h-[40px] flex items-center gap-2 shrink-0 border-b border-gray-200 dark:border-gray-800">
      <span class="shrink-0 w-3.5 h-3.5 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
        <svg class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
          <path d="M1.5 4.5v7a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V5.5a1 1 0 0 0-1-1H8L6.5 3h-4a1 1 0 0 0-1 1Z" stroke="currentColor" stroke-width="1.2" />
        </svg>
      </span>
      <span class="flex-1 min-w-0 text-xs font-semibold text-gray-500 uppercase tracking-[0.04em]">{{ $t('browser.folderPanel') }}</span>
      <button
        class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :title="$t('common.close')"
        @click="$emit('close')"
      >✕</button>
    </div>

    <div v-if="!folder" class="px-3 py-4 text-xs text-gray-400">{{ $t('browser.selectFolder') }}</div>

    <div v-else class="flex-1 overflow-y-auto min-h-0 p-3 space-y-4">
      <!-- 폴더 이름 / 경로 / 이름변경 -->
      <div>
        <div class="flex items-center gap-1.5 mb-1">
          <span
            class="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider"
            :class="area === 'workspace'
              ? 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
              : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-500'"
          >{{ area === 'workspace' ? $t('sidebar.workspaceSection') : $t('sidebar.librarySection') }}</span>
          <button
            class="ml-auto shrink-0 px-1.5 py-0.5 rounded text-xs text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            :title="$t('sidebar.renameFolder')"
            @click="showRenameFolderModal = true"
          >✎</button>
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white break-all" :title="folder.name">{{ folder.name }}</p>
        <p class="mt-0.5 text-[11px] font-mono text-gray-500 dark:text-gray-400 break-all" :title="relativeFolderPath">{{ relativeFolderPath }}</p>
      </div>

      <!-- 오디오 파일명 — 본문 테이블에는 파일명 컬럼이 없으므로 여기가 유일한 확인 지점 -->
      <div v-if="browserStore.files.length > 0">
        <p class="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-gray-400 dark:text-gray-600">
          {{ $t('browser.audioFiles') }} <span class="font-mono">{{ browserStore.files.length }}</span>
        </p>
        <div class="space-y-0.5">
          <div
            v-for="file in browserStore.files"
            :key="file.path"
            class="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer transition-colors text-[11px]"
            :class="browserStore.selectedFile?.path === file.path
              ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
            :title="file.filename"
            @click="browserStore.selectFile(file)"
          >
            <span class="text-[9px] px-1 py-0.5 rounded font-mono uppercase shrink-0" :class="audioBadge(file.ext)">{{ file.ext }}</span>
            <span class="flex-1 truncate" :title="file.filename">{{ file.filename }}</span>
          </div>
        </div>
      </div>

      <!-- 커버 이미지 -->
      <div v-if="imageFiles.length > 0">
        <p class="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-gray-400 dark:text-gray-600">{{ $t('browser.coverImages') }}</p>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="img in imageFiles"
            :key="img.path"
            class="group relative aspect-square rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors"
            :title="img.filename"
            @click="openImage(img)"
          >
            <img :src="`/api/browse/extra-file?path=${encodeURIComponent(img.path)}`" :alt="img.filename" class="w-full h-full object-cover" />
            <span class="absolute inset-x-0 bottom-0 px-1 py-0.5 bg-black/55 text-white text-[9px] truncate text-left">{{ img.filename }}</span>
            <span
              class="absolute top-1 right-1 w-4 h-4 rounded flex items-center justify-center bg-black/50 text-white text-[10px] opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500"
              :title="$t('common.delete')"
              @click.stop="removeFile(img)"
            >✕</span>
          </button>
        </div>
      </div>

      <!-- 앨범카드 (HTML) -->
      <div v-if="htmlFiles.length > 0">
        <p class="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-gray-400 dark:text-gray-600">{{ $t('browser.albumCard') }}</p>
        <div class="space-y-1">
          <div
            v-for="f in htmlFiles"
            :key="f.path"
            class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors group text-xs"
            :class="browserStore.selectedExtraFile?.path === f.path
              ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
            :title="f.filename"
            @click="openHtml(f)"
          >
            <span class="text-[9px] px-1 py-0.5 rounded font-mono uppercase shrink-0 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-600 dark:text-yellow-400">html</span>
            <span class="flex-1 truncate" :title="f.filename">{{ f.filename }}</span>
            <button
              class="shrink-0 w-4 h-4 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
              :title="$t('common.delete')"
              @click.stop="removeFile(f)"
            >✕</button>
          </div>
        </div>
      </div>

      <!-- LRC 가사 파일 -->
      <div v-if="lrcFiles.length > 0">
        <p class="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-gray-400 dark:text-gray-600">
          {{ $t('browser.lrcFiles') }} <span class="font-mono">{{ lrcFiles.length }}</span>
        </p>
        <div class="max-h-40 overflow-y-auto space-y-0.5">
          <div
            v-for="f in lrcFiles"
            :key="f.path"
            class="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] text-gray-400 dark:text-gray-600"
            :title="f.filename"
          >
            <span class="text-[9px] px-1 py-0.5 rounded font-mono uppercase shrink-0 bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400">lrc</span>
            <span class="flex-1 truncate" :title="f.filename">{{ f.filename }}</span>
          </div>
        </div>
      </div>

      <div v-if="browserStore.extraFiles.length === 0 && browserStore.files.length === 0" class="text-xs text-gray-400">{{ $t('browser.noExtraFiles') }}</div>
    </div>

    <!-- 폴더 이름 변경 모달 -->
    <Teleport to="body">
      <RenameFolderModal
        v-if="showRenameFolderModal && folder"
        :folder="folder"
        :first-track="browserStore.files[0] || null"
        @close="showRenameFolderModal = false"
        @renamed="onFolderRenamed"
      />
    </Teleport>

    <!-- 이미지 뷰어 -->
    <Teleport to="body">
      <div
        v-if="viewerImage"
        class="fixed inset-0 bg-black/85 z-[400] flex items-center justify-center p-4"
        @click.self="viewerImage = null"
      >
        <div class="relative max-w-3xl max-h-[90vh] flex flex-col items-center">
          <button class="absolute -top-8 right-0 text-white/70 hover:text-white text-sm" @click="viewerImage = null">✕ {{ $t('common.close') }}</button>
          <img
            :src="`/api/browse/extra-file?path=${encodeURIComponent(viewerImage.path)}`"
            :alt="viewerImage.filename"
            class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          />
          <p class="mt-2 text-white/60 text-xs">{{ viewerImage.filename }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import RenameFolderModal from './RenameFolderModal.vue'

defineEmits(['close'])

const { t } = useI18n()
const browserStore = useBrowserStore()
const toastStore = useToastStore()

const showRenameFolderModal = ref(false)
const viewerImage = ref(null)

const folder = computed(() => browserStore.selectedFolder)
const area = computed(() => browserStore.currentArea)

const imageFiles = computed(() => browserStore.extraFiles.filter(f => f.file_type === 'image'))
const htmlFiles  = computed(() => browserStore.extraFiles.filter(f => f.file_type === 'html'))
const lrcFiles   = computed(() => browserStore.extraFiles.filter(f => f.file_type === 'lrc'))

const relativeFolderPath = computed(() => {
  const f = folder.value
  if (!f) return ''
  const root = browserStore.breadcrumb[0]
  if (!root || root.path === f.path) return f.name
  const rootPath = root.path.endsWith('/') ? root.path : root.path + '/'
  const rel = f.path.startsWith(rootPath) ? f.path.slice(rootPath.length) : f.path
  return rel || f.name
})

function onFolderRenamed(data) {
  const cur = folder.value
  const newFolder = { name: data.new_name, path: data.new_path }
  const newCrumb = browserStore.breadcrumb.map(b => (b.path === cur.path ? newFolder : b))
  browserStore.invalidateFilesCache(cur.path)
  browserStore.selectedFolder = newFolder
  browserStore.breadcrumb = newCrumb
  browserStore.loadFiles(newFolder.path, true)
  showRenameFolderModal.value = false
  toastStore.success(t('sidebar.renameSuccess', { name: data.new_name }))
}

function audioBadge(ext) {
  const map = {
    mp3:  'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    flac: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    m4a:  'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    ogg:  'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    aac:  'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',
  }
  return map[ext] || 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
}

function openImage(file) {
  viewerImage.value = file
}

function openHtml(file) {
  browserStore.selectExtraFile(file)
}

async function removeFile(file) {
  if (!confirm(t('sidebar.deleteConfirm', { filename: file.filename }))) return
  try {
    await browseApi.deleteExtraFile(file.path)
    if (browserStore.selectedExtraFile?.path === file.path) browserStore.selectExtraFile(null)
    const path = folder.value?.path
    if (path) {
      browserStore.invalidateFilesCache(path)
      browserStore.loadFiles(path, true)
    }
    toastStore.success(t('sidebar.deleteSuccess', { filename: file.filename }))
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('sidebar.deleteFailed'))
  }
}
</script>
