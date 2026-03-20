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
          style="backdrop-filter:blur(8px); min-width:260px; max-width:340px;"
          @click="minimized = false"
        >
          <div class="w-8 h-8 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 shrink-0">
            <img v-if="file.has_cover" :src="coverUrl" class="w-full h-full object-cover" />
            <span v-else class="w-full h-full flex items-center justify-center text-sm">🎵</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold text-gray-900 dark:text-white truncate leading-tight">{{ file.title || file.filename }}</p>
            <p class="text-[10px] text-gray-400 truncate">{{ file.artist || '—' }}</p>
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
          class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col"
          style="width: min(520px, calc(100vw - 16px)); max-height: min(580px, 85vh);"
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

          <!-- 본문 -->
          <div class="flex flex-col sm:flex-row gap-4 p-4 flex-1 min-h-0 overflow-hidden">

            <!-- 왼쪽: 앨범아트 + 컨트롤 + 태그 -->
            <div class="flex flex-col items-center gap-3 shrink-0 sm:w-44 w-full">
              <!-- 앨범아트 -->
              <div class="w-28 h-28 sm:w-40 sm:h-40 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow-lg shrink-0">
                <img v-if="file.has_cover" :src="coverUrl" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-5xl">🎵</div>
              </div>

              <!-- 제목/아티스트/앨범 -->
              <div class="w-full text-center">
                <p class="text-sm font-bold text-gray-900 dark:text-white truncate leading-snug">{{ file.title || file.filename }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ file.artist || '—' }}</p>
                <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ file.album_title }}</p>
              </div>

              <!-- 프로그레스 바 -->
              <div class="w-full flex items-center gap-1">
                <span class="text-[10px] text-gray-400 w-7 text-right shrink-0">{{ formatTime(currentTime) }}</span>
                <input
                  type="range" min="0" :max="duration || 100" step="0.1" :value="currentTime"
                  class="flex-1 h-1.5 accent-blue-500 cursor-pointer"
                  @input="seek($event.target.value)"
                />
                <span class="text-[10px] text-gray-400 w-7 shrink-0">{{ formatTime(duration) }}</span>
              </div>

              <!-- 재생 버튼 -->
              <button
                class="w-10 h-10 rounded-full bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white flex items-center justify-center shadow-md transition-colors"
                @click="togglePlay"
              >
                <span class="text-lg leading-none">{{ isPlaying ? '⏸' : '▶' }}</span>
              </button>

              <!-- 볼륨 -->
              <div class="w-full flex items-center gap-1.5">
                <span class="text-[11px] text-gray-400 shrink-0">🔊</span>
                <input
                  type="range" min="0" max="1" step="0.05" :value="volume"
                  class="flex-1 h-1.5 accent-blue-500 cursor-pointer"
                  @input="setVolume($event.target.value)"
                />
              </div>

              <!-- 태그 정보 -->
              <div class="w-full space-y-1 text-[10px] border-t border-gray-100 dark:border-gray-800 pt-2">
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
            <div class="flex-1 min-w-0 flex flex-col min-h-0">
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
                class="flex-1 overflow-y-auto space-y-0.5 pr-1"
                style="scrollbar-width:thin;"
              >
                <div
                  v-for="(line, idx) in parsedLrc"
                  :key="idx"
                  :ref="el => { if (el) lineRefs[idx] = el }"
                  class="px-2 py-1.5 rounded-lg transition-all duration-200 cursor-pointer leading-snug"
                  :class="idx === currentLineIdx
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-semibold text-sm'
                    : 'text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-xs'"
                  @click="seekToLine(line.time)"
                >{{ line.text || '♪' }}</div>
              </div>

              <!-- 일반 텍스트 가사 -->
              <div v-else-if="lyricsContent"
                class="flex-1 overflow-y-auto text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line leading-relaxed pr-1"
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
const volume = ref(1)

// 가사
const lyricsContent = ref('')
const lyricsSource = ref('')
const loadingLyrics = ref(false)
const parsedLrc = ref([])
const currentLineIdx = ref(-1)
const lyricsEl = ref(null)
const lineRefs = ref([])

// ── 드래그 ────────────────────────────────────────────────
const playerW = Math.min(520, window.innerWidth - 16)
const playerH = Math.min(580, window.innerHeight * 0.85)
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
  posX.value = Math.max(0, Math.min(window.innerWidth - 530, e.clientX - dragOffset.x))
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
  const lines = []
  const re = /\[(\d{1,3}):(\d{2})(?:[.:,](\d{1,3}))?\](.*)/
  for (const raw of text.split('\n')) {
    const m = raw.match(re)
    if (!m) continue
    const mins = parseInt(m[1])
    const secs = parseInt(m[2])
    const ms = m[3] ? parseInt(m[3].padEnd(3, '0')) : 0
    const time = mins * 60 + secs + ms / 1000
    const line = m[4].trim()
    if (/^\[/.test(line)) continue
    lines.push({ time, text: line })
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
  lineRefs.value = []
  try {
    const { data } = await browseApi.lrcContent(props.file.path)
    lyricsSource.value = data.source || ''
    const text = data.content || ''
    if (isLrcFormat(text)) {
      parsedLrc.value = parseLrc(text)
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
function setVolume(val) {
  volume.value = parseFloat(val)
  if (audioEl.value) audioEl.value.volume = volume.value
}

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
async function scrollToLine(idx) {
  if (idx < 0 || !lyricsEl.value) return
  await nextTick()
  const el = lineRefs.value[idx]
  if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
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

onMounted(() => loadLyrics())
onUnmounted(() => stopDrag())
</script>
