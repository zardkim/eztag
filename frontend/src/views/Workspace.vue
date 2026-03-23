<template>
  <div class="flex flex-col h-full">

    <!-- ── 툴바 (데스크톱): App 상단 바에 Teleport ── -->
    <Teleport v-if="toolbarReady" to="#app-toolbar-slot">
      <div class="flex items-center gap-2 h-full px-4 overflow-x-auto scrollbar-none flex-1 min-w-0">
        <template v-if="workspaceStore.items.length > 0">
          <!-- 다중 선택 카운트 -->
          <span v-if="checkedIds.size > 0" class="text-xs text-blue-600 dark:text-blue-400 font-medium shrink-0">
            {{ $t('workspace.selectedCount', { n: checkedIds.size }) }}
            <button class="ml-1 text-gray-400 hover:text-gray-600" @click="checkedIds.clear()">✕</button>
          </span>
          <!-- 정렬 -->
          <select v-model="sortKey" class="text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-1.5 py-1 focus:outline-none shrink-0">
            <option value="sort_order">{{ $t('workspace.sortOrder') }}</option>
            <option value="filename">{{ $t('workspace.sortFilename') }}</option>
            <option value="title">{{ $t('workspace.sortTitle') }}</option>
            <option value="artist">{{ $t('workspace.sortArtist') }}</option>
          </select>
          <!-- 전체 선택 -->
          <button class="btn-toolbar shrink-0" @click="toggleSelectAll">
            {{ checkedIds.size === displayItems.length && displayItems.length > 0 ? $t('workspace.deselectAll') : $t('workspace.selectAll') }}
          </button>
          <!-- 배치 편집 -->
          <button
            class="btn-toolbar shrink-0"
            :class="showPanel === 'batch' ? 'btn-toolbar-active' : ''"
            @click="showPanel = showPanel === 'batch' ? null : 'batch'"
          >✏️ {{ $t('workspace.batchEdit') }}</button>
          <!-- 자동 태그 -->
          <div class="relative shrink-0" ref="autoTagRef">
            <button
              class="btn-toolbar !bg-green-100 !text-green-700 hover:!bg-green-200 dark:!bg-green-900/30 dark:!text-green-400 flex items-center gap-1"
              @click="showAutoTagMenu = !showAutoTagMenu"
            >🏷 {{ $t('workspace.autoTag') }}<span class="text-[10px] opacity-60">▾</span></button>
            <div
              v-if="showAutoTagMenu"
              class="fixed top-10 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-[200] py-1.5"
              :style="autoTagMenuPos"
            >
              <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ $t('workspace.selectSource') }}</p>
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
          >{{ $t('workspace.applyBtn', { n: workspaceStore.pendingCount }) }}</button>
          <!-- 폴더 이동 (모두 적용됨 + 단일 폴더) -->
          <button
            v-if="canMove"
            class="btn-toolbar !bg-indigo-100 !text-indigo-700 hover:!bg-indigo-200 dark:!bg-indigo-900/30 dark:!text-indigo-400 shrink-0 font-medium"
            @click="showMoveModal = true"
          >📦 {{ $t('workspace.moveFolder') }}</button>
        </template>
        <template v-else>
          <span class="text-xs text-gray-400">{{ $t('workspace.emptyToolbar') }}</span>
        </template>
        <button class="btn-toolbar shrink-0 ml-auto" @click="workspaceStore.loadCurrentSession()" title="새로고침">🔄</button>
      </div>
    </Teleport>

    <!-- ── 툴바 (모바일): App 상단 모바일 슬롯에 Teleport ── -->
    <Teleport v-if="toolbarReady" to="#app-toolbar-slot-mobile">
      <div class="flex items-center gap-1.5 h-full px-2 flex-1 min-w-0">
        <template v-if="workspaceStore.items.length > 0">
          <!-- 전체선택 -->
          <button
            class="btn-toolbar shrink-0 text-xs"
            :class="checkedIds.size > 0 ? 'btn-toolbar-active' : ''"
            @click="toggleSelectAll"
          >
            <template v-if="checkedIds.size === 0">{{ $t('workspace.selectAll') }}</template>
            <template v-else>{{ checkedIds.size }}/{{ displayItems.length }} ✕</template>
          </button>
          <!-- 배치 편집 -->
          <button
            class="btn-toolbar shrink-0 text-xs"
            :class="showPanel === 'batch' ? 'btn-toolbar-active' : ''"
            @click="showPanel = showPanel === 'batch' ? null : 'batch'"
          >✏️</button>
          <!-- 전체 적용 -->
          <button
            v-if="workspaceStore.pendingCount > 0"
            class="btn-toolbar !bg-blue-100 !text-blue-700 shrink-0 text-xs font-medium"
            @click="showApply = true"
          >{{ $t('workspace.applyBtn', { n: workspaceStore.pendingCount }) }}</button>
        </template>
        <div class="flex-1"></div>
        <button
          class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 shrink-0"
          @click="workspaceStore.loadCurrentSession()"
          title="새로고침"
        >🔄</button>
        <!-- 더보기 버튼 -->
        <button
          v-if="workspaceStore.items.length > 0"
          class="w-9 h-9 flex items-center justify-center rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 shrink-0 text-xl font-bold leading-none"
          @click="showMobileMobileMenu = true"
        >···</button>
      </div>
    </Teleport>

    <!-- ── 모바일 액션 바텀시트 ── -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200 ease-out" leave-active-class="transition duration-150 ease-in" enter-from-class="opacity-0" leave-to-class="opacity-0">
        <div v-if="showMobileMobileMenu" class="lg:hidden fixed inset-0 z-[120] flex flex-col justify-end" @click="showMobileMobileMenu = false">
          <div class="absolute inset-0 bg-black/40" />
          <Transition enter-active-class="transition duration-200 ease-out" leave-active-class="transition duration-150 ease-in" enter-from-class="translate-y-full" leave-to-class="translate-y-full">
            <div v-if="showMobileMobileMenu" class="relative bg-white dark:bg-gray-900 rounded-t-2xl shadow-2xl max-h-[80vh] flex flex-col" @click.stop>
              <div class="flex justify-center pt-3 pb-1 shrink-0">
                <div class="w-10 h-1 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
              </div>
              <div class="overflow-y-auto flex-1 px-3 pb-2 space-y-0.5">
                <!-- 자동 태그 -->
                <div class="border-b border-gray-100 dark:border-gray-800 pb-1 mb-1">
                  <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🏷 {{ $t('workspace.autoTag') }}</p>
                  <button
                    v-for="p in availableProviders"
                    :key="p.key"
                    class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
                    @click="openAutoTag(p.key); showMobileMobileMenu = false"
                  ><img :src="p.logo" :alt="p.label" class="w-5 h-5 rounded object-cover shrink-0" />{{ p.label }}</button>
                </div>
                <!-- LRC -->
                <div>
                  <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">🎵 LRC</p>
                  <button
                    v-for="src in [{key:'bugs',label:'Bugs'},{key:'lrclib',label:'LRCLIB'}]"
                    :key="src.key"
                    class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
                    :disabled="fetchingLyrics"
                    @click="startLrc(src.key); showMobileMobileMenu = false"
                  ><span class="text-xl">🎵</span>{{ src.label }}</button>
                </div>
                <!-- 폴더 이동 -->
                <button
                  v-if="canMove"
                  class="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors text-left"
                  @click="showMoveModal = true; showMobileMobileMenu = false"
                ><span class="text-xl">📦</span>{{ $t('workspace.moveFolder') }}</button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- LRC 진행 패널 -->
    <Transition enter-from-class="opacity-0 -translate-y-1" leave-to-class="opacity-0 -translate-y-1" enter-active-class="transition duration-200" leave-active-class="transition duration-150">
      <div v-if="fetchingLyrics || lrcProgress.done" class="shrink-0 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-100 dark:border-purple-800 px-4 py-2 flex items-center gap-3">
        <span class="text-sm">🎵</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-semibold text-purple-700 dark:text-purple-300">
              {{ fetchingLyrics ? $t('workspace.lrcSearching', { current: lrcProgress.current, total: lrcProgress.total }) : $t('workspace.lrcDone') }}
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
          <p class="text-gray-500 dark:text-gray-400 text-sm mb-2">{{ $t('workspace.empty') }}</p>
          <p class="text-xs text-gray-400" v-html="$t('workspace.emptyHint')"></p>
        </div>

        <div v-else-if="workspaceStore.loading" class="flex items-center justify-center h-32">
          <p class="text-gray-400 text-sm">{{ $t('workspace.loading') }}</p>
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
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[160px]">{{ $t('workspace.colTitle') }}</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[120px]">{{ $t('workspace.colArtist') }}</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider min-w-[120px]">{{ $t('workspace.colAlbum') }}</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider w-16">{{ $t('workspace.colYear') }}</th>
                  <th class="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider w-20">{{ $t('workspace.colFormat') }}</th>
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
                    <span v-if="item._has_changes" class="inline-block w-1.5 h-1.5 rounded-full bg-yellow-400" :title="$t('workspace.statusChanged')"></span>
                    <span v-else-if="item._status === 'applied'" class="inline-block w-1.5 h-1.5 rounded-full bg-green-400" :title="$t('workspace.statusApplied')"></span>
                    <span v-else class="inline-block w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700" :title="$t('workspace.statusOriginal')"></span>
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
        class="w-full sm:w-80 lg:w-96 shrink-0 overflow-y-auto max-h-full"
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

    <!-- 폴더 이동 모달 -->
    <MoveToDestinationModal
      v-if="showMoveModal && workspaceFolderPath"
      :source-path="workspaceFolderPath"
      :source-file-count="workspaceStore.items.length"
      @close="showMoveModal = false"
      @moved="onMoved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWorkspaceStore } from '../stores/workspace.js'
import { useToastStore } from '../stores/toast.js'
import { configApi } from '../api/config.js'
import { browseApi } from '../api/index.js'
import TagPanel from '../components/TagPanel.vue'
import BatchTagPanel from '../components/BatchTagPanel.vue'
import SpotifySearchDialog from '../components/SpotifySearchDialog.vue'
import ApplyPreviewModal from '../components/ApplyPreviewModal.vue'
import MoveToDestinationModal from '../components/MoveToDestinationModal.vue'

const { t } = useI18n()
const workspaceStore = useWorkspaceStore()
const toastStore = useToastStore()

const toolbarReady = ref(false)
const showPanel = ref(null)
const showApply = ref(false)
const showMoveModal = ref(false)
const showSpotifyDialog = ref(false)
const showAutoTagMenu = ref(false)
const showLrcMenu = ref(false)
const showMobileMobileMenu = ref(false)
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

// ── 이동(Move) ────────────────────────────────────────────
// 워크스페이스 아이템들의 공통 부모 폴더
const workspaceFolderPath = computed(() => {
  const items = workspaceStore.items
  if (!items.length) return null
  const folders = [...new Set(items.map(i => {
    const parts = i.file_path.split('/')
    parts.pop()
    return parts.join('/')
  }))]
  return folders.length === 1 ? folders[0] : null
})

// pending 변경 없음 + 단일 폴더 → 이동 가능
// (미편집 아이템은 status='pending'이지만 has_changes=false이므로 pendingCount에 포함 안 됨)
const canMove = computed(() =>
  workspaceStore.items.length > 0 &&
  workspaceStore.pendingCount === 0 &&
  workspaceFolderPath.value !== null
)

function onMoved(result) {
  showMoveModal.value = false
  toastStore.success(t('workspace.moveSuccess', { dest: result.dest }))
  workspaceStore.newSession()
}

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
  toastStore.success(t('workspace.lrcDoneToast', { n: lrcProgress.ok }))
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
  toolbarReady.value = true
  await workspaceStore.loadCurrentSession()
  await loadProviders()
  document.addEventListener('click', onClickOutside, true)
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
})
</script>
