<template>
  <div class="flex flex-col h-full min-h-0 select-none">

    <!-- 헤더 -->
    <div class="px-3 pt-3 pb-2 shrink-0">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">워크스페이스</span>
        <div class="flex gap-1">
          <!-- 새 세션 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-xs"
            title="새 세션 시작"
            @click="confirmNewSession"
          >↺</button>
        </div>
      </div>

      <!-- 세션 상태 배지 -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-gray-400">{{ workspaceStore.items.length }}개 파일</span>
      </div>
    </div>

    <!-- 폴더/파일 열기 버튼 -->
    <div class="px-3 pb-2 shrink-0 flex gap-1.5">
      <button
        class="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg border border-dashed border-blue-300 dark:border-blue-700 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
        @click="showFolderPicker = true"
      >
        <span>📂</span>
        <span>폴더 열기</span>
      </button>
      <button
        class="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        @click="showPicker = true"
      >
        <span>📄</span>
        <span>파일 열기</span>
      </button>
    </div>

    <!-- 현재 열린 폴더 경로 (상대경로) -->
    <div v-if="browserStore.selectedFolder" class="px-3 pb-1 shrink-0">
      <!-- 이름 변경 인풋 -->
      <div v-if="renamingFolder" class="bg-gray-50 dark:bg-gray-800 rounded-lg px-2.5 py-2">
        <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">폴더 이름 변경</p>
        <input
          ref="folderNameInput"
          v-model="folderNewName"
          class="w-full text-[11px] font-mono bg-white dark:bg-gray-700 border border-blue-400 rounded px-1.5 py-1 outline-none text-gray-900 dark:text-white"
          @keydown.enter="submitFolderRename"
          @keydown.escape="renamingFolder = false"
        />
        <div class="flex gap-1 mt-1.5">
          <button class="flex-1 text-[10px] py-0.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors" @click="submitFolderRename">확인</button>
          <button class="flex-1 text-[10px] py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors" @click="renamingFolder = false">취소</button>
        </div>
      </div>
      <!-- 폴더 경로 표시 -->
      <div
        v-else
        class="bg-gray-50 dark:bg-gray-800 rounded-lg px-2.5 py-2 cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors group"
        title="태그편집 페이지로 이동"
        @click="router.push('/browser')"
      >
        <div class="flex items-center justify-between mb-0.5">
          <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">현재 폴더 ↗</p>
          <button
            class="text-[10px] text-gray-300 hover:text-gray-600 dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-all px-1"
            title="폴더 이름 변경"
            @click.stop="startFolderRename"
          >✎</button>
        </div>
        <p class="text-[11px] text-gray-700 dark:text-gray-300 truncate font-mono" :title="relativeFolderPath">{{ relativeFolderPath }}</p>
      </div>
    </div>

    <!-- 파일 목록 (폴더 열기 모드) -->
    <div v-if="browserStore.selectedFolder" class="flex-1 overflow-y-auto min-h-0 px-2 pb-2">
      <div v-if="browserStore.loading" class="py-4 text-center text-xs text-gray-400">불러오는 중...</div>
      <div v-else-if="browserStore.files.length === 0 && browserStore.extraFiles.length === 0" class="py-4 text-center text-xs text-gray-400">파일 없음</div>
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
            <!-- 이미지/HTML만 삭제 버튼 -->
            <button
              v-if="file.file_type === 'image' || file.file_type === 'html'"
              class="shrink-0 w-4 h-4 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 text-xs"
              title="삭제"
              @click.stop="deleteExtraFile(file)"
            >✕</button>
          </div>
        </template>
      </div>
    </div>

    <!-- 아이템 목록 (워크스페이스 모드) -->
    <div v-else class="flex-1 overflow-y-auto min-h-0 px-2">
      <!-- 빈 상태 -->
      <div v-if="workspaceStore.items.length === 0" class="flex flex-col items-center justify-center py-8 text-center px-2">
        <p class="text-2xl mb-2">📭</p>
        <p class="text-[11px] text-gray-400 leading-relaxed">폴더를 열어 파일을 워크스페이스에 추가하세요.</p>
      </div>

      <!-- 워크스페이스 파일 목록 -->
      <div v-else class="space-y-0.5 pb-2">
        <div
          v-for="item in workspaceStore.items"
          :key="item.id"
          class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors text-left group"
          :class="workspaceStore.selectedItemId === item.id
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
          :title="item.filename"
          @click="workspaceStore.selectItem(item.id)"
        >
          <span class="w-1.5 h-1.5 rounded-full shrink-0 mt-0.5 bg-gray-300 dark:bg-gray-600"></span>
          <span class="flex-1 text-[11px] truncate">{{ item.filename }}</span>
          <button
            class="shrink-0 w-4 h-4 flex items-center justify-center text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 text-xs"
            @click.stop="workspaceStore.removeItem(item.id)"
          >✕</button>
        </div>
      </div>
    </div><!-- /워크스페이스 모드 -->

    <!-- 폴더 열기 (folderMode) -->
    <Teleport to="body">
      <LibraryPickerModal
        v-if="showFolderPicker"
        :folder-mode="true"
        @close="showFolderPicker = false"
        @select-folder="onSelectFolder"
      />
    </Teleport>

    <!-- 파일 열기 -->
    <Teleport to="body">
      <LibraryPickerModal
        v-if="showPicker"
        @close="showPicker = false"
        @added="showPicker = false"
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
          >✕ 닫기</button>
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
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { workspaceApi } from '../api/index.js'
import { browseApi } from '../api/index.js'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import LibraryPickerModal from './LibraryPickerModal.vue'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const browserStore = useBrowserStore()
const toastStore = useToastStore()

const showPicker = ref(false)
const showFolderPicker = ref(false)
const showImageModal = ref(false)
const selectedImage = ref(null)

// ── 폴더 이름 변경 ─────────────────────────────────────────
const renamingFolder = ref(false)
const folderNewName = ref('')
const folderNameInput = ref(null)

function startFolderRename() {
  folderNewName.value = browserStore.selectedFolder?.name || ''
  renamingFolder.value = true
  nextTick(() => {
    folderNameInput.value?.select()
  })
}

async function submitFolderRename() {
  const folder = browserStore.selectedFolder
  if (!folder || !folderNewName.value.trim()) return
  try {
    const { data } = await browseApi.renameFolder(folder.path, folderNewName.value.trim())
    // breadcrumb·selectedFolder 갱신
    const newFolder = { name: data.new_name, path: data.new_path }
    const newCrumb = browserStore.breadcrumb.map(b =>
      b.path === folder.path ? newFolder : b
    )
    browserStore.selectFolder(newFolder, newCrumb)
    renamingFolder.value = false
    toastStore.success(`폴더 이름이 "${data.new_name}"으로 변경되었습니다.`)
  } catch (e) {
    toastStore.error(e.response?.data?.detail || '폴더 이름 변경에 실패했습니다.')
  }
}

// ── 기타 파일 삭제 ─────────────────────────────────────────
async function deleteExtraFile(file) {
  if (!confirm(`"${file.filename}" 파일을 삭제하시겠습니까?`)) return
  try {
    await browseApi.deleteExtraFile(file.path)
    // selectedExtraFile이 삭제된 파일이면 초기화
    if (browserStore.selectedExtraFile?.path === file.path) {
      browserStore.selectExtraFile(null)
    }
    // 파일 목록 새로고침
    const path = browserStore.selectedFolder?.path
    if (path) {
      browserStore.invalidateFilesCache(path)
      browserStore.loadFiles(path, true)
    }
    toastStore.success(`"${file.filename}" 삭제되었습니다.`)
  } catch (e) {
    toastStore.error(e.response?.data?.detail || '파일 삭제에 실패했습니다.')
  }
}

function onExtraFileClick(file) {
  if (file.file_type === 'lrc') return
  if (file.file_type === 'image') {
    selectedImage.value = file
    showImageModal.value = true
  } else if (file.file_type === 'html') {
    browserStore.selectExtraFile(file)
    router.push('/browser')
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

// 현재 폴더의 상대경로 (라이브러리 루트 기준)
const relativeFolderPath = computed(() => {
  const folder = browserStore.selectedFolder
  if (!folder) return ''
  const root = browserStore.breadcrumb[0]
  if (!root || root.path === folder.path) return folder.name
  const rootPath = root.path.endsWith('/') ? root.path : root.path + '/'
  const rel = folder.path.startsWith(rootPath) ? folder.path.slice(rootPath.length) : folder.path
  return rel || folder.name
})

function onSelectFolder(folder) {
  showFolderPicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }])
  router.push('/browser')
}

async function confirmNewSession() {
  if (workspaceStore.pendingCount > 0) {
    if (!confirm(`변경되지 않은 내용이 ${workspaceStore.pendingCount}개 있습니다.\n새 세션을 시작하면 현재 변경 사항이 사라집니다.\n계속하시겠습니까?`)) return
  }
  await workspaceStore.newSession()
  toastStore.success('새 세션이 시작되었습니다.')
}



function fmtDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}


defineExpose({
  openFolderPicker: () => { showFolderPicker.value = true },
  openFilePicker: () => { showPicker.value = true },
})
</script>
