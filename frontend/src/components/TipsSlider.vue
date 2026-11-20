<template>
  <div
    class="relative h-full overflow-hidden rounded-2xl border-2 border-sky-200 dark:border-sky-800/80 bg-gradient-to-br from-sky-50 via-cyan-50 to-teal-50 dark:from-sky-950/40 dark:via-cyan-950/30 dark:to-teal-950/20"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
    @touchstart.passive="paused = true"
  >
    <!-- 슬라이드 -->
    <div class="relative h-[132px] sm:h-[116px] lg:h-[124px]">
      <Transition
        enter-active-class="transition duration-300 ease-out"
        leave-active-class="transition duration-300 ease-in absolute inset-0"
        enter-from-class="opacity-0 translate-x-4"
        leave-to-class="opacity-0 -translate-x-4"
        mode="out-in"
      >
        <div :key="index" class="h-full flex items-start gap-3 p-4">
          <div
            class="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-xl shadow-sm"
            :class="current.tone"
          >{{ current.icon }}</div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-gray-900 dark:text-white mb-1">{{ current.title }}</p>
            <p class="text-xs leading-relaxed text-gray-600 dark:text-gray-300 line-clamp-3">{{ current.body }}</p>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 하단 컨트롤 -->
    <div class="flex items-center gap-2 px-3 py-2 border-t border-sky-200/70 dark:border-sky-800/50">
      <button
        class="w-6 h-6 shrink-0 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :aria-label="t('home.tipPrev')"
        @click="go(-1)"
      >‹</button>
      <div class="flex-1 flex items-center justify-center gap-1.5">
        <button
          v-for="(tip, i) in tips"
          :key="i"
          class="h-1.5 rounded-full transition-all"
          :class="i === index ? 'w-4 bg-sky-500' : 'w-1.5 bg-sky-300/70 dark:bg-sky-700/70 hover:bg-sky-400'"
          :aria-label="`${i + 1}`"
          @click="select(i)"
        />
      </div>
      <button
        class="w-6 h-6 shrink-0 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :aria-label="t('home.tipNext')"
        @click="go(1)"
      >›</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm, rt, locale } = useI18n()

const TONES = [
  'bg-blue-100 dark:bg-blue-900/40',
  'bg-emerald-100 dark:bg-emerald-900/40',
  'bg-violet-100 dark:bg-violet-900/40',
  'bg-orange-100 dark:bg-orange-900/40',
  'bg-rose-100 dark:bg-rose-900/40',
  'bg-teal-100 dark:bg-teal-900/40',
]

// i18n 의 home.tips 배열을 그대로 쓴다. 언어를 바꾸면 자동으로 따라간다.
const tips = computed(() => {
  const raw = tm('home.tips') || []
  return raw.map((item, i) => ({
    icon:  rt(item.icon),
    title: rt(item.title),
    body:  rt(item.body),
    tone:  TONES[i % TONES.length],
  }))
})

const index = ref(0)
const paused = ref(false)
const current = computed(() => tips.value[index.value] || { icon: '💡', title: '', body: '', tone: TONES[0] })

function go(step) {
  const n = tips.value.length
  if (!n) return
  index.value = (index.value + step + n) % n
}
function select(i) { index.value = i }

// 언어가 바뀌면 첫 장으로
watch(locale, () => { index.value = 0 })

const INTERVAL_MS = 7000
let timer = null
onMounted(() => {
  timer = setInterval(() => { if (!paused.value) go(1) }, INTERVAL_MS)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
