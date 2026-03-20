<template>
  <div class="flex flex-col h-full">
    <!-- ── Toolbar Row 1: 메뉴 버튼 ── -->
    <div class="shrink-0 h-10 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
      <div class="flex items-center gap-2 h-full px-4 overflow-x-auto scrollbar-none">
        <template v-if="browserStore.selectedFolder && !browserStore.loading">
          <template v-if="browserStore.files.length > 0">
            <!-- 다중 선택 카운트 -->
            <span v-if="browserStore.checkedPaths.size > 0" class="text-xs text-blue-600 dark:text-blue-400 font-medium shrink-0">
              {{ t('browser.checkedCount', { n: browserStore.checkedPaths.size }) }}
              <button class="ml-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" @click="browserStore.setCheckedPaths(new Set())">✕</button>
            </span>
            <!-- 정렬 선택 -->
            <select
              v-model="browserStore.sortKey"
              class="text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-1.5 py-1 focus:outline-none shrink-0"
            >
              <option value="track_no">{{ t('browser.sortTrack') }}</option>
              <option value="filename">{{ t('browser.sortFilename') }}</option>
              <option value="artist">{{ t('browser.sortArtist') }}</option>
              <option value="album_title">{{ t('browser.sortAlbum') }}</option>
            </select>
            <button
              class="btn-toolbar px-2 shrink-0"
              :title="browserStore.sortOrder === 'asc' ? t('browser.sortDesc') : t('browser.sortAsc')"
              @click="browserStore.sortOrder = browserStore.sortOrder === 'asc' ? 'desc' : 'asc'"
            >{{ browserStore.sortOrder === 'asc' ? '↑' : '↓' }}</button>
            <!-- 전체선택 버튼 -->
            <button
              class="btn-toolbar shrink-0"
              :class="browserStore.checkedPaths.size === browserStore.displayFiles.length && browserStore.displayFiles.length > 0 ? 'btn-toolbar-active' : ''"
              @click="toggleSelectAll"
            >{{ t('browser.selectAll') }}</button>
            <button
              class="btn-toolbar shrink-0"
              :class="showPanel === 'tag' ? 'btn-toolbar-active' : ''"
              @click="openBatchPanel('tag')"
            >✏️ {{ $t('browser.editTag') }}</button>
            <!-- 자동 태그 드롭다운 -->
            <div class="relative shrink-0" ref="autoTagRef">
              <button
                class="btn-toolbar !bg-green-100 !text-green-700 hover:!bg-green-200 dark:!bg-green-900/30 dark:!text-green-400 flex items-center gap-1"
                @click="toggleAutoTagMenu"
              >🏷 {{ t('browser.autoTag') }}<span class="text-[10px] opacity-60">▾</span></button>
              <div
                v-if="showAutoTagMenu"
                class="fixed top-10 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-[200] py-1.5"
                :style="autoTagMenuPos"
              >
                <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('browser.selectSource') }}</p>
                <button
                  v-for="p in availableProviders"
                  :key="p.key"
                  class="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                  @click="openAutoTagSearch(p.key)"
                ><img :src="p.logo" :alt="p.label" class="w-5 h-5 rounded object-cover shrink-0" />{{ p.label }}</button>
              </div>
            </div>
            <!-- LRC 드롭다운 -->
            <div class="relative shrink-0" ref="lrcMenuRef">
              <button
                class="btn-toolbar !bg-purple-100 !text-purple-700 hover:!bg-purple-200 dark:!bg-purple-900/30 dark:!text-purple-400 disabled:opacity-40 flex items-center gap-1"
                :disabled="fetchingLyrics || (browserStore.checkedPaths.size === 0 && browserStore.files.length === 0)"
                @click="showLrcMenu = !showLrcMenu"
              >🎵 LRC<span class="text-[10px] opacity-60">▾</span></button>
              <div
                v-if="showLrcMenu"
                class="fixed top-10 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-[200] py-1.5"
                :style="lrcMenuPos"
              >
                <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('browser.lrcSourceLabel') }}</p>
                <!-- 자동 (설정 기반) -->
                <button
                  class="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors text-left"
                  @click="startFetchLyrics('auto')"
                >
                  <span class="text-base">⚡</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium">{{ t('browser.lrcAuto') }}</div>
                    <div class="text-[10px] text-gray-400 truncate">{{ lrcAutoDesc }}</div>
                  </div>
                </button>
                <div class="mx-3 my-1 border-t border-gray-100 dark:border-gray-700"></div>
                <p class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ t('browser.lrcManual') }}</p>
                <button
                  v-for="src in [{key:'bugs', label:'Bugs 뮤직 (한국어)'}, {key:'lrclib', label:'LRCLIB.net (국제)'}]"
                  :key="src.key"
                  class="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors text-left"
                  @click="startFetchLyrics(src.key)"
                ><span class="text-base">🎵</span>{{ src.label }}</button>
              </div>
            </div>
            <button
              class="btn-toolbar !bg-orange-100 !text-orange-700 hover:!bg-orange-200 dark:!bg-orange-900/30 dark:!text-orange-400 disabled:opacity-40 shrink-0"
              :disabled="browserStore.files.length === 0"
              @click="showRenameModal = true"
            >{{ t('browser.rename') }}</button>
            <button
              v-if="isLibrarySubfolder"
              class="btn-toolbar !bg-indigo-100 !text-indigo-700 hover:!bg-indigo-200 dark:!bg-indigo-900/30 dark:!text-indigo-400 shrink-0"
              @click="showMoveModal = true"
            >{{ t('browser.moveFolder.button') }}</button>
          </template>
          <button
            v-if="browserStore.files.length > 0"
            class="btn-toolbar !bg-teal-100 !text-teal-700 hover:!bg-teal-200 dark:!bg-teal-900/30 dark:!text-teal-400 disabled:opacity-40 shrink-0"
            :disabled="exportingHtml"
            @click="exportFolderHtml"
          >📄 {{ exportingHtml ? '...' : t('browser.exportHtml') }}</button>
          <button class="btn-toolbar shrink-0" @click="forceReload" title="새로고침">🔄</button>
        </template>
        <template v-else>
          <span class="text-xs text-gray-400">{{ $t('browser.selectFolder') }}</span>
        </template>
      </div>
    </div>

    <!-- ── Toolbar Row 2: 폴더 경로 ── -->
    <div class="shrink-0 h-8 border-b border-gray-100 dark:border-gray-800/60 bg-gray-50 dark:bg-gray-900/60">
      <div class="flex items-center h-full px-4 overflow-x-auto scrollbar-none gap-1 text-xs text-gray-500 dark:text-gray-400">
        <template v-if="browserStore.breadcrumb.length > 0">
          <!-- 루트 폴더 (첫 번째 crumb) — 현재 폴더와 같으면 생략 -->
          <button
            v-if="browserStore.breadcrumb.length > 1"
            class="hover:text-gray-900 dark:hover:text-white transition-colors truncate max-w-[160px]"
            :title="browserStore.breadcrumb[0].path"
            @click="navigateToCrumb(browserStore.breadcrumb[0], 0)"
          >{{ browserStore.breadcrumb[0].name }}</button>
          <span v-if="browserStore.breadcrumb.length > 1" class="text-gray-300 dark:text-gray-700 shrink-0 mx-0.5">-</span>
          <!-- 현재 폴더 (마지막 crumb) -->
          <button
            class="hover:text-gray-900 dark:hover:text-white transition-colors truncate text-gray-900 dark:text-white font-medium"
            :title="browserStore.breadcrumb[browserStore.breadcrumb.length - 1].path"
            @click="navigateToCrumb(browserStore.breadcrumb[browserStore.breadcrumb.length - 1], browserStore.breadcrumb.length - 1)"
          >{{ browserStore.breadcrumb[browserStore.breadcrumb.length - 1].name }}</button>
        </template>
        <span v-else class="text-gray-400 italic text-[11px]">{{ $t('browser.selectFolder') }}</span>
      </div>
    </div>

    <!-- LRC 진행 패널 -->
    <Transition enter-from-class="opacity-0 -translate-y-1" leave-to-class="opacity-0 -translate-y-1" enter-active-class="transition duration-200" leave-active-class="transition duration-150">
      <div v-if="fetchingLyrics || lrcProgress.done" class="shrink-0 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-100 dark:border-purple-800 px-4 py-2 flex items-center gap-3">
        <!-- 프로그레스 -->
        <span class="text-sm">🎵</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-semibold text-purple-700 dark:text-purple-300">
              {{ fetchingLyrics ? t('browser.lrcSearching', { current: lrcProgress.current, total: lrcProgress.total, source: lrcProgress.source }) : t('browser.lrcComplete') }}
            </span>
            <span class="text-xs text-purple-500 dark:text-purple-400">
              {{ lrcProgress.ok }}✅ {{ lrcProgress.notFound }}❌ {{ lrcProgress.noSync }}⚠️
            </span>
          </div>
          <div class="h-1 bg-purple-100 dark:bg-purple-800 rounded-full overflow-hidden">
            <div
              class="h-full bg-purple-500 rounded-full transition-all duration-300"
              :style="{ width: lrcProgress.total > 0 ? (lrcProgress.current / lrcProgress.total * 100) + '%' : (fetchingLyrics ? '100%' : '100%') }"
              :class="fetchingLyrics && lrcProgress.total === 0 ? 'animate-lrc-progress' : ''"
            />
          </div>
          <!-- 현재 파일 -->
          <p v-if="lrcProgress.currentFile" class="text-[10px] text-purple-500 dark:text-purple-400 truncate mt-0.5">{{ lrcProgress.currentFile }}</p>
        </div>
        <button v-if="lrcProgress.done" class="text-purple-400 hover:text-purple-600 text-xs shrink-0" @click="lrcProgress.done = false">✕</button>
      </div>
    </Transition>

    <!-- 태그 기반 파일명 변경 모달 -->
    <RenameByTagsModal
      v-if="showRenameModal"
      :files="renameTargetFiles"
      @close="showRenameModal = false"
      @renamed="onRenamed"
    />

    <!-- 폴더 이동 모달 -->
    <MoveToDestinationModal
      v-if="showMoveModal"
      :source-path="browserStore.selectedFolder?.path || ''"
      :source-file-count="browserStore.files.length"
      @close="showMoveModal = false"
      @moved="onMoved"
    />

    <!-- ── Content area ── -->
    <div class="relative flex-1 flex overflow-hidden min-h-0">
      <!-- File list -->
      <div
        ref="tableContainerRef"
        class="flex-1 overflow-y-auto overflow-x-hidden relative select-none min-h-0 flex flex-col"
        :class="showPanel ? 'hidden sm:flex sm:flex-col' : ''"
        @mousedown="onTableMouseDown"
      >
        <!-- 드래그 선택 오버레이 -->
        <div
          v-if="dragActive"
          class="pointer-events-none absolute border border-blue-400 bg-blue-400/10 z-20 rounded-sm"
          :style="dragOverlayStyle"
        />
        <!-- Empty state -->
        <div v-if="!browserStore.selectedFolder" class="flex flex-col items-center justify-center h-full text-center p-8">
          <p class="text-4xl mb-3">📁</p>
          <p class="text-gray-500 dark:text-gray-400 text-sm">{{ $t('browser.selectFolderHint') }}</p>
        </div>

        <div v-else-if="browserStore.loading" class="flex items-center justify-center h-32">
          <p class="text-gray-400 text-sm">{{ $t('common.loading') }}</p>
        </div>

        <div v-else-if="browserStore.files.length === 0 && (browserStore.subfolders?.length ?? 0) === 0" class="flex flex-col items-center justify-center h-32 text-center p-4">
          <p class="text-gray-400 text-sm">{{ $t('browser.noFiles') }}</p>
        </div>

        <template v-else>
          <!-- 권한 경고 -->
          <div v-if="browserStore.fileWarning" class="mx-4 mt-3 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-xs text-yellow-700 dark:text-yellow-400">
            ⚠️ {{ browserStore.fileWarning }}
          </div>

          <!-- 하위 폴더 그리드 -->
          <div v-if="(browserStore.subfolders?.length ?? 0) > 0" class="px-4 pt-3 pb-2">
            <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">{{ t('browser.subfolders') }}</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="folder in (browserStore.subfolders ?? [])"
                :key="folder.path"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600 transition-colors text-left group"
                @click="enterSubfolder(folder)"
              >
                <span class="text-yellow-400 text-base shrink-0">{{ folder.has_children ? '📂' : '📁' }}</span>
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-blue-700 dark:group-hover:text-blue-300 max-w-[280px] truncate">{{ folder.name }}</span>
                <span v-if="folder.has_audio" class="text-[9px] px-1 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-500 dark:text-blue-400 shrink-0">{{ t('browser.audioLabel') }}</span>
              </button>
            </div>
            <div v-if="browserStore.files.length > 0" class="mt-3 border-t border-gray-100 dark:border-gray-800"></div>
          </div>

          <!-- 이미지 / HTML 파일 -->
          <div v-if="(browserStore.extraFiles?.length ?? 0) > 0" class="px-4 pt-2 pb-2">
            <div v-if="(browserStore.subfolders?.length ?? 0) > 0 || browserStore.files.length > 0" class="mb-2 border-t border-gray-100 dark:border-gray-800"></div>
            <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">기타 파일</p>
            <div class="flex flex-wrap gap-2">
              <template v-for="ef in browserStore.extraFiles" :key="ef.path">
                <!-- 이미지 -->
                <div
                  v-if="ef.file_type === 'image'"
                  class="flex items-center gap-2 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-300"
                  :title="ef.filename"
                >
                  <img :src="browseApi.folderImageUrl(ef.path)" class="w-8 h-8 rounded object-cover bg-gray-100 dark:bg-gray-700" loading="lazy" />
                  <span class="max-w-[140px] truncate">{{ ef.filename }}</span>
                </div>
                <!-- HTML -->
                <a
                  v-else-if="ef.file_type === 'html'"
                  :href="`/api/browse/open-file?path=${encodeURIComponent(ef.path)}`"
                  target="_blank"
                  class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-orange-50 dark:hover:bg-orange-900/20 hover:border-orange-300 dark:hover:border-orange-600 transition-colors text-xs text-gray-600 dark:text-gray-300 hover:text-orange-700 dark:hover:text-orange-300"
                  :title="ef.filename"
                >
                  <span class="text-base shrink-0">📄</span>
                  <span class="max-w-[160px] truncate">{{ ef.filename }}</span>
                </a>
              </template>
            </div>
          </div>

          <!-- 앨범 설명 -->
          <div v-if="browserStore.albumDescription" class="mx-4 mt-2 mb-1 px-4 py-3 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-xl">
            <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">앨범 소개</p>
            <p class="text-xs text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-wrap line-clamp-4" :title="browserStore.albumDescription">{{ browserStore.albumDescription }}</p>
          </div>

          <!-- 필터 결과 없음 -->
          <div v-if="browserStore.files.length > 0 && browserStore.displayFiles.length === 0" class="flex items-center justify-center h-24">
            <p class="text-gray-400 text-sm">검색 결과가 없습니다.</p>
          </div>

          <!-- ── 모바일 카드 뷰 (md 미만) ── -->
          <div v-if="browserStore.displayFiles.length > 0" class="md:hidden divide-y divide-gray-100 dark:divide-gray-800">
            <div
              v-for="file in browserStore.displayFiles"
              :key="file.path"
              class="flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors"
              :class="browserStore.selectedFile?.path === file.path
                ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-400 dark:border-blue-500'
                : browserStore.checkedPaths.has(file.path)
                ? 'bg-blue-50/60 dark:bg-blue-900/15 border-l-2 border-blue-300 dark:border-blue-600'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border-l-2 border-transparent'"
              @click="onRowClick(file, $event)"
            >
              <!-- 커버 -->
              <div class="w-10 h-10 rounded overflow-hidden bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                <img v-if="file.has_cover" :src="`/api/browse/file-cover?path=${encodeURIComponent(file.path)}`" class="w-full h-full object-cover" loading="lazy" />
                <span v-else class="text-gray-300 dark:text-gray-600 text-sm">🎵</span>
              </div>
              <!-- 정보 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ file.title || file.filename }}</p>
                  <span v-if="file.file_format" class="text-[9px] font-mono font-semibold px-1 py-0.5 rounded shrink-0" :class="formatBadgeClass(file.file_format)">{{ file.file_format }}</span>
                  <span v-if="file.has_lrc" class="text-[9px] font-semibold px-1 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 shrink-0">LRC</span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ file.artist }}<span v-if="file.artist && file.album_title"> · </span>{{ file.album_title }}</p>
                <div class="flex items-center gap-2 text-[10px] text-gray-400 mt-0.5">
                  <span v-if="file.track_no">{{ file.track_no }}번</span>
                  <span v-if="file.year">{{ file.year }}</span>
                  <span v-if="file.duration">{{ formatDuration(file.duration) }}</span>
                  <span v-if="file.bitrate">{{ file.bitrate }}k</span>
                </div>
              </div>
              <!-- 플레이 버튼 -->
              <button
                class="shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-gray-300 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
                :class="currentPlay?.path === file.path ? 'text-blue-500' : ''"
                :title="t('browser.play')"
                @click.stop="currentPlay = file"
              >{{ currentPlay?.path === file.path ? '⏸' : '▶' }}</button>
            </div>
          </div>

          <!-- ── 데스크톱 테이블 뷰 (md 이상) ── -->
          <div v-if="browserStore.displayFiles.length > 0" class="hidden md:flex md:flex-col md:flex-1 overflow-x-auto">
          <table class="w-full min-w-[1400px] text-sm">
              <thead class="sticky top-0 bg-gray-50 dark:bg-gray-800 z-10">
                <tr class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  <th class="text-center px-2 py-2 font-medium w-12">디스크</th>
                  <th class="text-center px-2 py-2 font-medium w-12">트랙</th>
                  <th class="w-9 shrink-0"></th>
                  <th class="text-left px-2 py-2 font-medium min-w-[160px]">{{ $t('common.title') }}</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[110px]">{{ $t('common.artist') }}</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[110px]">앨범 아티스트</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[110px]">{{ $t('common.album') }}</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[80px]">장르</th>
                  <th class="text-center px-2 py-2 font-medium w-14">연도</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[100px]">설명</th>
                  <th class="text-center px-2 py-2 font-medium w-16">코덱</th>
                  <th class="text-center px-2 py-2 font-medium w-12">LRC</th>
                  <th class="text-center px-2 py-2 font-medium w-16">태그버전</th>
                  <th class="text-center px-2 py-2 font-medium w-20">비트레이트</th>
                  <th class="text-center px-2 py-2 font-medium w-20">주파수</th>
                  <th class="text-center px-2 py-2 font-medium w-16">길이</th>
                  <th class="text-left px-3 py-2 font-medium min-w-[130px]">수정된 일시</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="file in browserStore.displayFiles"
                  :key="file.path"
                  class="group border-t border-gray-100 dark:border-gray-800 cursor-pointer transition-colors"
                  :class="browserStore.selectedFile?.path === file.path
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-400 dark:border-blue-500'
                    : browserStore.checkedPaths.has(file.path)
                    ? 'bg-blue-50/60 dark:bg-blue-900/15 border-l-2 border-blue-300 dark:border-blue-600'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border-l-2 border-transparent'"
                  @click="onRowClick(file, $event)"
                >
                  <td class="px-2 py-2 text-center text-gray-400 text-xs">{{ file.disc_no ?? '' }}</td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs">{{ file.track_no ?? '' }}</td>
                  <td class="py-1 pl-2 shrink-0">
                    <div class="w-8 h-8 rounded overflow-hidden bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                      <img v-if="file.has_cover" :src="`/api/browse/file-cover?path=${encodeURIComponent(file.path)}`" class="w-full h-full object-cover" loading="lazy" />
                      <span v-else class="text-gray-300 dark:text-gray-600 text-xs">🎵</span>
                    </div>
                  </td>
                  <td class="px-2 py-2 max-w-[200px]">
                    <div class="flex items-center gap-1.5">
                      <button
                        class="shrink-0 w-5 h-5 flex items-center justify-center rounded-full text-gray-300 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors opacity-0 group-hover:opacity-100"
                        :class="currentPlay?.path === file.path ? '!opacity-100 text-blue-500' : ''"
                        :title="t('browser.play')"
                        @click.stop="currentPlay = file"
                      >{{ currentPlay?.path === file.path ? '⏸' : '▶' }}</button>
                      <p class="truncate text-gray-900 dark:text-white font-medium">{{ file.title || file.filename }}</p>
                    </div>
                  </td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-[130px]">
                    <p class="truncate">{{ file.artist }}</p>
                  </td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-[130px]">
                    <p class="truncate">{{ file.album_artist }}</p>
                  </td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-[130px]">
                    <p class="truncate">{{ file.album_title }}</p>
                  </td>
                  <td class="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs max-w-[100px]">
                    <p class="truncate">{{ file.genre }}</p>
                  </td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs">{{ file.year ?? '' }}</td>
                  <td class="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs max-w-[120px]">
                    <p class="truncate">{{ file.comment }}</p>
                  </td>
                  <td class="px-2 py-2 text-center">
                    <span v-if="file.file_format" class="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded" :class="formatBadgeClass(file.file_format)">{{ file.file_format }}</span>
                  </td>
                  <td class="px-2 py-2 text-center">
                    <span v-if="file.has_lrc" class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400">LRC</span>
                  </td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs font-mono">{{ file.tag_version }}</td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs">{{ file.bitrate ? `${file.bitrate}k` : '' }}</td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs">{{ formatHz(file.sample_rate) }}</td>
                  <td class="px-2 py-2 text-center text-gray-400 text-xs font-mono">{{ formatDuration(file.duration) }}</td>
                  <td class="px-3 py-2 text-gray-400 text-xs font-mono whitespace-nowrap">{{ formatDateTime(file.modified_time) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>

      <!-- 미니 플레이어 (다이얼로그) -->
      <MiniPlayer
        v-if="currentPlay"
        :file="currentPlay"
        @close="currentPlay = null"
      />

      <!-- Batch Tag Panel (right) -->
      <div
        v-if="showPanel && browserStore.files.length > 0"
        class="w-full sm:w-80 lg:w-96 shrink-0 overflow-hidden"
      >
        <BatchTagPanel
          :focus-spotify="false"
          @close="closePanel"
          @saved="onSaved"
        />
      </div>
    </div>

    <!-- 자동 태그 검색 다이얼로그 -->
    <SpotifySearchDialog
      v-if="showSpotifyDialog"
      :initial-providers="selectedAutoProviders"
      @close="showSpotifyDialog = false"
      @applied="showSpotifyDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import BatchTagPanel from '../components/BatchTagPanel.vue'
import SpotifySearchDialog from '../components/SpotifySearchDialog.vue'
import RenameByTagsModal from '../components/RenameByTagsModal.vue'
import MoveToDestinationModal from '../components/MoveToDestinationModal.vue'
import MiniPlayer from '../components/MiniPlayer.vue'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import { configApi } from '../api/config.js'
import { browseApi } from '../api/index.js'
import { downloadBlob } from '../utils/download.js'

const { t } = useI18n()
const browserStore = useBrowserStore()
const toastStore = useToastStore()
const showPanel = ref(null)
const showSpotifyDialog = ref(false)
const currentPlay = ref(null)
const exportingHtml = ref(false)


// 폴더 변경 시 패널·선택 초기화
watch(() => browserStore.selectedFolder, () => {
  showPanel.value = null
  currentPlay.value = null
})

// ── 자동 태그 드롭다운 ──────────────────────────────
const showAutoTagMenu = ref(false)
const autoTagRef = ref(null)
const selectedAutoProviders = ref([])
const availableProviders = ref([])

const PROVIDER_META = {
  spotify:               { label: 'Spotify',               logo: '/logo/spotify.jpg' },
  bugs:                  { label: 'Bugs',                  logo: '/logo/bugs.jpg' },
  melon:                 { label: 'Melon',                 logo: '/logo/melon.jpg' },
  apple_music:           { label: 'Apple Music',           logo: '/logo/apple%20music.jpg' },
  apple_music_classical: { label: 'Apple Music Classical', logo: '/logo/Apple%20Music%20Classical.jpg' },
}

async function loadProviders() {
  try {
    const { data } = await configApi.get()
    const c = data.config
    const enabled = {
      spotify:               (c.spotify_enabled?.value ?? 'true') === 'true',
      bugs:                  (c.bugs_enabled?.value ?? 'true') === 'true',
      melon:                 (c.melon_enabled?.value ?? 'true') === 'true',
      apple_music:           c.apple_music_enabled?.value === 'true',
      apple_music_classical: c.apple_music_classical_enabled?.value === 'true',
    }
    availableProviders.value = Object.entries(enabled)
      .filter(([, v]) => v)
      .map(([k]) => ({ key: k, ...PROVIDER_META[k] }))
  } catch {
    availableProviders.value = [
      { key: 'spotify', ...PROVIDER_META.spotify },
      { key: 'bugs',    ...PROVIDER_META.bugs },
    ]
  }
}

function toggleAutoTagMenu() {
  showAutoTagMenu.value = !showAutoTagMenu.value
}

function dropdownPos(ref) {
  if (!ref?.value) return {}
  const r = ref.value.getBoundingClientRect()
  const right = window.innerWidth - r.right
  return { right: right + 'px' }
}
const autoTagMenuPos = computed(() => showAutoTagMenu.value ? dropdownPos(autoTagRef) : {})
const lrcMenuPos     = computed(() => showLrcMenu.value     ? dropdownPos(lrcMenuRef)  : {})

function openAutoTagSearch(providerKey) {
  selectedAutoProviders.value = [providerKey]
  showAutoTagMenu.value = false
  showSpotifyDialog.value = true
}

function onClickOutside(e) {
  if (autoTagRef.value && !autoTagRef.value.contains(e.target)) {
    showAutoTagMenu.value = false
  }
}

// ── 드래그 다중 선택 ────────────────────────────────
const tableContainerRef = ref(null)
const dragState = ref(null)    // { startX, startY, curX, curY }
const dragActive = ref(false)  // 실제 드래그 중 (4px 이상 이동)
const didDrag = ref(false)     // 드래그 완료 직후 클릭 이벤트 무시용

const dragOverlayStyle = computed(() => {
  if (!dragActive.value || !dragState.value) return {}
  const { startX, startY, curX, curY } = dragState.value
  return {
    left:   Math.min(startX, curX) + 'px',
    top:    Math.min(startY, curY) + 'px',
    width:  Math.abs(curX - startX) + 'px',
    height: Math.abs(curY - startY) + 'px',
  }
})

function getContentCoords(e) {
  const c = tableContainerRef.value
  const r = c.getBoundingClientRect()
  return {
    x: e.clientX - r.left + c.scrollLeft,
    y: e.clientY - r.top  + c.scrollTop,
  }
}

function onTableMouseDown(e) {
  if (e.button !== 0) return
  if (e.target.closest('button, a, audio, select, input')) return
  const { x, y } = getContentCoords(e)
  dragState.value = { startX: x, startY: y, curX: x, curY: y }
  dragActive.value = false
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e) {
  if (!dragState.value) return
  const { x, y } = getContentCoords(e)
  dragState.value = { ...dragState.value, curX: x, curY: y }
  if (!dragActive.value &&
      (Math.abs(x - dragState.value.startX) > 4 || Math.abs(y - dragState.value.startY) > 4)) {
    dragActive.value = true
  }
  if (dragActive.value) updateDragSelection()
}

function updateDragSelection() {
  const { startY, curY } = dragState.value
  const y1 = Math.min(startY, curY)
  const y2 = Math.max(startY, curY)
  const container = tableContainerRef.value
  const cRect = container.getBoundingClientRect()
  const scrollTop = container.scrollTop
  const rows = container.querySelectorAll('tbody tr')
  const newChecked = new Set()
  rows.forEach((row, idx) => {
    const rRect = row.getBoundingClientRect()
    const rowTop    = rRect.top    - cRect.top + scrollTop
    const rowBottom = rRect.bottom - cRect.top + scrollTop
    if (rowBottom > y1 && rowTop < y2) {
      const file = browserStore.displayFiles[idx]
      if (file) newChecked.add(file.path)
    }
  })
  browserStore.setCheckedPaths(newChecked)
}

function onDragEnd() {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  if (dragActive.value) {
    didDrag.value = true
    if (browserStore.checkedPaths.size > 0) {
      browserStore.selectFile(null)
      showPanel.value = 'tag'
    }
  }
  dragActive.value = false
  dragState.value = null
}

onMounted(async () => {
  await loadProviders()
  await loadLrcConfig()
  document.addEventListener('click', onClickOutside, true)
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})

// ────────────────────────────────────────────────────
function formatBadgeClass(fmt) {
  const map = {
    mp3:  'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    flac: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    m4a:  'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    ogg:  'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    aac:  'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',
  }
  return map[(fmt || '').toLowerCase()] || 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatHz(hz) {
  if (!hz) return ''
  const k = hz / 1000
  return `${Number.isInteger(k) ? k : k.toFixed(1)}kHz`
}

function formatDateTime(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

function navigateToCrumb(crumb, index) {
  const newCrumb = browserStore.breadcrumb.slice(0, index + 1)
  browserStore.selectFolder({ name: crumb.name, path: crumb.path }, newCrumb)
}

function onRowClick(file) {
  if (didDrag.value) { didDrag.value = false; return }
  browserStore.setCheckedPaths(new Set())
  browserStore.selectFile(file)
  showPanel.value = 'tag'
}

function closePanel() {
  showPanel.value = null
  browserStore.selectFile(null)
  browserStore.setCheckedPaths(new Set())
}

function openBatchPanel(mode) {
  showPanel.value = showPanel.value === mode ? null : mode
}

function toggleSelectAll() {
  const all = browserStore.displayFiles.map(f => f.path)
  const allSelected = all.length > 0 && all.every(p => browserStore.checkedPaths.has(p))
  if (allSelected) {
    browserStore.setCheckedPaths(new Set())
    browserStore.selectFile(null)
    showPanel.value = null
  } else {
    browserStore.setCheckedPaths(new Set(all))
    browserStore.selectFile(null)
    showPanel.value = 'tag'
  }
}

function onSaved() {}

function enterSubfolder(folder) {
  browserStore.selectFolder({ name: folder.name, path: folder.path })
}

async function exportFolderHtml() {
  const path = browserStore.selectedFolder?.path
  if (!path || exportingHtml.value) return
  exportingHtml.value = true
  try {
    const { data } = await browseApi.exportFolderHtml(path)
    toastStore.success(`${data.filename} 저장됨`)
    // 파일 목록 새로고침 (tracklist.html 표시)
    browserStore.invalidateFilesCache(path)
    browserStore.loadFiles(path, true)
  } catch (e) {
    toastStore.error(t('browser.exportHtmlError'))
  } finally {
    exportingHtml.value = false
  }
}

function forceReload() {
  const path = browserStore.selectedFolder?.path
  if (!path) return
  browserStore.invalidateFilesCache(path)
  browserStore.loadFiles(path, true)
}

// ── LRC 가져오기 ──────────────────────────────────────────
const fetchingLyrics = ref(false)
const showLrcMenu = ref(false)
const lrcMenuRef = ref(null)
const lrcProgress = reactive({
  total: 0, current: 0, ok: 0, notFound: 0, noSync: 0, errors: 0,
  currentFile: '', source: '', done: false,
})

// LRC 설정 (자동 모드 표시용)
const lrcPrimarySource = ref('bugs')
const lrcFallbackSource = ref('lrclib')
const lrcAutoDesc = computed(() => {
  const srcLabel = s => s === 'bugs' ? 'Bugs' : s === 'lrclib' ? 'LRCLIB' : ''
  const primary = srcLabel(lrcPrimarySource.value)
  const fallback = lrcFallbackSource.value !== 'none' ? srcLabel(lrcFallbackSource.value) : null
  return fallback ? `${primary} → ${fallback}` : primary
})

async function loadLrcConfig() {
  try {
    const { data } = await configApi.getAll()
    const c = data.config || {}
    lrcPrimarySource.value = c.lrc_primary_source?.value ?? 'bugs'
    lrcFallbackSource.value = c.lrc_fallback_source?.value ?? 'lrclib'
  } catch { /* ignore */ }
}

// 드롭다운 외부 클릭 시 닫기
function onLrcClickOutside(e) {
  if (lrcMenuRef.value && !lrcMenuRef.value.contains(e.target)) showLrcMenu.value = false
}
onMounted(() => document.addEventListener('click', onLrcClickOutside, true))
onUnmounted(() => document.removeEventListener('click', onLrcClickOutside, true))

// ── 폴더 이동 ─────────────────────────────────────────────
const showMoveModal = ref(false)

// library 경로 환경 (Docker: /app/data/library, 환경변수 없으면 그에 준하는 경로)
// 브라우저에서는 정확한 경로를 알 수 없으므로, 브레드크럼 depth == 1 (루트 직속)인지로 판단
const isLibrarySubfolder = computed(() => {
  if (!browserStore.selectedFolder) return false
  // 브레드크럼이 루트 1개 + 현재 폴더로 구성 (depth 1: library 바로 아래)
  return browserStore.breadcrumb.length === 2
})

async function onMoved(result) {
  showMoveModal.value = false
  showLrcToast(t('browser.moveFolder.success', { path: result.dest }))
  // 라이브러리 루트로 돌아가기
  const roots = browserStore.breadcrumb
  if (roots.length > 0) {
    const rootCrumb = roots[0]
    browserStore.selectFolder({ name: rootCrumb.name, path: rootCrumb.path }, [rootCrumb])
  }
}

// ── 태그 기반 파일명 변경 ─────────────────────────────────
const showRenameModal = ref(false)

const renameTargetFiles = computed(() => {
  const files = browserStore.checkedPaths.size > 0
    ? browserStore.files.filter(f => browserStore.checkedPaths.has(f.path))
    : browserStore.files
  return files.map(f => {
    const ext = f.path.includes('.') ? f.path.split('.').pop() : ''
    const filename = f.path.split('/').pop()
    const stem = ext ? filename.slice(0, -(ext.length + 1)) : filename
    return {
      path: f.path,
      title: f.title,
      artist: f.artist,
      album_artist: f.album_artist,
      album_title: f.album_title,
      track_no: f.track_no,
      total_tracks: f.total_tracks,
      disc_no: f.disc_no,
      year: f.year,
      genre: f.genre,
      label: f.label,
      file_format: f.file_format,
      bitrate: f.bitrate,
      _filename: stem,
      _ext: ext,
    }
  })
})

async function onRenamed(result) {
  showRenameModal.value = false
  const ok = result?.success ?? 0
  const fail = result?.failed ?? 0
  showLrcToast(fail ? t('browser.renameWithFail', { ok, fail }) : t('browser.renameSuccess', { ok }))
  // 폴더 캐시 무효화 후 새로고침
  const path = browserStore.selectedFolder?.path
  if (path) {
    browserStore.invalidateFilesCache(path)
    browserStore.loadFiles(path, true)
  }
}

async function startFetchLyrics(source) {
  showLrcMenu.value = false
  if (fetchingLyrics.value) return
  const paths = browserStore.checkedPaths.size > 0
    ? [...browserStore.checkedPaths]
    : browserStore.files.map(f => f.path)
  if (!paths.length) return

  // 진행 상태 초기화
  const srcLabel = source === 'auto' ? `⚡ ${lrcAutoDesc.value}` : source === 'bugs' ? 'Bugs' : 'LRCLIB'
  Object.assign(lrcProgress, { total: paths.length, current: 0, ok: 0, notFound: 0, noSync: 0, errors: 0, currentFile: '', source: srcLabel, done: false })
  fetchingLyrics.value = true

  try {
    for (let i = 0; i < paths.length; i++) {
      const path = paths[i]
      lrcProgress.current = i + 1
      lrcProgress.currentFile = path.split('/').pop()
      try {
        const { data } = await browseApi.fetchLyrics([path], source)
        const r = (data.results || [])[0]
        if (!r || r.status === 'ok') lrcProgress.ok++
        else if (r.status === 'not_found') lrcProgress.notFound++
        else if (r.status === 'no_sync') lrcProgress.noSync++
        else lrcProgress.errors++
      } catch {
        lrcProgress.errors++
      }
    }
  } finally {
    fetchingLyrics.value = false
    lrcProgress.currentFile = ''
    lrcProgress.done = true
    // 완료 후 토스트 요약
    const parts = []
    if (lrcProgress.ok) parts.push(t('browser.lrcSaved', { n: lrcProgress.ok }))
    if (lrcProgress.noSync) parts.push(t('browser.lrcNoSync', { n: lrcProgress.noSync }))
    if (lrcProgress.notFound) parts.push(t('browser.lrcNotFound', { n: lrcProgress.notFound }))
    if (lrcProgress.errors) parts.push(t('browser.lrcErrors', { n: lrcProgress.errors }))
    toastStore.success(parts.join(' · ') || t('browser.lrcDone'))
  }
}
</script>

<style scoped>
.btn-toolbar {
  @apply px-2.5 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white
         bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
         rounded-lg transition-colors whitespace-nowrap;
}
.btn-toolbar-active {
  @apply !bg-blue-100 !text-blue-700 dark:!bg-blue-900/30 dark:!text-blue-400;
}

/* LRC 로딩바 */
@keyframes lrc-progress {
  0%   { transform: translateX(-100%); }
  50%  { transform: translateX(0%); }
  100% { transform: translateX(100%); }
}
.animate-lrc-progress {
  width: 40%;
  animation: lrc-progress 1.4s ease-in-out infinite;
}

/* 토스트 트랜지션 */
.toast-enter-active, .toast-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }
</style>
