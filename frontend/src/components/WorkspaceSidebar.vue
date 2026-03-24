<template>
  <div class="flex flex-col h-full min-h-0 select-none">

    <!-- 홈 메뉴 -->
    <div class="px-2 pt-2 pb-1 shrink-0">
      <RouterLink
        to="/home"
        class="flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        active-class="bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white"
      >
        <span class="text-base shrink-0">🏠</span>
        <span class="font-medium">{{ $t('nav.home') }}</span>
      </RouterLink>
    </div>

    <!-- WORKSPACE / LIBRARY 버튼 한 줄 -->
    <div class="px-3 pt-1 pb-2 flex gap-1.5 shrink-0">
      <button
        class="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg border border-dashed border-orange-300 dark:border-orange-700 text-xs text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors"
        @click="showWorkspacePicker = true"
      >
        <span>📂</span>
        <span>{{ $t('sidebar.workspaceSection') }}</span>
      </button>
      <button
        class="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg border border-dashed border-blue-300 dark:border-blue-700 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
        @click="showLibraryPicker = true"
      >
        <span>📚</span>
        <span>{{ $t('sidebar.librarySection') }}</span>
      </button>
    </div>

    <!-- 구분선 -->
    <div class="mx-3 mb-2 border-t border-gray-200 dark:border-gray-700 shrink-0"></div>

    <!-- 현재 열린 폴더 경로 (상대경로) -->
    <div v-if="browserStore.selectedFolder" class="px-3 pb-1 shrink-0">
      <div
        class="rounded-lg px-2.5 py-2 cursor-pointer transition-colors group"
        :class="browserStore.currentArea === 'workspace'
          ? 'bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30'
          : 'bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30'"
        :title="$t('sidebar.goBrowser')"
        @click="router.push('/browser')"
      >
        <div class="flex items-center justify-between mb-0.5">
          <p
            class="text-[10px] font-semibold uppercase tracking-wider"
            :class="browserStore.currentArea === 'workspace'
              ? 'text-orange-500 dark:text-orange-400'
              : 'text-yellow-600 dark:text-yellow-500'"
          >
            {{ browserStore.currentArea === 'workspace' ? $t('sidebar.workspaceSection') : $t('sidebar.librarySection') }}
            <span class="ml-1">↗</span>
          </p>
          <button
            class="text-sm text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-all px-1"
            :title="$t('sidebar.renameFolder')"
            @click.stop="showRenameFolderModal = true"
          >✎</button>
        </div>
        <p class="text-[11px] text-gray-700 dark:text-gray-300 truncate font-mono" :title="relativeFolderPath">{{ relativeFolderPath }}</p>
      </div>
    </div>

    <!-- 폴더 이름 변경 모달 -->
    <Teleport to="body">
      <RenameFolderModal
        v-if="showRenameFolderModal && browserStore.selectedFolder"
        :folder="browserStore.selectedFolder"
        :first-track="browserStore.files[0] || null"
        @close="showRenameFolderModal = false"
        @renamed="onFolderRenamed"
      />
    </Teleport>

    <!-- 파일 목록 -->
    <div v-if="browserStore.selectedFolder" class="flex-1 overflow-y-auto min-h-0 px-2 pb-2">
      <div v-if="browserStore.loading" class="py-4 text-center text-xs text-gray-400">{{ $t('common.loading') }}</div>
      <div v-else-if="browserStore.files.length === 0 && browserStore.extraFiles.length === 0" class="py-4 text-center text-xs text-gray-400">{{ $t('sidebar.noFiles') }}</div>
      <div v-else class="space-y-0.5 pt-1">
        <!-- 오디오 파일 -->
        <div
          v-for="file in browserStore.files"
          :key="file.path"
          class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors group"
          :class="browserStore.selectedFile?.path === file.path
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
          :title="file.filename"
          @click="browserStore.selectFile(file)"
        >
          <span class="text-[9px] px-1 py-0.5 rounded font-mono uppercase shrink-0" :class="audioBadge(file.ext)">{{ file.ext }}</span>
          <span class="flex-1 text-[11px] truncate">{{ file.filename }}</span>
        </div>
        <!-- 기타 파일 (LRC, 이미지, HTML) -->
        <template v-if="browserStore.extraFiles.length > 0">
          <div class="my-1 border-t border-gray-100 dark:border-gray-800"></div>
          <div
            v-for="file in browserStore.extraFiles"
            :key="file.path"
            class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg transition-colors group"
            :class="[
              file.file_type === 'lrc' ? 'text-gray-400 dark:text-gray-600 cursor-default' : 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400',
              browserStore.selectedExtraFile?.path === file.path ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : '',
            ]"
            :title="file.filename"
            @click="onExtraFileClick(file)"
          >
            <span class="text-[9px] px-1 py-0.5 rounded font-mono uppercase shrink-0" :class="extraBadge(file.file_type)">{{ extFromName(file.filename) }}</span>
            <span class="flex-1 text-[11px] truncate">{{ file.filename }}</span>
            <button
              v-if="file.file_type === 'image' || file.file_type === 'html'"
              class="shrink-0 w-4 h-4 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 text-xs"
              :title="$t('common.delete')"
              @click.stop="deleteExtraFile(file)"
            >✕</button>
          </div>
        </template>
      </div>
    </div>

    <!-- 워크스페이스 폴더 피커 -->
    <Teleport to="body">
      <LibraryPickerModal
        v-if="showWorkspacePicker"
        :folder-mode="true"
        area="workspace"
        @close="showWorkspacePicker = false"
        @select-folder="onSelectWorkspaceFolder"
      />
    </Teleport>

    <!-- 라이브러리 폴더 피커 -->
    <Teleport to="body">
      <LibraryPickerModal
        v-if="showLibraryPicker"
        :folder-mode="true"
        area="library"
        @close="showLibraryPicker = false"
        @select-folder="onSelectLibraryFolder"
      />
    </Teleport>

    <!-- 이미지 뷰어 모달 -->
    <Teleport to="body">
      <div
        v-if="showImageModal && selectedImage"
        class="fixed inset-0 bg-black/80 z-[400] flex items-center justify-center p-4"
        @click.self="showImageModal = false"
      >
        <div class="relative max-w-3xl max-h-[90vh] flex flex-col items-center">
          <button
            class="absolute -top-8 right-0 text-white/70 hover:text-white text-sm"
            @click="showImageModal = false"
          >✕ {{ $t('common.close') }}</button>
          <img
            :src="`/api/browse/extra-file?path=${encodeURIComponent(selectedImage.path)}`"
            :alt="selectedImage.filename"
            class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          />
          <p class="mt-2 text-white/60 text-xs">{{ selectedImage.filename }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import LibraryPickerModal from './LibraryPickerModal.vue'
import RenameFolderModal from './RenameFolderModal.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const browserStore = useBrowserStore()
const toastStore = useToastStore()

const showWorkspacePicker = ref(false)
const showLibraryPicker = ref(false)
const showImageModal = ref(false)
const selectedImage = ref(null)
const showRenameFolderModal = ref(false)

function onFolderRenamed(data) {
  const folder = browserStore.selectedFolder
  const newFolder = { name: data.new_name, path: data.new_path }
  const newCrumb = browserStore.breadcrumb.map(b =>
    b.path === folder.path ? newFolder : b
  )
  browserStore.invalidateFilesCache(folder.path)
  browserStore.selectedFolder = newFolder
  browserStore.breadcrumb = newCrumb
  browserStore.loadFiles(newFolder.path, true)
  showRenameFolderModal.value = false
  toastStore.success(t('sidebar.renameSuccess', { name: data.new_name }))
}

async function deleteExtraFile(file) {
  if (!confirm(t('sidebar.deleteConfirm', { filename: file.filename }))) return
  try {
    await browseApi.deleteExtraFile(file.path)
    if (browserStore.selectedExtraFile?.path === file.path) {
      browserStore.selectExtraFile(null)
    }
    const path = browserStore.selectedFolder?.path
    if (path) {
      browserStore.invalidateFilesCache(path)
      browserStore.loadFiles(path, true)
    }
    toastStore.success(t('sidebar.deleteSuccess', { filename: file.filename }))
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('sidebar.deleteFailed'))
  }
}

function onExtraFileClick(file) {
  if (file.file_type === 'lrc') return
  if (file.file_type === 'image') {
    selectedImage.value = file
    showImageModal.value = true
  } else if (file.file_type === 'html') {
    browserStore.selectExtraFile(file)
    if (route.path !== '/browser') router.push('/browser')
  }
}

function extFromName(filename) {
  const i = filename.lastIndexOf('.')
  return i >= 0 ? filename.slice(i + 1).toLowerCase() : '?'
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

function extraBadge(fileType) {
  if (fileType === 'lrc')   return 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400'
  if (fileType === 'image') return 'bg-pink-100 dark:bg-pink-900/40 text-pink-600 dark:text-pink-400'
  if (fileType === 'html')  return 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-600 dark:text-yellow-400'
  return 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
}

const relativeFolderPath = computed(() => {
  const folder = browserStore.selectedFolder
  if (!folder) return ''
  const root = browserStore.breadcrumb[0]
  if (!root || root.path === folder.path) return folder.name
  const rootPath = root.path.endsWith('/') ? root.path : root.path + '/'
  const rel = folder.path.startsWith(rootPath) ? folder.path.slice(rootPath.length) : folder.path
  return rel || folder.name
})

function onSelectWorkspaceFolder(folder) {
  showWorkspacePicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'workspace')
  if (route.path !== '/browser') router.push('/browser')
}

function onSelectLibraryFolder(folder) {
  showLibraryPicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'library')
  if (route.path !== '/browser') router.push('/browser')
}

defineExpose({
  openFolderPicker: () => { showLibraryPicker.value = true },
})
</script>
