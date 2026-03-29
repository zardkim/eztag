<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full sm:max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">

      <!-- ── Header ── -->
      <div class="px-5 py-3.5 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3 shrink-0">
        <button
          v-if="mode !== 'search'"
          class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1 -ml-1 transition-colors text-sm"
          @click="mode = 'search'"
        >{{ $t('tagSearch.backToList') }}</button>
        <div class="flex-1 min-w-0">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ mode === 'search' ? $t('tagSearch.titleSearch') : mode === 'loading' ? $t('tagSearch.titleLoading') : $t('tagSearch.titleCompare') }}
          </h2>
          <p class="text-xs text-gray-400 mt-0.5 truncate">{{ targetLabel }}</p>
        </div>
        <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1 transition-colors" @click="$emit('close')">✕</button>
      </div>

      <!-- ══════════════════ SEARCH MODE ══════════════════ -->
      <template v-if="mode === 'search'">
        <!-- 검색바 + 소스 선택 -->
        <div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 shrink-0 space-y-2">
          <div class="flex gap-2">
            <input
              v-model="query"
              class="field flex-1 text-sm"
              :placeholder="$t('tagSearch.searchPlaceholder')"
              @keyup.enter="doSearch"
              ref="searchInput"
            />
            <button
              class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60 shrink-0"
              :disabled="searchLoading || !activeProviders.length"
              @click="doSearch"
            >{{ searchLoading ? $t('tagSearch.searching') : $t('tagSearch.search') }}</button>
          </div>
          <!-- 소스 선택 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-gray-400 shrink-0">{{ $t('tagSearch.sourceLabel') }}</span>
            <template v-for="p in availableProviders" :key="p.key">
              <button
                class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all"
                :class="selectedProviders.includes(p.key)
                  ? `${p.activeBg} ${p.activeText} ${p.activeBorder} shadow-sm`
                  : 'bg-white dark:bg-gray-800 text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
                @click="toggleProvider(p.key)"
              >
                <img :src="p.logo" :alt="p.label" class="w-4 h-4 rounded object-cover shrink-0" />
                <span>{{ p.label }}</span>
              </button>
            </template>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-5 py-4 space-y-2">
          <div v-if="searchLoading" class="flex items-center justify-center py-16 text-sm text-gray-400">{{ $t('tagSearch.searching') }}</div>
          <div v-else-if="searchError" class="text-center py-10 text-sm text-red-500">{{ searchError }}</div>
          <div v-else-if="results.length === 0 && searched" class="text-center py-10 text-sm text-gray-400">{{ $t('tagSearch.noResults') }}</div>

          <div
            v-for="result in results"
            :key="(result.provider || 'sp') + '_' + (result.provider_id || result.spotify_id)"
            class="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 cursor-pointer transition-colors group"
            @click="selectAlbum(result)"
          >
            <img v-if="result.cover_url" :src="result.cover_url" class="w-14 h-14 rounded-lg object-cover shrink-0 shadow" />
            <div v-else class="w-14 h-14 rounded-lg bg-gray-200 dark:bg-gray-700 shrink-0 flex items-center justify-center text-gray-400">🎵</div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5 flex-wrap">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ result.album_title || result.title }}</p>
                <span v-if="result.album_type" class="text-[10px] px-1.5 bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 rounded capitalize shrink-0">{{ result.album_type }}</span>
                <span
                  class="inline-flex items-center gap-1 text-[10px] pl-1 pr-1.5 py-0.5 rounded shrink-0"
                  :class="providerBadgeClass(result.provider)"
                >
                  <img v-if="providerLogo(result.provider)" :src="providerLogo(result.provider)" class="w-3.5 h-3.5 rounded object-cover" />
                  {{ providerLabel(result.provider) }}
                </span>
              </div>
              <p class="text-xs text-gray-500 truncate">{{ result.album_artist || result.artist }}</p>
              <div class="flex gap-2 mt-0.5 text-xs text-gray-400 flex-wrap">
                <span v-if="result.release_date">{{ result.release_date }}</span>
                <span v-if="result.total_tracks">· {{ $t('tagSearch.trackCount', { n: result.total_tracks }) }}</span>
                <span v-if="result.label">· {{ result.label }}</span>
                <span v-if="result.genres && result.genres.length">· {{ result.genres[0] }}</span>
                <span v-if="result.genre && !result.genres">· {{ result.genre }}</span>
              </div>
            </div>
            <span class="text-xs text-blue-500 group-hover:text-blue-600 dark:text-blue-400 shrink-0 pr-1">{{ $t('tagSearch.selectArrow') }}</span>
          </div>
        </div>
      </template>

      <!-- ══════════════════ LOADING MODE ══════════════════ -->
      <div v-else-if="mode === 'loading'" class="flex-1 flex items-center justify-center text-sm text-gray-400">
        {{ $t('tagSearch.loadingTracks', { provider: providerLabel(loadingProvider) }) }}
      </div>

      <!-- ══════════════════ COMPARE MODE ══════════════════ -->
      <template v-else-if="mode === 'compare' && selectedAlbum">
        <div class="flex-1 overflow-y-auto">

          <!-- 앨범 정보 헤더 -->
          <div class="px-5 py-4 bg-gray-50 dark:bg-gray-800 flex gap-4 items-start border-b border-gray-200 dark:border-gray-700">
            <img v-if="selectedAlbum.cover_url" :src="selectedAlbum.cover_url" class="w-20 h-20 rounded-xl object-cover shadow shrink-0" />
            <div class="flex-1 min-w-0 text-sm">
              <div class="flex items-center gap-2 mb-0.5">
                <p class="font-bold text-gray-900 dark:text-white text-base truncate">{{ selectedAlbum.album_title || selectedAlbum.title }}</p>
                <span
                  class="inline-flex items-center gap-1 text-[10px] pl-1 pr-1.5 py-0.5 rounded shrink-0"
                  :class="providerBadgeClass(selectedAlbum.provider)"
                >
                  <img v-if="providerLogo(selectedAlbum.provider)" :src="providerLogo(selectedAlbum.provider)" class="w-3.5 h-3.5 rounded object-cover" />
                  {{ providerLabel(selectedAlbum.provider) }}
                </span>
              </div>
              <p class="text-gray-500 truncate">{{ selectedAlbum.album_artist || selectedAlbum.artist }}</p>
              <div class="flex gap-3 mt-1 text-xs text-gray-400 flex-wrap">
                <span v-if="selectedAlbum.release_date">📅 {{ selectedAlbum.release_date }}</span>
                <span v-if="selectedAlbum.total_tracks">🎵 {{ $t('tagSearch.trackCount', { n: selectedAlbum.total_tracks }) }}</span>
                <span v-if="selectedAlbum.label">🏷 {{ selectedAlbum.label }}</span>
                <span v-if="selectedAlbum.genres && selectedAlbum.genres.length">🎸 {{ selectedAlbum.genres.join(', ') }}</span>
                <span v-if="selectedAlbum.genre && !selectedAlbum.genres">🎸 {{ selectedAlbum.genre }}</span>
                <span v-if="selectedAlbum.popularity != null">⭐ {{ selectedAlbum.popularity }}/100</span>
              </div>
            </div>
          </div>

          <!-- 앨범 공통 태그 변경사항 -->
          <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{{ $t('tagSearch.albumCommonTags') }}</p>

            <!-- PC: 좌/우 비교 테이블 -->
            <table class="hidden sm:table w-full text-xs border-collapse">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-800">
                  <th class="text-left pb-2 pr-3 w-28 text-gray-400 font-medium">{{ $t('tagSearch.colField') }}</th>
                  <th class="text-left pb-2 px-3 text-gray-400 font-medium w-1/2">{{ $t('tagSearch.colBefore') }}</th>
                  <th class="text-left pb-2 pl-3 text-gray-400 font-medium w-1/2">{{ $t('tagSearch.colAfter') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in albumRows"
                  :key="row.key"
                  class="border-b border-gray-50 dark:border-gray-800/50 last:border-0"
                  :class="row.changed ? 'bg-green-50 dark:bg-green-900/10' : ''"
                >
                  <td class="py-1.5 pr-3 text-gray-500 dark:text-gray-400 whitespace-nowrap align-top">{{ row.label }}</td>
                  <td class="py-1.5 px-3 align-top max-w-0">
                    <div class="truncate" :class="row.changed ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-600 dark:text-gray-300'">
                      <span v-if="row.current != null && row.current !== ''">{{ row.current }}</span>
                      <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                    </div>
                  </td>
                  <td class="py-1.5 pl-3 align-top max-w-0">
                    <div class="truncate" :class="row.changed ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-700 dark:text-gray-300'">
                      <span v-if="row.new != null && row.new !== ''">{{ row.new }}</span>
                      <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 모바일: 카드 스타일 -->
            <div class="sm:hidden space-y-1.5">
              <div
                v-for="row in albumRows"
                :key="row.key"
                class="rounded-lg px-3 py-2 text-xs"
                :class="row.changed ? 'bg-green-50 dark:bg-green-900/10' : 'bg-gray-50 dark:bg-gray-800/40'"
              >
                <div class="flex items-start gap-2">
                  <span class="text-gray-400 shrink-0 w-20 pt-0.5">{{ row.label }}</span>
                  <div class="flex-1 min-w-0">
                    <div v-if="row.changed && row.current != null && row.current !== ''" class="text-gray-400 line-through truncate">{{ row.current }}</div>
                    <div :class="row.changed ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-700 dark:text-gray-300'" class="truncate">
                      <span v-if="row.new != null && row.new !== ''">{{ row.new }}</span>
                      <span v-else class="italic text-gray-300 dark:text-gray-600">{{ $t('tagSearch.colEmpty') }}</span>
                    </div>
                  </div>
                  <span v-if="row.changed" class="text-[10px] bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded shrink-0">{{ $t('tagSearch.changed') }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 트랙별 매칭 -->
          <div class="px-5 py-3">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ $t('tagSearch.trackTags') }}</p>
              <span class="text-xs text-gray-400">{{ $t('tagSearch.matchCount', { matched: matchedCount, total: trackMatches.length }) }}</span>
            </div>

            <!-- PC: 좌/우 비교 테이블 -->
            <table class="hidden sm:table w-full text-xs border-collapse">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-800">
                  <th class="text-right pb-2 pr-3 w-8 text-gray-400 font-medium">#</th>
                  <th class="text-left pb-2 px-3 text-gray-400 font-medium w-1/2">{{ $t('tagSearch.colBefore') }}</th>
                  <th class="text-left pb-2 pl-3 text-gray-400 font-medium w-1/2">{{ $t('tagSearch.colAfter') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(match, i) in trackMatches"
                  :key="i"
                  class="border-b border-gray-50 dark:border-gray-800/50 last:border-0"
                  :class="!match.local || !match.remote ? 'opacity-40' : ''"
                >
                  <td class="py-1.5 pr-3 text-gray-400 text-right whitespace-nowrap align-top">
                    <span v-if="match.remote?.disc_no > 1" class="text-gray-300 dark:text-gray-600">{{ match.remote.disc_no }}-</span>{{ match.remote?.track_no || (i + 1) }}.
                  </td>
                  <td class="py-1.5 px-3 text-gray-600 dark:text-gray-300 align-top max-w-0">
                    <div class="truncate">
                      <span v-if="match.local">{{ match.local.title || match.local.filename }}</span>
                      <span v-else class="italic text-gray-300 dark:text-gray-600">{{ $t('tagSearch.noMatch') }}</span>
                    </div>
                  </td>
                  <td class="py-1.5 pl-3 align-top max-w-0"
                    :class="match.local && match.remote && match.local.title !== match.remote.title
                      ? 'text-green-600 dark:text-green-400 font-medium'
                      : 'text-gray-700 dark:text-gray-300'"
                  >
                    <div class="truncate">
                      <span v-if="match.remote">{{ match.remote.title }}</span>
                      <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- 모바일: 수정전/수정후 2줄 카드 스타일 -->
            <div class="sm:hidden space-y-1.5">
              <div
                v-for="(match, i) in trackMatches"
                :key="i"
                class="rounded-lg px-3 py-2 text-xs"
                :class="!match.local || !match.remote
                  ? 'opacity-50 bg-gray-50 dark:bg-gray-800/40'
                  : (match.local.title !== match.remote.title
                      ? 'bg-green-50 dark:bg-green-900/10'
                      : 'bg-gray-50 dark:bg-gray-800/40')"
              >
                <div class="flex items-start gap-2">
                  <!-- 트랙 번호 -->
                  <span class="text-gray-400 shrink-0 w-6 text-right pt-0.5 leading-tight">
                    <span v-if="match.remote?.disc_no > 1" class="text-gray-300 dark:text-gray-600">{{ match.remote.disc_no }}-</span>{{ match.remote?.track_no || (i + 1) }}.
                  </span>
                  <!-- 수정전 / 수정후 2줄 -->
                  <div class="flex-1 min-w-0 space-y-0.5">
                    <!-- 수정전 -->
                    <div class="flex items-baseline gap-1.5">
                      <span class="text-[10px] text-gray-400 shrink-0 w-10">{{ $t('tagSearch.colBefore') }}</span>
                      <span
                        class="flex-1 truncate"
                        :class="match.local && match.remote && match.local.title !== match.remote.title
                          ? 'line-through text-gray-400 dark:text-gray-500'
                          : 'text-gray-600 dark:text-gray-300'"
                      >
                        <template v-if="match.local">{{ match.local.title || match.local.filename }}</template>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">{{ $t('tagSearch.noMatch') }}</span>
                      </span>
                    </div>
                    <!-- 수정후 -->
                    <div class="flex items-baseline gap-1.5">
                      <span class="text-[10px] text-gray-400 shrink-0 w-10">{{ $t('tagSearch.colAfter') }}</span>
                      <span
                        class="flex-1 truncate"
                        :class="match.local && match.remote && match.local.title !== match.remote.title
                          ? 'text-green-600 dark:text-green-400 font-medium'
                          : 'text-gray-700 dark:text-gray-300'"
                      >
                        <template v-if="match.remote">{{ match.remote.title }}</template>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                      </span>
                      <span
                        v-if="match.local && match.remote && match.local.title !== match.remote.title"
                        class="text-[10px] bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded shrink-0"
                      >{{ $t('tagSearch.changed') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-4 pt-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] border-t border-gray-200 dark:border-gray-800 shrink-0 bg-white dark:bg-gray-900">
          <p class="text-xs text-gray-400 mb-2.5">
            {{ $t('tagSearch.footerSummary', { files: targetPaths.length, matched: matchedCount }) }}
          </p>
          <div class="flex gap-2">
            <button
              class="flex-1 py-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors"
              @click="$emit('close')"
            >{{ $t('common.cancel') }}</button>
            <button
              class="flex-[2] py-3 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-60"
              :disabled="applying"
              @click="applyAll"
            >{{ applying ? $t('tagSearch.applying') : $t('tagSearch.applyAll') }}</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { metadataApi, browseApi, albumsApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { configApi } from '../api/config.js'
import { useToastStore } from '../stores/toast.js'

const props = defineProps({
  initialProviders: { type: Array, default: null },
})
const { t } = useI18n()
const browserStore = useBrowserStore()
const toastStore = useToastStore()
const emit = defineEmits(['close', 'applied'])

// ── 상태 ──────────────────────────────────────
const mode = ref('search')   // 'search' | 'loading' | 'compare'
const query = ref('')
const searchLoading = ref(false)
const applying = ref(false)
const searchError = ref('')
const results = ref([])
const searched = ref(false)
const selectedAlbum = ref(null)
const remoteTracks = ref([])    // 선택된 앨범의 트랙 목록 (provider 무관)
const loadingProvider = ref('spotify')
const searchInput = ref(null)

// ── 소스 설정 ──────────────────────────────────
const providerConfig = ref({ spotify: false, bugs: false })
const selectedProviders = ref([])

const activeProviders = computed(() =>
  selectedProviders.value.filter(p => providerConfig.value[p])
)

// ── 소스 버튼 목록 ────────────────────────────
const PROVIDER_META = {
  spotify:               { key: 'spotify',               label: 'Spotify',               logo: '/logo/spotify.jpg',                        activeBg: 'bg-green-50 dark:bg-green-900/30',      activeText: 'text-green-700 dark:text-green-300',      activeBorder: 'border-green-400 dark:border-green-600' },
  bugs:                  { key: 'bugs',                  label: 'Bugs',                  logo: '/logo/bugs.jpg',                           activeBg: 'bg-orange-50 dark:bg-orange-900/30',    activeText: 'text-orange-700 dark:text-orange-300',    activeBorder: 'border-orange-400 dark:border-orange-600' },
  apple_music:           { key: 'apple_music',           label: 'Apple Music',           logo: '/logo/apple%20music.jpg',                  activeBg: 'bg-red-50 dark:bg-red-900/30',          activeText: 'text-red-700 dark:text-red-300',          activeBorder: 'border-red-400 dark:border-red-600' },
  apple_music_classical: { key: 'apple_music_classical', label: 'Apple Music Classical', logo: '/logo/Apple%20Music%20Classical.jpg',       activeBg: 'bg-pink-50 dark:bg-pink-900/30',        activeText: 'text-pink-700 dark:text-pink-300',        activeBorder: 'border-pink-400 dark:border-pink-600' },
  melon:                 { key: 'melon',                 label: 'Melon',                 logo: '/logo/melon.jpg',                          activeBg: 'bg-emerald-50 dark:bg-emerald-900/30',  activeText: 'text-emerald-700 dark:text-emerald-300',  activeBorder: 'border-emerald-400 dark:border-emerald-600' },
}

const availableProviders = computed(() =>
  Object.values(PROVIDER_META).filter(p => providerConfig.value[p.key])
)

function toggleProvider(key) {
  const idx = selectedProviders.value.indexOf(key)
  if (idx >= 0) {
    // 마지막 하나는 해제 불가
    if (selectedProviders.value.length > 1) selectedProviders.value.splice(idx, 1)
  } else {
    selectedProviders.value.push(key)
  }
}

// ── 소스 표시 헬퍼 ────────────────────────────
function providerLabel(provider) {
  return { spotify: 'Spotify', bugs: 'Bugs', melon: 'Melon', apple_music: 'Apple Music', apple_music_classical: 'AM Classical' }[provider] || provider || ''
}
function providerLogo(provider) {
  return PROVIDER_META[provider]?.logo || null
}
function providerBadgeClass(provider) {
  return {
    spotify:               'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    bugs:                  'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    melon:                 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400',
    apple_music:           'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400',
    apple_music_classical: 'bg-pink-100 dark:bg-pink-900/40 text-pink-600 dark:text-pink-400',
  }[provider] || 'bg-gray-100 dark:bg-gray-800 text-gray-500'
}
const compareHeaderClass = computed(() => {
  return providerBadgeClass(selectedAlbum.value?.provider)
    .replace('bg-', 'text-')
    .split(' ').filter(c => c.startsWith('text-')).join(' ')
    || 'text-green-600 dark:text-green-400'
})

// ── 대상 파일 ──────────────────────────────────
const localFiles = computed(() =>
  browserStore.checkedPaths.size > 0
    ? browserStore.checkedFiles
    : browserStore.files
)
const targetPaths = computed(() => localFiles.value.map(f => f.path))
const firstFile = computed(() => localFiles.value[0] || null)

const targetLabel = computed(() => {
  if (browserStore.checkedPaths.size > 0)
    return t('tagSearch.targetSelected', { n: browserStore.checkedPaths.size })
  const folder = browserStore.selectedFolder
  return folder ? t('tagSearch.targetFolder', { folder: folder.name || folder.path, n: browserStore.files.length }) : ''
})

// ── 초기화 ────────────────────────────────────
onMounted(async () => {
  // 활성화된 소스 목록 로드
  try {
    const { data } = await configApi.get()
    const c = data.config
    providerConfig.value = {
      spotify:               (c.spotify_enabled?.value ?? 'true') === 'true',
      bugs:                  (c.bugs_enabled?.value ?? 'true') === 'true',
      apple_music:           c.apple_music_enabled?.value === 'true',
      apple_music_classical: c.apple_music_classical_enabled?.value === 'true',
      melon:                 (c.melon_enabled?.value ?? 'true') === 'true',
    }
    // 기본 선택: initialProviders prop 우선, 없으면 활성화된 소스 전체
    const allEnabled = Object.entries(providerConfig.value)
      .filter(([, v]) => v)
      .map(([k]) => k)
    selectedProviders.value = props.initialProviders
      ? props.initialProviders.filter(p => providerConfig.value[p])
      : allEnabled
  } catch {
    providerConfig.value = { spotify: true, bugs: true, apple_music: false, apple_music_classical: false, melon: true }
    selectedProviders.value = props.initialProviders ?? ['spotify', 'bugs', 'melon']
  }

  const f = firstFile.value
  query.value = f?.album_title
    || parseFolderNameToQuery(browserStore.selectedFolder?.name)
    || f?.title
    || ''
  await nextTick()
  searchInput.value?.focus()
  if (query.value) doSearch()
})

// ── 폴더명 파싱 (노이즈 제거 후 아티스트+앨범 추출) ──────────
function parseFolderNameToQuery(name) {
  if (!name) return ''
  let s = name
  // 연도: [2023], (2023), [2023.03.15], (2023-05)
  s = s.replace(/[\[(]\d{4}[\d.\s/-]*[\])]/g, '')
  // 오디오 포맷/품질: [FLAC], [MP3 320], [320kbps], [24bit-96kHz], [HQ], [Hi-Res] 등
  s = s.replace(/[\[(][^\]([]*?(flac|mp3|aac|wav|alac|ape|ogg|wma|\d+kbps?|\d+bit|\d+-\d+|hq|hi-?res|hifi|lossless)[^\]([]*[\])]/gi, '')
  // 음원 서비스 태그: [Bugs], [Melon], [Genie], [FLO], [Spotify] 등
  s = s.replace(/[\[(](bugs|melon|genie|flo|spotify|itunes|apple\s*music|youtube|soundcloud|tidal)[\])]/gi, '')
  // 에디션 정보: (Deluxe Edition), (Remastered 2021), (Special Version), (Re-release) 등
  s = s.replace(/\((deluxe|special|standard|limited|expanded|remaster(?:ed)?|edition|version|re-?release|anniversary|single|mini)[^)]*\)/gi, '')
  // 디스크/볼륨: [Disc 1], [CD1], [Vol.2] 등
  s = s.replace(/[\[(](disc|disk|cd|vol\.?)\s*\d+[\])]/gi, '')
  // 잔여 빈 괄호 및 앞뒤 공백 정리
  s = s.replace(/[\[(]\s*[\])]/g, '').replace(/\s{2,}/g, ' ').trim()
  // 끝에 남은 구분자 제거 (- _ . 로 끝나는 경우)
  s = s.replace(/[-_.]+$/, '').trim()
  return s
}

// ── 검색 ──────────────────────────────────────
async function doSearch() {
  const q = query.value.trim()
  if (!q || !activeProviders.value.length) return
  searchLoading.value = true
  searchError.value = ''
  results.value = []
  searched.value = false

  try {
    const searches = activeProviders.value.map(async (provider) => {
      // 앨범 검색
      const { data } = await metadataApi.search({ q, type: 'album', limit: 8, provider })
      if (data.results.length) return data.results
      // fallback: 트랙 검색
      const { data: td } = await metadataApi.search({ q, type: 'track', limit: 5, provider })
      return td.results
    })

    const allResults = await Promise.all(searches)
    results.value = allResults.flat()
    searched.value = true
  } catch {
    searchError.value = t('tagSearch.searchFailed')
  } finally {
    searchLoading.value = false
  }
}

// ── 앨범 선택 → 트랙 목록 로드 ────────────────
async function selectAlbum(album) {
  selectedAlbum.value = album
  remoteTracks.value = []
  const provider = album.provider || 'spotify'
  const id = album.provider_id || album.spotify_id
  loadingProvider.value = provider
  mode.value = 'loading'

  const hasAlbumTracks = album.type === 'album' || album.album_type || album.total_tracks

  if (id && hasAlbumTracks) {
    try {
      const { data } = await metadataApi.albumTracks(id, provider)
      remoteTracks.value = data.tracks || []
      // 앨범 상세 정보(장르, 레이블 등)를 selectedAlbum에 병합
      if (data.album && Object.keys(data.album).length) {
        selectedAlbum.value = { ...album, ...data.album }
      }
    } catch {
      remoteTracks.value = []
    }
  } else if (album.title) {
    remoteTracks.value = [album]
  }

  mode.value = 'compare'
}

// ── 트랙 매칭 ─────────────────────────────────
const trackMatches = computed(() => {
  const locals = [...localFiles.value].sort((a, b) => {
    if (a.track_no && b.track_no) return a.track_no - b.track_no
    return (a.filename || '').localeCompare(b.filename || '')
  })
  const remote = [...remoteTracks.value].sort((a, b) => {
    if (a.disc_no !== b.disc_no) return (a.disc_no || 1) - (b.disc_no || 1)
    return (a.track_no || 0) - (b.track_no || 0)
  })

  const matches = []
  const usedRemote = new Set()
  const trackKey = (t) => t.provider_id || t.spotify_id || t.title

  // track_no 기준 매칭 우선
  for (const local of locals) {
    let rm = null
    if (local.track_no) {
      rm = remote.find(r => !usedRemote.has(trackKey(r)) && r.track_no === local.track_no)
    }
    if (rm) usedRemote.add(trackKey(rm))
    matches.push({ local, remote: rm || null })
  }

  // 순서 기반 재매칭
  const unmatched = remote.filter(r => !usedRemote.has(trackKey(r)))
  let ui = 0
  for (const m of matches) {
    if (!m.remote && ui < unmatched.length) {
      m.remote = unmatched[ui++]
    }
  }
  for (; ui < unmatched.length; ui++) {
    matches.push({ local: null, remote: unmatched[ui] })
  }

  return matches
})

const matchedCount = computed(() =>
  trackMatches.value.filter(m => m.local && m.remote).length
)

// ── 앨범 공통 태그 비교 행 ───────────────────
const albumRows = computed(() => {
  if (!selectedAlbum.value || !firstFile.value) return []
  const c = firstFile.value
  const s = selectedAlbum.value
  const genre = s.genre || (s.genres && s.genres[0]) || null

  const truncate = (v, n = 80) => v && v.length > n ? v.slice(0, n) + '…' : v

  return [
    { key: 'artist',       label: t('tagSearch.fieldArtist'),       current: c.artist,       new: s.album_artist || s.artist },
    { key: 'album_artist', label: t('tagSearch.fieldAlbumArtist'),  current: c.album_artist, new: s.album_artist },
    { key: 'album_title',  label: t('tagSearch.fieldAlbum'),        current: c.album_title,  new: s.album_title || s.title },
    { key: 'genre',        label: t('tagSearch.fieldGenre'),        current: c.genre,        new: genre,         alwaysShow: true },
    { key: 'year',         label: t('tagSearch.fieldYear'),         current: c.year,         new: s.year },
    { key: 'release_date', label: t('tagSearch.fieldReleaseDate'),  current: null,           new: s.release_date },
    { key: 'total_tracks', label: t('tagSearch.fieldTotalTracks'),  current: null,           new: s.total_tracks },
    { key: 'label',        label: t('tagSearch.fieldLabel'),        current: null,           new: s.label },
    { key: 'description',  label: t('tagSearch.fieldDescription'),  current: null,           new: truncate(s.description), alwaysShow: true },
  ]
    .filter(r => r.alwaysShow || (r.new != null && r.new !== ''))
    .map(r => ({
      ...r,
      changed: r.current != null
        ? String(r.current) !== String(r.new)
        : false,
    }))
})

// ── 전체 적용 ─────────────────────────────────
async function applyAll() {
  if (!selectedAlbum.value) return
  applying.value = true
  const s = selectedAlbum.value
  const genre = s.genre || (s.genres && s.genres[0]) || null

  const albumUpdates = {}
  if (s.album_artist || s.artist) albumUpdates.artist       = s.album_artist || s.artist
  if (s.album_artist)             albumUpdates.album_artist = s.album_artist
  if (s.album_title || s.title)   albumUpdates.album_title  = s.album_title || s.title
  if (genre)                      albumUpdates.genre        = genre
  if (s.year)                     albumUpdates.year         = s.year
  if (s.release_date)             albumUpdates.release_date = s.release_date
  if (s.total_tracks)             albumUpdates.total_tracks = s.total_tracks
  if (s.label)                    albumUpdates.label        = s.label

  try {
    const paths = targetPaths.value

    // 1. 앨범 공통 태그 일괄 적용
    if (Object.keys(albumUpdates).length) {
      if (s.cover_url) {
        // 커버 포함: 파일별 applyByPath 병렬 처리
        await Promise.allSettled(
          paths.map(path => metadataApi.applyByPath({ path, ...albumUpdates, cover_url: s.cover_url }))
        )
        browserStore.updateFiles(paths, { ...albumUpdates, has_cover: true })
        const folderPath = browserStore.selectedFolder?.path
        if (folderPath) browserStore.invalidateFilesCache(folderPath)
      } else {
        await browseApi.batchWriteTags({ paths, ...albumUpdates })
        browserStore.updateFiles(paths, albumUpdates)
      }
    }

    // 2. 트랙별 태그: 병렬 처리
    const trackWriteJobs = trackMatches.value
      .filter(m => m.local && m.remote)
      .map(m => {
        const rm = m.remote
        const trackUpdates = {}
        if (rm.title)    trackUpdates.title    = rm.title
        if (rm.track_no) trackUpdates.track_no = rm.track_no
        if (rm.disc_no)  trackUpdates.disc_no  = rm.disc_no
        if (rm.artist && rm.artist !== (s.album_artist || s.artist)) trackUpdates.artist = rm.artist
        if (!Object.keys(trackUpdates).length) return null
        return browseApi.writeTags({ path: m.local.path, ...trackUpdates })
          .then(() => browserStore.updateFile({ path: m.local.path, ...trackUpdates }))
      })
      .filter(Boolean)
    if (trackWriteJobs.length) await Promise.allSettled(trackWriteJobs)

    // is_title_track 저장 (DB 전용 필드, Melon에서만 제공)
    const titleTrackJobs = trackMatches.value
      .filter(m => m.local && m.remote && m.remote.is_title_track !== undefined)
      .map(m =>
        browseApi.setTrackInfo({ path: m.local.path, is_title_track: !!m.remote.is_title_track })
          .then(() => browserStore.updateFile({ path: m.local.path, is_title_track: !!m.remote.is_title_track }))
          .catch(e => console.warn('is_title_track 저장 실패:', m.local.path, e))
      )
    if (titleTrackJobs.length) await Promise.allSettled(titleTrackJobs)

    // 앨범 소개 DB 저장 (파일 태그 미기록)
    if (s.description) {
      let albumId = firstFile.value?.album_id
      if (!albumId) {
        const title = (s.album_title || s.title || '').trim()
        const artist = (s.album_artist || s.artist || '').trim()
        if (title) {
          try {
            const { data } = await albumsApi.ensureAlbum(title, artist)
            albumId = data.id
          } catch (e) {
            console.warn('앨범 조회/생성 실패:', e)
          }
        }
      }
      if (albumId) {
        try {
          await albumsApi.setDescription(albumId, s.description)
        } catch (e) {
          console.warn('앨범 소개 저장 실패:', e)
        }
      }
    }

    // 캐시 무효화 + 파일 목록 재로드 (album_description 반영)
    const folderPath = browserStore.selectedFolder?.path
    if (folderPath) {
      browserStore.invalidateFilesCache(folderPath)
      browserStore.loadFiles(folderPath, true)
    }

    emit('applied')
    emit('close')
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    applying.value = false
  }
}
</script>
