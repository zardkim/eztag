<template>
  <Teleport to="body">
    <Transition
      enter-from-class="opacity-0 scale-95"
      leave-to-class="opacity-0 scale-95"
      enter-active-class="transition duration-200"
      leave-active-class="transition duration-150"
    >
      <div
        v-if="true"
        :style="dialogStyle"
        class="fixed z-[9999] select-none"
      >
        <!-- ── 최소화: 플로팅 바 ── -->
        <div
          v-if="minimized"
          class="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 cursor-pointer"
          style="backdrop-filter:blur(8px); min-width:280px; max-width:380px;"
          @click="minimized = false"
        >
          <div class="w-10 h-10 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 shrink-0">
            <img v-if="file.has_cover" :src="coverUrl" class="w-full h-full object-cover" />
            <span v-else class="w-full h-full flex items-center justify-center text-sm">🎵</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold text-gray-900 dark:text-white truncate leading-tight">{{ file.title || file.filename }}</p>
            <p class="text-[10px] text-gray-400 truncate leading-tight">{{ file.artist || '—' }}</p>
          </div>
          <button class="text-blue-500 hover:text-blue-700 text-base px-1 shrink-0" @click.stop="togglePlay">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <span class="text-[10px] text-gray-400 shrink-0">{{ formatTime(currentTime) }}</span>
          <button class="text-gray-400 hover:text-red-500 text-xs px-1 shrink-0" @click.stop="$emit('close')">✕</button>
        </div>

        <!-- ── 펼친 상태: 다이얼로그 ── -->
        <div
          v-else
          class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden"
          style="width: min(540px, calc(100vw - 16px)); height: min(600px, 88vh);"
        >
          <!-- 헤더 (드래그 핸들) -->
          <div
            class="flex items-center justify-between px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 cursor-move shrink-0"
            @mousedown="startDrag"
          >
            <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">🎵 {{ t('player.title') }}</span>
            <div class="flex gap-1">
              <button
                class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                @click="minimized = true"
              >— {{ t('player.minimize') }}</button>
              <button
                class="text-gray-400 hover:text-red-500 text-xs px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                @click="$emit('close')"
              >✕</button>
            </div>
          </div>

          <!-- ── 모바일 레이아웃 (sm 미만) ── -->
          <div class="flex sm:hidden flex-col flex-1 min-h-0">
            <!-- 상단: 앨범아트 + 제목 + 컨트롤 (compact) -->
            <div class="flex items-center gap-3 px-4 pt-3 pb-2 shrink-0">
              <!-- 앨범아트 -->
              <div class="w-16 h-16 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow shrink-0">
                <img v-if="file.has_cover" :src="coverUrl" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-2xl">🎵</div>
              </div>
              <!-- 제목/아티스트 -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-gray-900 dark:text-white truncate leading-snug">{{ file.title || file.filename }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ file.artist || '—' }}</p>
                <p class="text-[10px] text-gray-400 truncate">{{ file.album_title }}</p>
              </div>
              <!-- 재생 버튼 -->
              <button
                class="w-10 h-10 rounded-full flex items-center justify-center bg-gray-100 hover:bg-gray-200 active:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 shrink-0"
                @click="togglePlay"
              >{{ isPlaying ? '⏸' : '▶' }}</button>
            </div>
            <!-- 프로그레스 바 -->
            <div class="flex items-center gap-1 px-4 pb-2 shrink-0">
              <span class="text-[10px] text-gray-400 w-7 text-right shrink-0">{{ formatTime(currentTime) }}</span>
              <input
                type="range" min="0" :max="duration || 100" step="0.1" :value="currentTime"
                class="flex-1 h-3 accent-blue-500 cursor-pointer"
                style="touch-action:pan-y;"
                @input="seek($event.target.value)"
                @change="seek($event.target.value)"
              />
              <span class="text-[10px] text-gray-400 w-7 shrink-0">{{ formatTime(duration) }}</span>
            </div>
            <!-- 가사 영역 -->
            <div class="flex-1 min-h-0 flex flex-col px-4 pb-3">
              <div class="flex items-center justify-between mb-1.5 shrink-0">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">{{ t('player.lyrics') }}</span>
                <span v-if="lyricsSource" class="text-[9px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400">
                  {{ lyricsSource === 'lrc_file' ? 'LRC' : t('player.embedded') }}
                </span>
              </div>
              <!-- 가사 없음 -->
              <div v-if="!lyricsContent && !loadingLyrics && !parsedLrc.length"
                class="flex-1 flex flex-col items-center justify-center gap-1 text-gray-400 dark:text-gray-600">
                <span class="text-2xl">🎼</span>
                <span class="text-xs">{{ t('player.noLyrics') }}</span>
              </div>
              <!-- 로딩 -->
              <div v-else-if="loadingLyrics" class="flex-1 flex items-center justify-center">
                <span class="text-xs text-gray-400 animate-pulse">{{ t('player.loadingLyrics') }}</span>
              </div>
              <!-- LRC 싱크 가사 -->
              <div
                v-else-if="parsedLrc.length > 0"
                ref="lyricsEl"
                class="flex-1 min-h-0 overflow-y-auto space-y-0.5 pr-1"
                style="scrollbar-width:thin;"
              >
                <div
                  v-for="(line, idx) in parsedLrc"
                  :key="idx"
                  :ref="el => setLineRef(idx, el)"
                  class="px-2 py-1.5 rounded-lg transition-all duration-200 cursor-pointer leading-snug"
                  :class="idx === currentLineIdx
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-semibold text-sm'
                    : 'text-gray-500 dark:text-gray-500 text-xs'"
                  @click="seekToLine(line.time)"
                >{{ line.text || '♪' }}</div>
              </div>
              <!-- 일반 텍스트 가사 -->
              <div v-else-if="lyricsContent"
                class="flex-1 min-h-0 overflow-y-auto text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line leading-relaxed pr-1"
                style="scrollbar-width:thin;">
                {{ lyricsContent }}
              </div>
            </div>
          </div>

          <!-- ── 데스크톱 레이아웃 (sm 이상) ── -->
          <div class="hidden sm:flex flex-row gap-4 p-4 flex-1 min-h-0">

            <!-- 왼쪽: 앨범아트 + 컨트롤 + 태그 -->
            <div class="flex flex-col gap-3 shrink-0 w-44 items-center">
              <!-- 앨범아트 -->
              <div class="w-40 h-40 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow-lg shrink-0">
                <img v-if="file.has_cover" :src="coverUrl" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-5xl">🎵</div>
              </div>
              <!-- 제목/아티스트/앨범 -->
              <div class="w-full text-center min-w-0">
                <p class="text-sm font-bold text-gray-900 dark:text-white truncate leading-snug">{{ file.title || file.filename }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ file.artist || '—' }}</p>
                <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ file.album_title }}</p>
              </div>
              <!-- 프로그레스 바 -->
              <div class="w-full flex items-center gap-1">
                <span class="text-[10px] text-gray-400 w-7 text-right shrink-0">{{ formatTime(currentTime) }}</span>
                <input
                  type="range" min="0" :max="duration || 100" step="0.1" :value="currentTime"
                  class="flex-1 h-3 accent-blue-500 cursor-pointer"
                  style="user-select:auto;-webkit-user-select:auto;touch-action:pan-y;"
                  @input="seek($event.target.value)"
                  @change="seek($event.target.value)"
                />
                <span class="text-[10px] text-gray-400 w-7 shrink-0">{{ formatTime(duration) }}</span>
              </div>
              <!-- 재생 버튼 -->
              <button
                class="self-center w-11 h-11 rounded-full flex items-center justify-center shadow-sm transition-colors bg-gray-100 hover:bg-gray-200 active:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 dark:active:bg-gray-500 text-gray-700 dark:text-gray-200"
                @click="togglePlay"
              >
                <span class="text-lg leading-none">{{ isPlaying ? '⏸' : '▶' }}</span>
              </button>
              <!-- 볼륨 -->
              <div class="w-full flex items-center gap-1.5">
                <span class="text-[11px] text-gray-400 shrink-0">🔊</span>
                <input
                  type="range" min="0" max="1" step="0.05" v-model.number="volume"
                  class="flex-1 h-3 accent-blue-500 cursor-pointer"
                  style="user-select:auto;-webkit-user-select:auto;touch-action:pan-y;"
                />
                <span class="text-[11px] text-gray-400 shrink-0 w-6 text-right">{{ Math.round(volume * 100) }}</span>
              </div>
              <!-- 태그 정보 -->
              <div class="w-full space-y-1 text-[10px] border-t border-gray-100 dark:border-gray-800 pt-2 overflow-y-auto">
                <div v-if="file.year" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.year') }}</span>
                  <span class="text-gray-700 dark:text-gray-300">{{ file.year }}</span>
                </div>
                <div v-if="file.genre" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.genre') }}</span>
                  <span class="text-gray-700 dark:text-gray-300 truncate">{{ file.genre }}</span>
                </div>
                <div v-if="file.track_no" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.track') }}</span>
                  <span class="text-gray-700 dark:text-gray-300">{{ file.track_no }}{{ file.total_tracks ? ' / ' + file.total_tracks : '' }}</span>
                </div>
                <div v-if="file.disc_no && file.disc_no > 1" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.disc') }}</span>
                  <span class="text-gray-700 dark:text-gray-300">{{ file.disc_no }}</span>
                </div>
                <div v-if="file.bitrate" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.bitrate') }}</span>
                  <span class="text-gray-700 dark:text-gray-300">{{ file.bitrate }} kbps</span>
                </div>
                <div v-if="file.file_format" class="flex gap-1">
                  <span class="text-gray-400 w-12 shrink-0">{{ t('player.format') }}</span>
                  <span class="text-gray-700 dark:text-gray-300 uppercase">{{ file.file_format }}</span>
                </div>
              </div>
            </div>

            <!-- 오른쪽: 가사 -->
            <div class="flex-1 min-w-0 min-h-0 flex flex-col">
              <div class="flex items-center justify-between mb-2 shrink-0">
                <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ t('player.lyrics') }}</span>
                <span v-if="lyricsSource" class="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400">
                  {{ lyricsSource === 'lrc_file' ? 'LRC' : t('player.embedded') }}
                </span>
              </div>
              <!-- 가사 없음 -->
              <div v-if="!lyricsContent && !loadingLyrics && !parsedLrc.length"
                class="flex-1 flex flex-col items-center justify-center gap-2 text-gray-400 dark:text-gray-600">
                <span class="text-3xl">🎼</span>
                <span class="text-sm">{{ t('player.noLyrics') }}</span>
              </div>
              <!-- 로딩 -->
              <div v-else-if="loadingLyrics" class="flex-1 flex items-center justify-center">
                <span class="text-sm text-gray-400 animate-pulse">{{ t('player.loadingLyrics') }}</span>
              </div>
              <!-- LRC 싱크 가사 -->
              <div
                v-else-if="parsedLrc.length > 0"
                ref="lyricsEl"
                class="flex-1 min-h-0 overflow-y-auto space-y-0.5 pr-1"
                style="scrollbar-width:thin;"
              >
                <div
                  v-for="(line, idx) in parsedLrc"
                  :key="idx"
                  :ref="el => setLineRef(idx, el)"
                  class="px-2 py-1.5 rounded-lg transition-all duration-200 cursor-pointer leading-snug"
                  :class="idx === currentLineIdx
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-semibold text-sm'
                    : 'text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-xs'"
                  @click="seekToLine(line.time)"
                >{{ line.text || '♪' }}</div>
              </div>
              <!-- 일반 텍스트 가사 -->
              <div v-else-if="lyricsContent"
                class="flex-1 min-h-0 overflow-y-auto text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line leading-relaxed pr-1"
                style="scrollbar-width:thin;">
                {{ lyricsContent }}
              </div>
            </div>
          </div>
        </div>

        <!-- 숨겨진 오디오 -->
        <audio
          ref="audioEl"
          :src="streamUrl"
          autoplay
          class="hidden"
          @timeupdate="onTimeUpdate"
          @loadedmetadata="onMetadata"
          @ended="isPlaying = false"
          @play="isPlaying = true"
          @pause="isPlaying = false"
        />
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'

const { t } = useI18n()

const props = defineProps({
  file: { type: Object, required: true },
})
const emit = defineEmits(['close'])

// ── 상태 ──────────────────────────────────────────────────
const minimized = ref(false)
const audioEl = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.5)

// 가사
const lyricsContent = ref('')
const lyricsSource = ref('')
const loadingLyrics = ref(false)
const parsedLrc = ref([])
const currentLineIdx = ref(-1)
const lyricsEl = ref(null)
// lineRefs: 인덱스 → DOM element 매핑 (plain object, not reactive)
const lineRefs = {}

function setLineRef(idx, el) {
  if (el) lineRefs[idx] = el
  else delete lineRefs[idx]
}

// ── 드래그 ────────────────────────────────────────────────
const playerW = Math.min(540, window.innerWidth - 16)
const playerH = Math.min(600, window.innerHeight * 0.88)
const posX = ref(Math.round((window.innerWidth - playerW) / 2))
const posY = ref(Math.round((window.innerHeight - playerH) / 2))
let dragOffset = null

const dialogStyle = computed(() => ({
  left: posX.value + 'px',
  top: posY.value + 'px',
}))

function startDrag(e) {
  dragOffset = { x: e.clientX - posX.value, y: e.clientY - posY.value }
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', stopDrag)
}
function onDragMove(e) {
  if (!dragOffset) return
  posX.value = Math.max(0, Math.min(window.innerWidth - 550, e.clientX - dragOffset.x))
  posY.value = Math.max(0, Math.min(window.innerHeight - 100, e.clientY - dragOffset.y))
}
function stopDrag() {
  dragOffset = null
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', stopDrag)
}

// ── computed ──────────────────────────────────────────────
const coverUrl = computed(() =>
  `/api/browse/file-cover?path=${encodeURIComponent(props.file.path)}`
)
const streamUrl = computed(() =>
  browseApi.streamUrl(props.file.path)
)
const hasLyrics = computed(() =>
  props.file.has_lrc || props.file.has_lyrics || !!props.file.lyrics
)

// ── LRC 파싱 ──────────────────────────────────────────────
function parseLrc(text) {
  if (!text) return []
  // BOM 제거
  const content = text.replace(/^\ufeff/, '')
  const lines = []

  // 타임스탬프 패턴 ([mm:ss.xxx] 또는 [mm:ss])
  const stampRe = /\[(\d{1,3}):(\d{2})(?:[.:,](\d{1,3}))?\]/g

  // 전체 컨텐츠에서 타임스탬프 위치를 모두 수집
  // (한 줄에 [t]가사[t]가사... 형식도 처리)
  const stamps = []
  let m
  while ((m = stampRe.exec(content)) !== null) {
    const mins = parseInt(m[1])
    const secs = parseInt(m[2])
    const ms = m[3] ? parseInt(m[3].padEnd(3, '0')) : 0
    stamps.push({ time: mins * 60 + secs + ms / 1000, start: m.index, end: m.index + m[0].length })
  }

  // 각 타임스탬프에 대해: 가사 = 다음 타임스탬프 시작 전까지의 텍스트
  for (let i = 0; i < stamps.length; i++) {
    const textStart = stamps[i].end
    const textEnd = i + 1 < stamps.length ? stamps[i + 1].start : content.length
    // 가사 텍스트 (줄바꿈은 공백으로)
    const lyric = content.slice(textStart, textEnd).replace(/\r?\n/g, ' ').trim()
    // time=0 이고 가사가 없으면 구분자 → 건너뜀
    if (stamps[i].time === 0 && !lyric) continue
    lines.push({ time: stamps[i].time, text: lyric })
  }

  return lines.sort((a, b) => a.time - b.time)
}

function isLrcFormat(text) {
  return text ? /\[\d{1,3}:\d{2}/.test(text) : false
}

// ── 가사 로드 ─────────────────────────────────────────────
async function loadLyrics() {
  if (!hasLyrics.value) return
  loadingLyrics.value = true
  parsedLrc.value = []
  lyricsContent.value = ''
  lyricsSource.value = ''
  // lineRefs 초기화
  Object.keys(lineRefs).forEach(k => delete lineRefs[k])
  try {
    const { data } = await browseApi.lrcContent(props.file.path)
    lyricsSource.value = data.source || ''
    const text = data.content || ''
    if (data.source === 'lrc_file' || isLrcFormat(text)) {
      parsedLrc.value = parseLrc(text)
      if (!parsedLrc.value.length && text) {
        lyricsContent.value = text
      }
    } else {
      lyricsContent.value = text
    }
  } catch {
    // 가사 없음
  } finally {
    loadingLyrics.value = false
  }
}

// ── 오디오 이벤트 ─────────────────────────────────────────
function onTimeUpdate() {
  if (!audioEl.value) return
  currentTime.value = audioEl.value.currentTime
  syncLrc()
}
function onMetadata() {
  if (!audioEl.value) return
  duration.value = audioEl.value.duration || 0
}
function togglePlay() {
  if (!audioEl.value) return
  if (isPlaying.value) audioEl.value.pause()
  else audioEl.value.play()
}
function seek(val) {
  if (!audioEl.value) return
  audioEl.value.currentTime = parseFloat(val)
}
function seekToLine(time) {
  if (!audioEl.value) return
  audioEl.value.currentTime = Math.max(0, time - 0.1)
  if (!isPlaying.value) audioEl.value.play()
}
watch(volume, (val) => {
  if (audioEl.value) audioEl.value.volume = val
})

// ── LRC 싱크 ─────────────────────────────────────────────
function syncLrc() {
  if (!parsedLrc.value.length) return
  const ct = currentTime.value
  let idx = -1
  for (let i = parsedLrc.value.length - 1; i >= 0; i--) {
    if (ct >= parsedLrc.value[i].time) { idx = i; break }
  }
  if (idx !== currentLineIdx.value) {
    currentLineIdx.value = idx
    scrollToLine(idx)
  }
}

function scrollToLine(idx) {
  if (idx < 0) return
  nextTick(() => {
    const container = lyricsEl.value
    const el = lineRefs[idx]
    if (!container || !el) return
    // 컨테이너 기준 중앙 스크롤 (scrollIntoView 대신 직접 계산)
    const containerH = container.clientHeight
    const elTop = el.offsetTop
    const elH = el.clientHeight
    const targetScroll = elTop - containerH / 2 + elH / 2
    container.scrollTo({ top: targetScroll, behavior: 'smooth' })
  })
}

// ── 유틸 ─────────────────────────────────────────────────
function formatTime(s) {
  if (!s || isNaN(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

// ── 파일 변경 ─────────────────────────────────────────────
watch(() => props.file?.path, () => {
  currentTime.value = 0
  duration.value = 0
  isPlaying.value = false
  currentLineIdx.value = -1
  parsedLrc.value = []
  lyricsContent.value = ''
  if (!minimized.value) loadLyrics()
})

watch(minimized, (val) => {
  if (!val && !lyricsContent.value && !parsedLrc.value.length) loadLyrics()
})

onMounted(() => {
  loadLyrics()
  if (audioEl.value) audioEl.value.volume = volume.value
})
onUnmounted(() => stopDrag())
</script>
