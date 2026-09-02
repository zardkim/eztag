<template>
  <!-- 사이드바는 폴더 트리 전용.
       폴더 정보 / 커버 / 앨범카드 / 파일명 변경은 Browser 의 우측 인스펙터 패널(FolderInspectorPanel)로 이동했다. -->
  <div class="flex flex-col h-full min-h-0 select-none">
    <FolderTree ref="folderTreeRef" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FolderTree from './FolderTree.vue'

const folderTreeRef = ref(null)

defineExpose({
  refreshTree: () => folderTreeRef.value?.refreshRoots(),
})
</script>
