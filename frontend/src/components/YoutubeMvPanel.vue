<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2 min-w-0">
        <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 text-red-500 shrink-0">
          <path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
        </svg>
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">YouTube MV</h3>
        <span class="text-xs text-gray-400">{{ browserStore.files.length }}개 파일</span>
      </div>
      <div class="flex items-center gap-1.5 shrink-0">
        <button
          class="text-xs px-2.5 py-1 rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors disabled:opacity-50 flex items-center gap-1"
          :disabled="bulkSearching"
          title="URL이 없는 파일을 모두 자동 검색 후 1위 결과를 저장합니다"
          @click="searchAll"
        >
          <span v-if="bulkSearching">
            {{ bulkProgress.current }}/{{ bulkProgress.total }} 검색 중...
          </span>
          <span v-else>전체 자동 검색</span>
        </button>
        <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1" @click="$emit('close')">✕</button>
      </div>
    </div>

    <!-- 진행 바 (전체 검색 중) -->
    <div v-if="bulkSearching" class="shrink-0 h-1 bg-gray-100 dark:bg-gray-800">
      <div
        class="h-full bg-red-500 transition-all duration-300"
        :style="{ width: bulkProgress.total > 0 ? (bulkProgress.current / bulkProgress.total * 100) + '%' : '0%' }"
      />
    </div>

    <!-- 파일 목록 -->
    <div class="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-800">
      <div
        v-for="file in browserStore.files"
        :key="file.path"
      >
        <!-- 파일 행 -->
        <div
          class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors"
          :class="activeRow === file.path ? 'bg-red-50 dark:bg-red-900/10' : ''"
        >
          <!-- 트랙 번호 -->
          <span class="text-xs text-gray-400 w-6 text-center shrink-0">{{ file.track_no || '—' }}</span>

          <!-- 타이틀곡 토글 -->
          <button
            class="shrink-0 text-[9px] font-extrabold px-1.5 py-0.5 rounded transition-colors leading-none"
            :class="titleMap[file.path]
              ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'"
            :title="titleMap[file.path] ? '타이틀곡 해제' : '타이틀곡으로 지정'"
            :disabled="file.scanned === false || savingMap[file.path]"
            @click="toggleTitle(file)"
          >타이틀</button>

          <!-- 제목/아티스트 -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate leading-tight">
              {{ file.title || file.filename }}
            </p>
            <p class="text-[11px] text-gray-400 truncate">{{ file.artist }}</p>
          </div>

          <!-- YouTube 상태 + 검색 버튼 -->
          <div class="flex items-center gap-1 shrink-0">
            <!-- 저장된 URL 링크 -->
            <a
              v-if="urlMap[file.path]"
              :href="urlMap[file.path]"
              target="_blank"
              class="text-red-500 hover:text-red-600 transition-colors"
              title="뮤직비디오 보기"
              @click.stop
            >
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                <path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
              </svg>
            </a>
            <!-- 검색 버튼 -->
            <button
              class="text-[11px] px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors disabled:opacity-50 border border-gray-200 dark:border-gray-700"
              :disabled="searchingMap[file.path] || bulkSearching"
              @click="toggleSearch(file)"
            >
              {{ searchingMap[file.path] ? '...' : activeRow === file.path ? '닫기' : '검색' }}
            </button>
          </div>
        </div>

        <!-- 확장: URL 입력 + 검색 결과 -->
        <div v-if="activeRow === file.path" class="px-3 pb-2.5 bg-red-50/50 dark:bg-red-900/5">
          <!-- 미스캔 경고 -->
          <div v-if="file.scanned === false" class="text-[10px] text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded px-2 py-1.5 mb-2 mt-1">
            라이브러리에 등록되지 않은 파일입니다. 먼저 스캔하세요.
          </div>

          <!-- URL 직접 입력 -->
          <div class="flex gap-1.5 mt-1.5 mb-1.5" v-if="file.scanned !== false">
            <input
              v-model="urlMap[file.path]"
              class="flex-1 text-[11px] font-mono px-2 py-1 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-red-400 dark:focus:border-red-600"
              placeholder="https://www.youtube.com/watch?v=..."
              @keydown.enter="saveFile(file)"
            />
            <button
              class="shrink-0 px-2.5 py-1 text-[11px] rounded bg-red-600 hover:bg-red-500 text-white transition-colors disabled:opacity-50"
              :disabled="savingMap[file.path]"
              @click="saveFile(file)"
            >저장</button>
            <button
              v-if="urlMap[file.path]"
              class="shrink-0 px-2 py-1 text-[11px] rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors"
              title="URL 제거"
              @click="clearUrl(file)"
            >✕</button>
          </div>

          <!-- 검색 결과 -->
          <div v-if="resultsMap[file.path]?.length > 0" class="space-y-1 max-h-52 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <button
              v-for="item in resultsMap[file.path]"
              :key="item.video_id"
              class="w-full flex items-center gap-2 px-2 py-1.5 text-left hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors border-b border-gray-100 dark:border-gray-800 last:border-0"
              :class="urlMap[file.path] === item.url ? 'bg-red-50 dark:bg-red-900/20' : ''"
              @click="selectResult(file, item)"
            >
              <img v-if="item.thumbnail" :src="item.thumbnail" class="w-14 h-9 object-cover rounded shrink-0" loading="lazy" />
              <div class="min-w-0 flex-1">
                <p class="text-[11px] text-gray-800 dark:text-gray-200 font-medium leading-tight line-clamp-2">{{ item.title }}</p>
                <p class="text-[10px] text-gray-400 truncate">{{ item.channel }}</p>
              </div>
              <span v-if="urlMap[file.path] === item.url" class="shrink-0 text-red-500 text-xs">✓</span>
            </button>
          </div>
          <p v-else-if="resultsMap[file.path] !== undefined && resultsMap[file.path].length === 0 && !searchingMap[file.path]" class="text-[10px] text-gray-400 mt-1">검색 결과 없음</p>
        </div>
      </div>

      <!-- 빈 상태 -->
      <div v-if="browserStore.files.length === 0" class="flex items-center justify-center h-32 text-gray-400 text-sm">
        파일이 없습니다.
      </div>
    </div>

    <!-- 안내 -->
    <div class="px-4 py-2 border-t border-gray-100 dark:border-gray-800 shrink-0">
      <p class="text-[10px] text-gray-400 leading-relaxed">
        저장 후 <b>HTML 생성</b>을 실행하면 트랙 목록에 YouTube 아이콘이 표시됩니다.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import { useJobStore } from '../stores/job.js'
import { browseApi } from '../api/index.js'

defineEmits(['close'])

const browserStore = useBrowserStore()
const toastStore = useToastStore()
const jobStore = useJobStore()

// ── 상태 ──────────────────────────────────────────────────
const urlMap = reactive({})       // path → youtube_url
const titleMap = reactive({})     // path → is_title_track
const resultsMap = reactive({})   // path → result[]
const searchingMap = reactive({}) // path → boolean
const savingMap = reactive({})    // path → boolean
const activeRow = ref(null)       // 확장된 파일 path

// jobStore YouTube 작업에서 파생 (패널은 Browser.vue 안에 있으므로 같은 routePath)
const _ytPanelJob = computed(() =>
  jobStore.youtubeJob?.routePath === '/browser' ? jobStore.youtubeJob : null
)
const bulkSearching = computed(() => !!_ytPanelJob.value?.running)
const bulkProgress = computed(() => _ytPanelJob.value || { current: 0, total: 0 })

// URL이 새로 검색되면 urlMap에 즉시 반영
watch(() => jobStore.youtubeJob?.lastFoundResult, (result) => {
  if (result) urlMap[result.path] = result.url || ''
})

// ── 초기화 ────────────────────────────────────────────────
function initFromFiles(files) {
  for (const f of files) {
    if (!(f.path in urlMap)) urlMap[f.path] = f.youtube_url || ''
    if (!(f.path in titleMap)) titleMap[f.path] = !!f.is_title_track
  }
}

watch(() => browserStore.files, initFromFiles, { immediate: true })

// ── 검색 ─────────────────────────────────────────────────
function toggleSearch(file) {
  if (activeRow.value === file.path) {
    activeRow.value = null
    return
  }
  activeRow.value = file.path
  if (!resultsMap[file.path]) searchFile(file)
}

async function searchFile(file) {
  const artist = file.artist || ''
  const title = file.title || file.filename || ''
  searchingMap[file.path] = true
  try {
    const { data } = await browseApi.searchYoutubeMV(artist, title)
    resultsMap[file.path] = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    const detail = e.response?.data?.detail || 'YouTube 검색 실패'
    toastStore.info(detail)
    resultsMap[file.path] = []
  } finally {
    searchingMap[file.path] = false
  }
}

async function selectResult(file, item) {
  const prev = urlMap[file.path]
  // 같은 항목 클릭 시 선택 해제
  urlMap[file.path] = prev === item.url ? '' : item.url
  await saveFile(file, { closeOnSuccess: false })
}

// ── 저장 ─────────────────────────────────────────────────
async function saveFile(file, { closeOnSuccess = true } = {}) {
  if (file.scanned === false) {
    toastStore.info('라이브러리에 등록되지 않은 파일입니다.')
    return
  }
  savingMap[file.path] = true
  try {
    await browseApi.setTrackInfo({
      path: file.path,
      is_title_track: titleMap[file.path],
      youtube_url: urlMap[file.path] || null,
    })
    browserStore.updateFiles([file.path], {
      is_title_track: titleMap[file.path],
      youtube_url: urlMap[file.path] || null,
    })
    if (closeOnSuccess) activeRow.value = null
  } catch (e) {
    if (e.response?.status === 404) {
      toastStore.info('라이브러리에 등록되지 않은 파일입니다. 먼저 스캔하세요.')
    } else {
      toastStore.info(e.response?.data?.detail || '저장 실패')
    }
  } finally {
    savingMap[file.path] = false
  }
}

async function clearUrl(file) {
  urlMap[file.path] = ''
  await saveFile(file, { closeOnSuccess: false })
}

async function toggleTitle(file) {
  titleMap[file.path] = !titleMap[file.path]
  await saveFile(file, { closeOnSuccess: false })
}

// ── 전체 자동 검색 ────────────────────────────────────────
async function searchAll() {
  const targets = browserStore.files.filter(f => f.scanned !== false && !urlMap[f.path])
  if (!targets.length) {
    toastStore.info('검색할 파일이 없습니다. (이미 URL이 있거나 미등록 파일)')
    return
  }
  const folderPath = browserStore.selectedFolder?.path || ''
  const folderName = browserStore.selectedFolder?.name || ''
  // 백그라운드 실행 (await 없음 - 다른 페이지 이동해도 계속 실행)
  jobStore.startYoutubeJob({ files: targets, routePath: '/browser', routeLabel: folderName, folderPath })
}
</script>
