<template>
  <div
    class="rounded-lg border overflow-hidden transition-colors"
    :class="applied ? 'border-green-500 dark:border-green-600' : 'border-gray-200 dark:border-gray-700'"
  >
    <!-- 상단: 커버 + 기본 정보 -->
    <div class="flex gap-3 p-3">
      <img
        v-if="result.cover_url"
        :src="result.cover_url"
        class="w-16 h-16 rounded object-cover shrink-0 shadow"
      />
      <div v-else class="w-16 h-16 rounded bg-gray-200 dark:bg-gray-700 shrink-0 flex items-center justify-center text-gray-400 text-xl">🎵</div>

      <div class="flex-1 min-w-0">
        <!-- 제목 + 뱃지 -->
        <div class="flex items-center gap-1.5 flex-wrap">
          <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">
            {{ result.title || result.album_title }}
          </p>
          <span v-if="result.explicit" class="text-[10px] px-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded shrink-0 font-bold">E</span>
          <span v-if="result.album_type" class="text-[10px] px-1.5 bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 rounded shrink-0 capitalize">{{ result.album_type }}</span>
        </div>

        <!-- 아티스트 -->
        <p class="text-xs text-gray-600 dark:text-gray-300 truncate mt-0.5">
          {{ result.artist || result.album_artist }}
        </p>

        <!-- 앨범 (트랙 검색 결과일 때) -->
        <p v-if="result.album_title && result.title" class="text-xs text-gray-400 truncate">
          {{ result.album_title }}
        </p>

        <!-- 날짜 + 트랙 수 + 재생시간 -->
        <div class="flex items-center gap-1.5 mt-1 flex-wrap text-xs text-gray-400">
          <span v-if="result.release_date">{{ result.release_date }}</span>
          <span v-else-if="result.year">{{ result.year }}</span>
          <span v-if="result.total_tracks">· {{ result.total_tracks }}곡</span>
          <span v-if="result.duration">· {{ formatDuration(result.duration) }}</span>
        </div>
      </div>
    </div>

    <!-- 상세 태그 테이블 -->
    <div class="px-3 pb-3 space-y-0.5 border-t border-gray-100 dark:border-gray-800 pt-2">
      <div v-if="result.album_artist && result.title" class="tag-row">
        <span class="tag-label">앨범 아티스트</span>
        <span class="tag-value">{{ result.album_artist }}</span>
      </div>
      <div v-if="result.track_no" class="tag-row">
        <span class="tag-label">트랙 번호</span>
        <span class="tag-value">{{ result.track_no }}</span>
      </div>
      <div v-if="result.disc_no" class="tag-row">
        <span class="tag-label">디스크</span>
        <span class="tag-value">{{ result.disc_no }}</span>
      </div>
      <div v-if="result.genre" class="tag-row">
        <span class="tag-label">장르</span>
        <span class="tag-value">{{ result.genre }}</span>
      </div>
      <div v-else-if="result.genres && result.genres.length" class="tag-row">
        <span class="tag-label">장르</span>
        <span class="tag-value">{{ result.genres.join(', ') }}</span>
      </div>
      <div v-if="result.label" class="tag-row">
        <span class="tag-label">레이블</span>
        <span class="tag-value">{{ result.label }}</span>
      </div>
      <div v-if="result.isrc" class="tag-row">
        <span class="tag-label">ISRC</span>
        <span class="tag-value font-mono">{{ result.isrc }}</span>
      </div>
      <div v-if="result.popularity != null" class="tag-row">
        <span class="tag-label">인기도</span>
        <span class="tag-value flex items-center gap-1.5">
          {{ result.popularity }}
          <span class="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full max-w-[60px]">
            <span class="block h-1 bg-green-400 rounded-full" :style="{ width: result.popularity + '%' }"></span>
          </span>
        </span>
      </div>
      <div v-if="result.spotify_url" class="pt-1">
        <a :href="result.spotify_url" target="_blank" rel="noopener"
           class="text-[11px] text-green-500 hover:text-green-400 hover:underline">
          🎵 Spotify에서 보기
        </a>
      </div>
    </div>

    <!-- 적용 버튼 -->
    <button
      class="w-full text-xs py-2 transition-colors border-t border-gray-200 dark:border-gray-700 font-medium"
      :class="applied
        ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400'
        : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'"
      @click="$emit('apply', result)"
    >
      {{ applied ? '✓ ' + $t('browser.spotifyApplied') : $t('browser.spotifyApply') }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  result: { type: Object, required: true },
  applied: { type: Boolean, default: false },
})
defineEmits(['apply'])

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.tag-row {
  @apply flex gap-2 min-w-0;
}
.tag-label {
  @apply text-[10px] text-gray-400 shrink-0 w-20 leading-[1.4] pt-px;
}
.tag-value {
  @apply text-[11px] text-gray-700 dark:text-gray-200 truncate leading-[1.4];
}
</style>
