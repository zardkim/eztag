<template>
  <Teleport to="body">
    <div
      class="fixed bottom-[72px] lg:bottom-5 left-1/2 lg:left-auto lg:right-5 -translate-x-1/2 lg:translate-x-0 z-[300] flex flex-col gap-2 items-center lg:items-end pointer-events-none"
    >
      <!-- LRC 작업 pill -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        leave-active-class="transition duration-150 ease-in"
        enter-from-class="opacity-0 scale-90 translate-y-2"
        leave-to-class="opacity-0 scale-90 translate-y-2"
      >
        <div
          v-if="showLrc"
          class="pointer-events-auto flex items-center gap-2 bg-purple-700 dark:bg-purple-800 text-white text-xs px-3 py-2 rounded-full shadow-lg cursor-pointer select-none max-w-[260px]"
          @click="goTo(jobStore.lrcJob)"
        >
          <span v-if="jobStore.lrcJob.running" class="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin shrink-0" />
          <span v-else class="shrink-0 text-sm">🎵</span>
          <span class="font-semibold shrink-0">LRC</span>
          <span class="shrink-0">{{ jobStore.lrcJob.current }}/{{ jobStore.lrcJob.total }}</span>
          <span v-if="jobStore.lrcJob.running && jobStore.lrcJob.currentFile" class="text-white/60 truncate">{{ jobStore.lrcJob.currentFile }}</span>
          <span v-if="jobStore.lrcJob.done" class="text-white/70 shrink-0">
            {{ jobStore.lrcJob.ok }}✅ {{ jobStore.lrcJob.notFound }}❌
          </span>
          <button
            class="shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-0.5 text-sm leading-none"
            @click.stop="jobStore.clearLrcJob()"
          >✕</button>
        </div>
      </Transition>

      <!-- YouTube 작업 pill -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        leave-active-class="transition duration-150 ease-in"
        enter-from-class="opacity-0 scale-90 translate-y-2"
        leave-to-class="opacity-0 scale-90 translate-y-2"
      >
        <div
          v-if="showYt"
          class="pointer-events-auto flex items-center gap-2 bg-red-600 dark:bg-red-700 text-white text-xs px-3 py-2 rounded-full shadow-lg cursor-pointer select-none max-w-[260px]"
          @click="goTo(jobStore.youtubeJob)"
        >
          <span v-if="jobStore.youtubeJob.running" class="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin shrink-0" />
          <span v-else class="shrink-0">▶</span>
          <span class="font-semibold shrink-0">YouTube</span>
          <span class="shrink-0">{{ jobStore.youtubeJob.current }}/{{ jobStore.youtubeJob.total }}</span>
          <span v-if="jobStore.youtubeJob.running && jobStore.youtubeJob.currentFile" class="text-white/60 truncate">{{ jobStore.youtubeJob.currentFile }}</span>
          <span v-if="jobStore.youtubeJob.done" class="text-white/70 shrink-0">
            {{ jobStore.youtubeJob.found }}✅
          </span>
          <button
            class="shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-0.5 text-sm leading-none"
            @click.stop="jobStore.clearYoutubeJob()"
          >✕</button>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useJobStore } from '../stores/job.js'

const jobStore = useJobStore()
const router = useRouter()
const route = useRoute()

// 현재 페이지가 작업 페이지가 아닐 때만 표시
const showLrc = computed(() =>
  !!jobStore.lrcJob && route.path !== jobStore.lrcJob.routePath
)
const showYt = computed(() =>
  !!jobStore.youtubeJob && route.path !== jobStore.youtubeJob.routePath
)

function goTo(job) {
  if (job?.routePath) router.push(job.routePath)
}
</script>
