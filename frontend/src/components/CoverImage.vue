<template>
  <!-- 커버 이미지. 두 경우를 함께 처리한다:
       · URL 이 아예 없는 경우 — Discogs 는 토큰 없이 검색하면 커버를 주지 않는다
       · URL 은 있는데 404 인 경우 — MusicBrainz 커버(Cover Art Archive)는
         없는 릴리스가 흔해서, 그대로 두면 깨진 이미지 아이콘이 뜬다 -->
  <img
    v-if="src && !failed"
    :src="src"
    :class="imgClass"
    loading="lazy"
    referrerpolicy="no-referrer"
    @error="failed = true"
  />
  <div v-else :class="[imgClass, 'bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-400']">
    <span :style="{ fontSize: iconSize }">{{ icon }}</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  imgClass: { type: String, default: 'w-12 h-12 rounded object-cover shrink-0' },
  icon: { type: String, default: '🎵' },
  iconSize: { type: String, default: '1.25rem' },
})

const failed = ref(false)
// 같은 자리에 다른 앨범이 들어오면 실패 상태를 푼다
watch(() => props.src, () => { failed.value = false })
</script>
