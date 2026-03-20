<template>
  <div class="flex flex-col h-full">

    <!-- ── 툴바 ── -->
    <div class="shrink-0 h-10 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
      <div class="flex items-center gap-2 h-full px-4 overflow-x-auto scrollbar-none">
        <template v-if="workspaceStore.items.length > 0">
          <!-- 다중 선택 카운트 -->
          <span v-if="checkedIds.size > 0" class="text-xs text-blue-600 dark:text-blue-400 font-medium shrink-0">
            {{ checkedIds.size }}개 선택
            <button class="ml-1 text-gray-400 hover:text-gray-600" @click="checkedIds.clear()">✕</button>
          </span>
          <!-- 정렬 -->
          <select v-model="sortKey" class="text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-1.5 py-1 focus:outline-none shrink-0">
            <option value="sort_order">추가순</option>
            <option value="filename">파일명</option>
            <option value="title">제목</option>
            <option value="artist">아티스트</option>
          </select>
          <!-- 전체 선택 -->
          <button class="btn-toolbar shrink-0" @click="toggleSelectAll">
            {{ checkedIds.size === displayItems.length && displayItems.length > 0 ? '선택 해제' : '전체 선택' }}
          </button>
          <!-- 배치 편집 -->
          <button
            class="btn-toolbar shrink-0"
            :class="showPanel === 'batch' ? 'btn-toolbar-active' : ''"
            @click="showPanel = showPanel === 'batch' ? null : 'batch'"
          >✏️ 일괄 편집</button>
          <!-- 자동 태그 -->
          <div class="relative shrink-0" ref="autoTagRef">
            <button
              class="btn-toolbar !bg-green-100 !text-green-700 hover:!bg-green-200 dark:!bg-green-900/30 dark:!text-green-400 flex items-center gap-1"
              @click="showAutoTagMenu = !showAutoTagMenu"
            >🏷 자동 태그<span class="text-[10px] opacity-60">▾</span></button>
            <div
              v-if="showAutoTagMenu"
              class="fixed top-10 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-[200] py-1.5"
              :style="autoTagMenuPos"
            >
              <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">소스 선택</p>
              <button
                v-for="p in availableProviders"
                :key="p.key"
                class="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                @click="openAutoTag(p.key)"
              ><img :src="p.logo" :alt="p.label" class="w-5 h-5 rounded object-cover shrink-0" />{{ p.label }}</button>
            </div>
          </div>
          <!-- LRC -->
          <div class="relative shrink-0" ref="lrcMenuRef">
            <button
              class="btn-toolbar !bg-purple-100 !text-purple-700 hover:!bg-purple-200 dark:!bg-purple-900/30 dark:!text-purple-400 disabled:opacity-40 flex items-center gap-1"
              :disabled="fetchingLyrics"
              @click="showLrcMenu = !showLrcMenu"
            >🎵 LRC<span class="text-[10px] opacity-60">▾</span></button>
            <div
              v-if="showLrcMenu"
              class="fixed top-10 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-[200] py-1.5"
              :style="lrcMenuPos"
            >
              <button
                v-for="src in [{key:'bugs',label:'Bugs'},{key:'lrclib',label:'LRCLIB'}]"
                :key="src.key"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors text-left"
                @click="startLrc(src.key)"
              ><span>🎵</span>{{ src.label }}</button>
            </div>
          </div>
          <!-- 전체 적용 -->
          <button
            v-if="workspaceStore.pendingCount > 0"
            class="btn-toolbar !bg-blue-100 !text-blue-700 hover:!bg-blue-200 dark:!bg-blue-900/30 dark:!text-blue-400 shrink-0 font-medium"
            @click="showApply = true"
          >✅ 적용 ({{ workspaceStore.pendingCount }})</button>
        </template>
        <template v-else>
          <span class="text-xs text-gray-400">워크스페이스가 비어있습니다. 사이드바에서 폴더를 열어 파일을 추가하세요.</span>
        </template>
        <button class="btn-toolbar shrink-0 ml-auto" @click="workspaceStore.loadCurrentSession()" title="새로고침">🔄</button>
      </div>
    </div>

    <!-- LRC 진행 패널 -->
    <Transition enter-from-class="opacity-0 -translate-y-1" leave-to-class="opacity-0 -translate-y-1" enter-active-class="transition duration-200" leave-active-class="transition duration-150">
      <div v-if="fetchingLyrics || lrcProgress.done" class="shrink-0 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-100 dark:border-purple-800 px-4 py-2 flex items-center gap-3">
        <span class="text-sm">🎵</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-semibold text-purple-700 dark:text-purple-300">
              {{ fetchingLyrics ? `LRC 검색 중 (${lrcProgress.current}/${lrcProgress.total})` : 'LRC 검색 완료' }}
            </span>
            <span class="text-xs text-purple-500">{{ lrcProgress.ok }}✅ {{ lrcProgress.notFound }}❌</span>
          </div>
          <div class="h-1 bg-purple-100 dark:bg-purple-800 rounded-full overflow-hidden">
            <div class="h-full bg-purple-500 rounded-full transition-all duration-300"
              :style="{ width: lrcProgress.total > 0 ? (lrcProgress.current / lrcProgress.total * 100) + '%' : '100%' }" />
          </div>
          <p v-if="lrcProgress.currentFile" class="text-[10px] text-purple-500 truncate mt-0.5">{{ lrcProgress.currentFile }}</p>
        </div>
        <button v-if="lrcProgress.done" class="text-purple-400 hover:text-purple-600 text-xs shrink-0" @click="lrcProgress.done = false">✕</button>
      </div>
    </Transition>

    <!-- ── 콘텐츠 영역 ── -->
    <div class="flex-1 flex overflow-hidden min-h-0">

      <!-- 파일 테이블 -->
      <div class="flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col" :class="showPanel ? 'hidden sm:flex sm:flex-col' : ''">

        <!-- 빈 상태 -->
        <div v-if="workspaceStore.items.length === 0" class="flex flex-col items-center justify-center h-full text-center p-8">
          <p class="text-5xl mb-4">📭</p>
          <p class="text-gray-500 dark:text-gray-400 text-sm mb-2">워크스페이스가 비어있습니다.</p>
          <p class="text-xs text-gray-400">사이드바의 <strong>폴더 열기</strong> 버튼으로 음악 파일을 추가하세요.</p>
        </div>

        <div v-else-if="workspaceStore.loading" class="flex items-center justify-center h-32">
          <p class="text-gray-400 text-sm">불러오는 중...</p>
        </div>

        <template v-else>
          <!-- 데스크톱 테이블 -->
          <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead class="sticky top-0 bg-gray-50 dark:bg-gray-900 z-10">
                <tr class="border-b border-gray-200 dark:border-gray-800">
                  <th class="w-8 px-2 py-2">
                    <input type="checkbox" class="w-3.5 h-3.5 rounded"
                      :checked="checkedIds.size === displayItems.length && displayItems.length > 0"
                      @change="toggleSelectAll" />
                  </th>
                  <th class="w-8 px-1 py-2"></th><!-- 상태 -->
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider w-8">#</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[160px]">제목</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[120px]">아티스트</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[120px]">앨범</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider w-16">연도</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider w-20">포맷</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                <tr
                  v-for="item in displayItems"
                  :key="item.id"
                  class="cursor-pointer transition-colors"
                  :class="workspaceStore.selectedItemId === item._workspace_item_id
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : checkedIds.has(item._workspace_item_id)
                    ? 'bg-blue-50/60 dark:bg-blue-900/15'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'"
                  @click="onRowClick(item)"
                >
                  <td class="px-2 py-2" @click.stop>
                    <input type="checkbox" class="w-3.5 h-3.5 rounded"
                      :checked="checkedIds.has(item._workspace_item_id)"
                      @change="toggleCheck(item._workspace_item_id)" />
                  </td>
                  <!-- 상태 배지 -->
                  <td class="px-1 py-2 text-center">
                    <span v-if="item._has_changes" class="inline-block w-1.5 h-1.5 rounded-full bg-yellow-400" title="변경됨"></span>
                    <span v-else-if="item._status === 'applied'" class="inline-block w-1.5 h-1.5 rounded-full bg-green-400" title="적용됨"></span>
                    <span v-else class="inline-block w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700" title="원본"></span>
                  </td>
                  <td class="px-2 py-2 text-xs text-gray-400 text-center font-mono">{{ item.track_no || '' }}</td>
                  <td class="px-2 py-2">
                    <p class="text-sm text-gray-900 dark:text-white truncate max-w-[200px]" :class="item._has_changes ? 'text-yellow-700 dark:text-yellow-300' : ''">
                      {{ item.title || item.filename }}
                    </p>
                    <p class="text-[10px] text-gray-400 truncate max-w-[200px]">{{ item.filename }}</p>
                  </td>
                  <td class="px-2 py-2 text-xs text-gray-600 dark:text-gray-400 truncate max-w-[140px]">{{ item.artist }}</td>
                  <td class="px-2 py-2 text-xs text-gray-600 dark:text-gray-400 truncate max-w-[140px]">{{ item.album_title }}</td>
                  <td class="px-2 py-2 text-xs text-gray-400 text-center">{{ item.year }}</td>
                  <td class="px-2 py-2">
                    <span v-if="item.file_format" class="text-[10px] px-1.5 py-0.5 rounded font-mono uppercase"
                      :class="formatBadgeClass(item.file_format)">{{ item.file_format }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 모바일 카드 -->
          <div class="md:hidden divide-y divide-gray-100 dark:divide-gray-800">
            <div
              v-for="item in displayItems"
              :key="item.id"
              class="flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors"
              :class="workspaceStore.selectedItemId === item._workspace_item_id
                ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-400'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border-l-2 border-transparent'"
              @click="onRowClick(item)"
            >
              <span class="w-1.5 h-1.5 rounded-full shrink-0 mt-1"
                :class="item._has_changes ? 'bg-yellow-400' : item._status === 'applied' ? 'bg-green-400' : 'bg-gray-200'"
              ></span>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-gray-900 dark:text-white truncate" :class="item._has_changes ? 'text-yellow-700 dark:text-yellow-300' : ''">
                  {{ item.title || item.filename }}
                </p>
                <p class="text-xs text-gray-400 truncate">{{ item.artist }} · {{ item.album_title }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 태그 패널 (우측) -->
      <div
        v-if="showPanel && workspaceStore.items.length > 0"
        class="w-full sm:w-80 lg:w-96 shrink-0 overflow-hidden"
      >
        <TagPanel
          v-if="showPanel === 'tag' && selectedFile"
          :file="selectedFile"
          :workspace-item="workspaceStore.selectedItem"
          @close="closePanel"
          @saved="onSaved"
        />
        <BatchTagPanel
          v-else-if="showPanel === 'batch'"
          :workspace-mode="true"
          :checked-workspace-ids="[...checkedIds]"
          @close="closePanel"
          @saved="onSaved"
        />
      </div>
    </div>

    <!-- 자동 태그 다이얼로그 -->
    <SpotifySearchDialog
      v-if="showSpotifyDialog"
      :initial-providers="selectedAutoProviders"
      :workspace-mode="true"
      :workspace-checked-ids="[...checkedIds]"
      @close="showSpotifyDialog = false"
      @applied="showSpotifyDialog = false"
    />

    <!-- 적용 미리보기 모달 -->
    <ApplyPreviewModal
      v-if="showApply"
      @close="showApply = false"
      @applied="showApply = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useToastStore } from '../stores/toast.js'
import { configApi } from '../api/config.js'
import { browseApi } from '../api/index.js'
import TagPanel from '../components/TagPanel.vue'
import BatchTagPanel from '../components/BatchTagPanel.vue'
import SpotifySearchDialog from '../components/SpotifySearchDialog.vue'
import ApplyPreviewModal from '../components/ApplyPreviewModal.vue'

const workspaceStore = useWorkspaceStore()
const toastStore = useToastStore()

const showPanel = ref(null)
const showApply = ref(false)
const showSpotifyDialog = ref(false)
const showAutoTagMenu = ref(false)
const showLrcMenu = ref(false)
const autoTagRef = ref(null)
const lrcMenuRef = ref(null)
const selectedAutoProviders = ref([])
const availableProviders = ref([])
const sortKey = ref('sort_order')
const checkedIds = reactive(new Set())

// ── 파일 목록 (workspace.files는 이미 변환됨) ─────────────────
const displayItems = computed(() => {
  const items = [...workspaceStore.files]
  if (sortKey.value === 'filename') items.sort((a, b) => a.filename.localeCompare(b.filename))
  else if (sortKey.value === 'title') items.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  else if (sortKey.value === 'artist') items.sort((a, b) => (a.artist || '').localeCompare(b.artist || ''))
  return items
})

const selectedFile = computed(() => {
  if (!workspaceStore.selectedItem) return null
  return workspaceStore.files.find(f => f._workspace_item_id === workspaceStore.selectedItemId) || null
})

// ── 선택 ──────────────────────────────────────────────────
function onRowClick(item) {
  checkedIds.clear()
  workspaceStore.selectItem(item._workspace_item_id)
  showPanel.value = 'tag'
}

function toggleCheck(id) {
  if (checkedIds.has(id)) checkedIds.delete(id)
  else checkedIds.add(id)
}

function toggleSelectAll() {
  if (checkedIds.size === displayItems.value.length && displayItems.value.length > 0) {
    checkedIds.clear()
    showPanel.value = null
  } else {
    displayItems.value.forEach(i => checkedIds.add(i._workspace_item_id))
    showPanel.value = 'batch'
  }
}

function closePanel() {
  showPanel.value = null
  workspaceStore.selectItem(null)
  checkedIds.clear()
}

function onSaved() { /* 스테이징 후 자동 반영 */ }

// ── 자동 태그 ────────────────────────────────────────────
const PROVIDER_META = {
  spotify: { label: 'Spotify', logo: '/logo/spotify.jpg' },
  bugs:    { label: 'Bugs',    logo: '/logo/bugs.jpg' },
  melon:   { label: 'Melon',  logo: '/logo/melon.jpg' },
  apple_music:           { label: 'Apple Music',           logo: '/logo/apple%20music.jpg' },
  apple_music_classical: { label: 'Apple Music Classical', logo: '/logo/Apple%20Music%20Classical.jpg' },
}

async function loadProviders() {
  try {
    const { data } = await configApi.get()
    const c = data.config
    const enabled = {
      spotify:               (c.spotify_enabled?.value ?? 'true') === 'true',
      bugs:                  (c.bugs_enabled?.value ?? 'true') === 'true',
      melon:                 (c.melon_enabled?.value ?? 'true') === 'true',
      apple_music:           c.apple_music_enabled?.value === 'true',
      apple_music_classical: c.apple_music_classical_enabled?.value === 'true',
    }
    availableProviders.value = Object.entries(enabled)
      .filter(([, v]) => v)
      .map(([k]) => ({ key: k, ...PROVIDER_META[k] }))
  } catch {
    availableProviders.value = [{ key: 'spotify', ...PROVIDER_META.spotify }]
  }
}

function openAutoTag(key) {
  selectedAutoProviders.value = [key]
  showAutoTagMenu.value = false
  showSpotifyDialog.value = true
}

function dropdownPos(ref) {
  if (!ref?.value) return {}
  const r = ref.value.getBoundingClientRect()
  return { right: (window.innerWidth - r.right) + 'px' }
}
const autoTagMenuPos = computed(() => showAutoTagMenu.value ? dropdownPos(autoTagRef) : {})
const lrcMenuPos     = computed(() => showLrcMenu.value     ? dropdownPos(lrcMenuRef)  : {})

// ── LRC ────────────────────────────────────────────────────
const fetchingLyrics = ref(false)
const lrcProgress = reactive({ total: 0, current: 0, ok: 0, notFound: 0, currentFile: '', done: false })

async function startLrc(source) {
  showLrcMenu.value = false
  const targets = checkedIds.size > 0
    ? workspaceStore.items.filter(i => checkedIds.has(i.id))
    : workspaceStore.items
  if (!targets.length) return

  fetchingLyrics.value = true
  Object.assign(lrcProgress, { total: targets.length, current: 0, ok: 0, notFound: 0, currentFile: '', done: false })

  for (let i = 0; i < targets.length; i++) {
    const item = targets[i]
    lrcProgress.current = i + 1
    lrcProgress.currentFile = item.filename
    try {
      const { data } = await browseApi.libraryFetchLyrics([item.file_path], source)
      const r = (data.results || [])[0]
      if (!r || r.status === 'ok') lrcProgress.ok++
      else lrcProgress.notFound++
    } catch { lrcProgress.notFound++ }
  }
  fetchingLyrics.value = false
  lrcProgress.done = true
  lrcProgress.currentFile = ''
  toastStore.success(`LRC 완료: ${lrcProgress.ok}개 저장`)
}

// ── 포맷 배지 ──────────────────────────────────────────────
function formatBadgeClass(fmt) {
  const map = {
    mp3: 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    flac: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    m4a: 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    ogg: 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    aac: 'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',
  }
  return map[(fmt || '').toLowerCase()] || 'bg-gray-100 dark:bg-gray-800 text-gray-500'
}

function onClickOutside(e) {
  if (autoTagRef.value && !autoTagRef.value.contains(e.target)) showAutoTagMenu.value = false
  if (lrcMenuRef.value  && !lrcMenuRef.value.contains(e.target))  showLrcMenu.value = false
}

onMounted(async () => {
  await workspaceStore.loadCurrentSession()
  await loadProviders()
  document.addEventListener('click', onClickOutside, true)
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
})
</script>
