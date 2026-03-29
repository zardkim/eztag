<template>
  <div class="max-w-2xl mx-auto p-4 sm:p-6">

    <!-- 헤더 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">📝 Get LRC</h2>
        <p class="text-xs text-gray-500 mt-0.5">폴더를 선택하고 LRC 가사 파일을 검색·저장합니다.</p>
      </div>
      <label class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400 cursor-pointer shrink-0">
        <input type="checkbox" v-model="lrcSkipExisting" class="w-3.5 h-3.5 rounded" />
        기존 LRC 건너뛰기
      </label>
    </div>

    <!-- 기본 폴더 미설정 -->
    <div v-if="!baseFolder" class="text-center py-12">
      <p class="text-4xl mb-3">📂</p>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">Get LRC 폴더가 설정되지 않았습니다.</p>
      <RouterLink
        to="/settings"
        class="text-xs text-blue-500 hover:text-blue-400 underline"
      >설정 → 일반에서 Get LRC 폴더를 설정해주세요.</RouterLink>
    </div>

    <!-- 기본 폴더 설정됨 -->
    <template v-else>

      <!-- 하위 폴더 로딩 중 -->
      <div v-if="loadingFolders" class="text-xs text-gray-400 text-center py-8">폴더 목록을 불러오는 중...</div>

      <!-- 하위 폴더 없음 -->
      <div v-else-if="!subfolders.length" class="text-sm text-gray-400 text-center py-10">
        하위 폴더가 없습니다. ({{ baseFolder }})
      </div>

      <!-- 폴더 목록 -->
      <div v-else class="space-y-2">
        <div
          v-for="folder in subfolders"
          :key="folder.path"
          class="bg-white dark:bg-gray-900 rounded-xl shadow-sm overflow-hidden"
        >
          <div class="px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ folder.name }}</span>
                <span v-if="folderStats[folder.path]" class="text-xs px-2 py-0.5 rounded-full"
                  :class="folderStats[folder.path].missing_lrc === 0
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                    : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'">
                  LRC {{ folderStats[folder.path].has_lrc }} / {{ folderStats[folder.path].total }}
                </span>
              </div>
              <p class="text-xs text-gray-400 font-mono truncate mt-0.5">{{ folder.path }}</p>
              <p v-if="folderStats[folder.path]" class="text-xs text-gray-500 mt-0.5">
                총 {{ folderStats[folder.path].total }}개
                · LRC {{ folderStats[folder.path].has_lrc }}개
                <span v-if="folderStats[folder.path].missing_lrc > 0" class="text-purple-500">
                  ({{ folderStats[folder.path].missing_lrc }}개 없음)
                </span>
              </p>
              <p v-else class="text-xs text-gray-400 mt-0.5">스캔 전</p>
            </div>
            <div class="flex gap-2 flex-wrap shrink-0">
              <button
                class="px-2.5 py-1 text-xs rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors disabled:opacity-50"
                :disabled="scanningFolder[folder.path] || !!runningFolder"
                @click="scanFolder(folder.path)"
              >
                <span v-if="scanningFolder[folder.path]">스캔 중...</span>
                <span v-else>스캔</span>
              </button>
              <button
                class="px-2.5 py-1 text-xs rounded-lg bg-purple-100 dark:bg-purple-900/30 hover:bg-purple-200 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 transition-colors disabled:opacity-50"
                :disabled="!!runningFolder || !folderStats[folder.path]"
                @click="startFolderLrc(folder.path, 'bugs')"
              >🎵 Bugs</button>
              <button
                class="px-2.5 py-1 text-xs rounded-lg bg-indigo-100 dark:bg-indigo-900/30 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 transition-colors disabled:opacity-50"
                :disabled="!!runningFolder || !folderStats[folder.path]"
                @click="startFolderLrc(folder.path, 'lrclib')"
              >🎵 LRCLIB</button>
            </div>
          </div>

          <!-- 폴더별 진행 상태 -->
          <div v-if="folderProgress[folder.path]?.running || folderProgress[folder.path]?.done"
            class="border-t border-purple-100 dark:border-purple-800 px-4 py-2 bg-purple-50 dark:bg-purple-900/10">
            <div class="flex items-center gap-2 mb-1">
              <div v-if="folderProgress[folder.path]?.running" class="w-3 h-3 border-2 border-purple-500 border-t-transparent rounded-full animate-spin shrink-0"></div>
              <span class="text-xs text-purple-600 dark:text-purple-400 flex-1 truncate">
                {{ folderProgress[folder.path]?.currentFile || (folderProgress[folder.path]?.done ? '완료' : '') }}
              </span>
              <span class="text-xs text-purple-500 shrink-0">
                {{ folderProgress[folder.path]?.current }}/{{ folderProgress[folder.path]?.total }}
                · {{ folderProgress[folder.path]?.ok }}✅ {{ folderProgress[folder.path]?.notFound }}❌
              </span>
              <button v-if="folderProgress[folder.path]?.done" class="text-purple-400 hover:text-purple-600 text-xs" @click="jobStore.clearLrcJob(); delete folderProgress[folder.path]">✕</button>
            </div>
            <div class="h-1 bg-purple-200 dark:bg-purple-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-purple-500 rounded-full transition-all duration-300"
                :style="{ width: folderProgress[folder.path]?.total > 0 ? (folderProgress[folder.path]?.current / folderProgress[folder.path]?.total * 100) + '%' : '0%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { configApi } from '../api/config.js'
import { browseApi } from '../api/index.js'
import { useToastStore } from '../stores/toast.js'
import { useJobStore } from '../stores/job.js'

const toastStore = useToastStore()
const jobStore = useJobStore()

const baseFolder = ref('')
const subfolders = ref([])
const loadingFolders = ref(false)
const folderStats = ref({})
const scanningFolder = ref({})
const folderProgress = ref({})
const lrcSkipExisting = ref(true)

// 현재 실행 중인 폴더 (jobStore에서 파생)
const runningFolder = computed(() =>
  jobStore.lrcJob?.running && jobStore.lrcJob?.routePath === '/get-lrc'
    ? jobStore.lrcJob.folderPath : null
)

// jobStore.lrcJob 변화를 folderProgress에 실시간 반영
watch(() => jobStore.lrcJob, (job) => {
  if (job && job.routePath === '/get-lrc') {
    folderProgress.value[job.folderPath] = { ...job }
  }
}, { deep: true, immediate: true })

// 작업 완료 감지: 스캔 갱신 + 토스트
watch(() => jobStore.lrcJob?.done, async (done) => {
  if (!done) return
  const job = jobStore.lrcJob
  if (!job || job.routePath !== '/get-lrc') return
  await scanFolder(job.folderPath)
  const parts = []
  if (job.ok) parts.push(`${job.ok}개 저장`)
  if (job.notFound) parts.push(`${job.notFound}개 미발견`)
  toastStore.success(parts.join(' · ') || '완료')
})

async function loadSubfolders() {
  loadingFolders.value = true
  try {
    const { data } = await browseApi.lrcSubfolders()
    baseFolder.value = data.base
    subfolders.value = data.folders
  } catch (e) {
    if (e.response?.status === 400) {
      baseFolder.value = ''
    } else {
      toastStore.error(e.response?.data?.detail || e.message)
    }
  } finally {
    loadingFolders.value = false
  }
}

async function loadBaseFolder() {
  try {
    const { data } = await configApi.get()
    const v = data.config?.lrc_base_folder?.value ?? ''
    if (!v) { baseFolder.value = ''; return }
    await loadSubfolders()
  } catch (e) {
    console.error('Failed to load config', e)
  }
}

async function scanFolder(path) {
  scanningFolder.value[path] = true
  try {
    const { data } = await browseApi.libraryAudioFiles(path, true)
    folderStats.value[path] = data
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    scanningFolder.value[path] = false
  }
}

async function startFolderLrc(folderPath, source) {
  if (jobStore.lrcJob?.running) return
  const stats = folderStats.value[folderPath]
  if (!stats) return

  let files = stats.files
  if (lrcSkipExisting.value) files = files.filter(f => !f.has_lrc)
  if (!files.length) { toastStore.success('LRC가 이미 모두 있습니다.'); return }

  const paths = files.map(f => f.path)
  const sourceLabel = source === 'bugs' ? 'Bugs' : 'LRCLIB'
  // 백그라운드 실행 (await 없음 - 다른 페이지 이동해도 계속 실행)
  jobStore.startLrcJob({
    files: paths,
    source,
    apiMode: 'library',
    routePath: '/get-lrc',
    routeLabel: folderPath.split('/').pop(),
    folderPath,
    sourceLabel,
  })
}

onMounted(() => {
  loadBaseFolder()
})
</script>
