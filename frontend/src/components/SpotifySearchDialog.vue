<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">

      <!-- ── Header ── -->
      <div class="px-5 py-3.5 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3 shrink-0">
        <button
          v-if="mode !== 'search'"
          class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1 -ml-1 transition-colors text-sm"
          @click="mode = 'search'"
        >← 목록</button>
        <div class="flex-1 min-w-0">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ mode === 'search' ? '🎵 태그 검색' : mode === 'loading' ? '트랙 목록 로딩 중...' : '태그 비교 및 적용' }}
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
              placeholder="앨범명, 아티스트로 검색..."
              @keyup.enter="doSearch"
              ref="searchInput"
            />
            <button
              class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60 shrink-0"
              :disabled="searchLoading || !activeProviders.length"
              @click="doSearch"
            >{{ searchLoading ? '검색 중...' : '검색' }}</button>
          </div>
          <!-- 소스 선택 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-gray-400 shrink-0">소스:</span>
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
          <div v-if="searchLoading" class="flex items-center justify-center py-16 text-sm text-gray-400">검색 중...</div>
          <div v-else-if="searchError" class="text-center py-10 text-sm text-red-500">{{ searchError }}</div>
          <div v-else-if="results.length === 0 && searched" class="text-center py-10 text-sm text-gray-400">검색 결과가 없습니다.</div>

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
                <span v-if="result.total_tracks">· {{ result.total_tracks }}곡</span>
                <span v-if="result.label">· {{ result.label }}</span>
                <span v-if="result.genres && result.genres.length">· {{ result.genres[0] }}</span>
                <span v-if="result.genre && !result.genres">· {{ result.genre }}</span>
              </div>
            </div>
            <span class="text-xs text-blue-500 group-hover:text-blue-600 dark:text-blue-400 shrink-0 pr-1">선택 →</span>
          </div>
        </div>
      </template>

      <!-- ══════════════════ LOADING MODE ══════════════════ -->
      <div v-else-if="mode === 'loading'" class="flex-1 flex items-center justify-center text-sm text-gray-400">
        {{ providerLabel(loadingProvider) }} 트랙 목록 로딩 중...
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
                <span v-if="selectedAlbum.total_tracks">🎵 {{ selectedAlbum.total_tracks }}곡</span>
                <span v-if="selectedAlbum.label">🏷 {{ selectedAlbum.label }}</span>
                <span v-if="selectedAlbum.genres && selectedAlbum.genres.length">🎸 {{ selectedAlbum.genres.join(', ') }}</span>
                <span v-if="selectedAlbum.genre && !selectedAlbum.genres">🎸 {{ selectedAlbum.genre }}</span>
                <span v-if="selectedAlbum.popularity != null">⭐ {{ selectedAlbum.popularity }}/100</span>
              </div>
            </div>
          </div>

          <!-- 앨범 공통 태그 변경사항 -->
          <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">앨범 공통 태그 (전체 파일 적용)</p>
            <table class="w-full text-xs border-collapse">
              <thead>
                <tr class="border-b border-gray-100 dark:border-gray-800">
                  <th class="text-left py-1.5 text-gray-400 font-normal w-28">필드</th>
                  <th class="text-left py-1.5 text-gray-500 font-medium w-[38%]">현재 (첫 번째 파일 기준)</th>
                  <th class="text-left py-1.5 font-medium" :class="compareHeaderClass">{{ providerLabel(selectedAlbum.provider) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in albumRows"
                  :key="row.key"
                  class="border-b border-gray-50 dark:border-gray-800/40"
                  :class="row.changed ? 'bg-green-50/60 dark:bg-green-900/10' : ''"
                >
                  <td class="py-1.5 text-gray-400 pr-2">{{ row.label }}</td>
                  <td class="py-1.5 text-gray-600 dark:text-gray-400 pr-4">
                    <span v-if="row.current != null && row.current !== ''">{{ row.current }}</span>
                    <span v-else class="italic text-gray-300 dark:text-gray-600">없음</span>
                  </td>
                  <td class="py-1.5">
                    <span v-if="row.new != null && row.new !== ''" :class="row.changed ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-700 dark:text-gray-300'">
                      {{ row.new }}
                    </span>
                    <span v-else class="italic text-gray-300 dark:text-gray-600">없음</span>
                    <span v-if="row.changed" class="ml-1.5 text-[10px] bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1 rounded">변경</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 트랙별 매칭 -->
          <div class="px-5 py-3">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">트랙별 태그 (개별 적용)</p>
              <span class="text-xs text-gray-400">{{ matchedCount }}개 매칭 / {{ trackMatches.length }}개 항목</span>
            </div>
            <table class="w-full text-xs border-collapse">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700">
                  <th class="text-left py-1.5 text-gray-400 font-normal w-6">#</th>
                  <th class="text-left py-1.5 text-gray-500 font-medium w-[38%]">로컬 파일</th>
                  <th class="text-left py-1.5 font-medium" :class="compareHeaderClass">{{ providerLabel(selectedAlbum.provider) }} 트랙</th>
                  <th class="text-right py-1.5 text-gray-400 font-normal w-12">제목 변경</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(match, i) in trackMatches"
                  :key="i"
                  class="border-b border-gray-50 dark:border-gray-800/40"
                  :class="!match.local || !match.remote ? 'opacity-50' : ''"
                >
                  <td class="py-1.5 text-gray-400 whitespace-nowrap">
                    <span v-if="match.remote?.disc_no > 1" class="text-gray-300 dark:text-gray-600">{{ match.remote.disc_no }}-</span>{{ match.remote?.track_no || (i + 1) }}
                  </td>
                  <td class="py-1.5 pr-3">
                    <span v-if="match.local" class="text-gray-700 dark:text-gray-300 truncate block max-w-[200px]">{{ match.local.title || match.local.filename }}</span>
                    <span v-else class="italic text-gray-300 dark:text-gray-600">매칭 없음</span>
                  </td>
                  <td class="py-1.5">
                    <span v-if="match.remote" class="text-gray-700 dark:text-gray-300 truncate block max-w-[200px]">{{ match.remote.title }}</span>
                    <span v-else class="italic text-gray-300 dark:text-gray-600">매칭 없음</span>
                  </td>
                  <td class="py-1.5 text-right">
                    <span
                      v-if="match.local && match.remote && match.local.title !== match.remote.title"
                      class="text-[10px] bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1 rounded"
                    >변경</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-5 py-3.5 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0 bg-white dark:bg-gray-900">
          <p class="text-xs text-gray-400">
            앨범 공통 태그 → 전체 {{ targetPaths.length }}개 파일 ·
            트랙별 태그 → {{ matchedCount }}개 매칭 파일
          </p>
          <div class="flex gap-2">
            <button class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors" @click="$emit('close')">취소</button>
            <button
              class="px-5 py-2 bg-green-600 hover:bg-green-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60"
              :disabled="applying"
              @click="applyAll"
            >{{ applying ? '적용 중...' : '전체 적용' }}</button>
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
    return `${browserStore.checkedPaths.size}개 파일 선택됨`
  const folder = browserStore.selectedFolder
  return folder ? `📂 ${folder.name || folder.path} — 전체 ${browserStore.files.length}개 파일` : ''
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
    || browserStore.selectedFolder?.name
    || f?.title
    || ''
  await nextTick()
  searchInput.value?.focus()
  if (query.value) doSearch()
})

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
    searchError.value = '검색 실패. 소스 설정을 확인해 주세요.'
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
    { key: 'artist',       label: '아티스트',     current: c.artist,       new: s.album_artist || s.artist },
    { key: 'album_artist', label: '앨범 아티스트', current: c.album_artist, new: s.album_artist },
    { key: 'album_title',  label: '앨범',         current: c.album_title,  new: s.album_title || s.title },
    { key: 'genre',        label: '장르',         current: c.genre,        new: genre,         alwaysShow: true },
    { key: 'year',         label: '연도',         current: c.year,         new: s.year },
    { key: 'release_date', label: '발매일',       current: null,           new: s.release_date },
    { key: 'total_tracks', label: '총 트랙 수',   current: null,           new: s.total_tracks },
    { key: 'label',        label: '레이블',       current: null,           new: s.label },
    { key: 'description',  label: '앨범 소개',    current: null,           new: truncate(s.description), alwaysShow: true },
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
        for (const path of paths) {
          await metadataApi.applyByPath({ path, ...albumUpdates, cover_url: s.cover_url })
        }
        browserStore.updateFiles(paths, { ...albumUpdates, has_cover: true })
        const folderPath = browserStore.selectedFolder?.path
        if (folderPath) browserStore.invalidateFilesCache(folderPath)
      } else {
        await browseApi.batchWriteTags({ paths, ...albumUpdates })
        browserStore.updateFiles(paths, albumUpdates)
      }
    }

    // 2. 트랙별 태그 개별 적용
    for (const match of trackMatches.value) {
      if (!match.local || !match.remote) continue
      const rm = match.remote
      const trackUpdates = {}
      if (rm.title)    trackUpdates.title    = rm.title
      if (rm.track_no) trackUpdates.track_no = rm.track_no
      if (rm.disc_no)  trackUpdates.disc_no  = rm.disc_no
      if (rm.artist && rm.artist !== (s.album_artist || s.artist)) {
        trackUpdates.artist = rm.artist
      }
      if (Object.keys(trackUpdates).length) {
        await browseApi.writeTags({ path: match.local.path, ...trackUpdates })
        browserStore.updateFile({ path: match.local.path, ...trackUpdates })
      }
    }

    // 앨범 소개 DB 저장 (파일 태그 미기록)
    if (s.description) {
      const albumId = firstFile.value?.album_id
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
