<template>
  <!-- 파일 목록 정렬 — 데스크톱은 경로 줄 우측(compact), 모바일은 목록 위 한 줄.
       둘 다 같은 상태(sortKey/sortOrder)를 쓰며 테이블 헤더 클릭과도 공유된다. -->
  <div class="flex items-center gap-1.5" :class="compact ? '' : 'gap-2 flex-wrap'">
    <span
      class="font-semibold text-gray-400 uppercase tracking-wider shrink-0"
      :class="compact ? 'text-[10px]' : 'text-[10px]'"
    >{{ t('browser.sortBy') }}</span>
    <select
      class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-400"
      :class="compact
        ? 'h-6 py-0 pl-1.5 pr-5 text-[11px] max-w-[140px]'
        : 'px-2 py-1 text-xs max-w-[48vw] sm:max-w-none'"
      :value="browserStore.sortKey"
      @change="browserStore.setSortKey($event.target.value)"
    >
      <option v-for="opt in sortOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
    </select>
    <!-- 오름/내림 토글 -->
    <div
      class="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shrink-0"
      :class="compact ? 'h-6' : ''"
    >
      <button
        class="transition-colors"
        :class="[
          compact ? 'px-1.5 text-[11px]' : 'px-2 py-1 text-xs',
          browserStore.sortOrder === 'asc'
            ? 'bg-blue-500 text-white'
            : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
        ]"
        :title="t('browser.sortAsc')"
        @click="browserStore.setSortOrder('asc')"
      >↑<span v-if="!compact" class="hidden sm:inline"> {{ t('browser.sortAscShort') }}</span></button>
      <button
        class="border-l border-gray-200 dark:border-gray-700 transition-colors"
        :class="[
          compact ? 'px-1.5 text-[11px]' : 'px-2 py-1 text-xs',
          browserStore.sortOrder === 'desc'
            ? 'bg-blue-500 text-white'
            : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
        ]"
        :title="t('browser.sortDesc')"
        @click="browserStore.setSortOrder('desc')"
      >↓<span v-if="!compact" class="hidden sm:inline"> {{ t('browser.sortDescShort') }}</span></button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useBrowserStore } from '../stores/browser.js'

defineProps({
  // 경로 줄에 끼워 넣는 축약형 (h-8 줄 안에 들어가야 한다)
  compact: { type: Boolean, default: false },
})

const { t } = useI18n()
const browserStore = useBrowserStore()

// 테이블 헤더가 설정할 수 있는 모든 키를 포함해야 한다.
// (빠지면 헤더 클릭 후 select 가 표시할 값을 잃는다)
const sortOptions = computed(() => [
  { key: 'filename',      label: t('browser.colFilename') },
  { key: 'title',         label: t('common.title') },
  { key: 'artist',        label: t('common.artist') },
  { key: 'album_artist',  label: t('browser.colAlbumArtist') },
  { key: 'album_title',   label: t('common.album') },
  { key: 'genre',         label: t('browser.colGenre') },
  { key: 'year',          label: t('browser.colYear') },
  { key: 'disc_no',       label: t('browser.colDisc') },
  { key: 'track_no',      label: t('browser.colTrack') },
  { key: 'file_format',   label: t('browser.colCodec') },
  { key: 'bitrate',       label: t('browser.colBitrate') },
  { key: 'sample_rate',   label: t('browser.colFrequency') },
  { key: 'duration',      label: t('browser.colDuration') },
  { key: 'modified_time', label: t('browser.colModified') },
])
</script>
