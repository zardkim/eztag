<template>
  <div class="relative flex flex-col bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0">
      <div class="min-w-0">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ $t('batchPanel.title') }}
          <span v-if="multiMode" class="ml-1.5 text-xs font-normal text-blue-500 dark:text-blue-400">{{ $t('batchPanel.filesCount', { n: targetFiles.length }) }}</span>
        </h3>
        <p class="text-xs text-gray-400 mt-0.5 truncate">
          {{ referenceFile?.title || referenceFile?.filename || '-' }}
        </p>
      </div>
      <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1 shrink-0 ml-2" @click="$emit('close')">✕</button>
    </div>

    <!-- 저장 / 초기화 / 태그검색 버튼 -->
    <div class="px-4 py-2.5 border-b border-gray-200 dark:border-gray-800 space-y-1.5">
      <div class="flex gap-2">
        <button
          class="flex-1 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg transition-colors"
          :disabled="saving"
          @click="save"
        >{{ saving ? $t('batchPanel.saving') : $t('batchPanel.save') }}</button>
        <button
          class="px-3 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white border border-gray-200 dark:border-gray-700 rounded-lg transition-colors"
          @click="reset"
        >{{ $t('batchPanel.reset') }}</button>
        <button
          class="px-3 py-2 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700 rounded-lg transition-colors shrink-0"
          :title="$t('batchPanel.searchTagTitle')"
          @click="$emit('search-tag', targetPaths)"
        >🏷</button>
      </div>
      <p v-if="hasSpecialCharWarning" class="text-[11px] text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
        <span>⚠️</span>{{ $t('tagWarning.specialChars') }}
      </p>
    </div>
    <!-- 되돌리기 / 다시 실행 -->
    <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-800 flex gap-2">
      <button
        class="flex-1 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg transition-colors disabled:opacity-30"
        :disabled="!historyStore.canUndo || historyStore.busy"
        :title="historyStore.undoLabel || $t('browser.undoEmpty')"
        @click="historyStore.undo(browserStore)"
      >↩ {{ $t('browser.undoLabel') }}</button>
      <button
        class="flex-1 py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg transition-colors disabled:opacity-30"
        :disabled="!historyStore.canRedo || historyStore.busy"
        :title="historyStore.redoLabel || $t('browser.redoEmpty')"
        @click="historyStore.redo(browserStore)"
      >{{ $t('browser.redoLabel') }} ↪</button>
    </div>

    <!-- Content -->
    <div>
      <!-- 커버 -->
      <div v-if="referenceFile" class="px-4 pt-3 pb-1">
        <div
          class="relative w-full aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow cursor-pointer group"
          :class="coverDragOver ? 'ring-2 ring-blue-400' : ''"
          @click="openFolderImagePicker"
          @dragover.prevent="coverDragOver = true"
          @dragleave="coverDragOver = false"
          @drop.prevent="onCoverDrop"
        >
          <img v-if="activeCoverUrl" :src="activeCoverUrl" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full flex items-center justify-center text-5xl text-gray-300 dark:text-gray-600">🎵</div>

          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
            <span class="opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs font-medium text-center px-2">
              🖼 {{ $t('batchPanel.coverFromFolder') }}
            </span>
          </div>

          <template v-if="coverList.length > 1">
            <button class="absolute left-1 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/50 hover:bg-black/70 text-white text-sm flex items-center justify-center transition-colors z-10" @click.stop="prevCover">‹</button>
            <button class="absolute right-1 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/50 hover:bg-black/70 text-white text-sm flex items-center justify-center transition-colors z-10" @click.stop="nextCover">›</button>
          </template>

          <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent px-3 py-2">
            <p class="text-white text-xs font-medium truncate">{{ referenceFile.title || referenceFile.filename }}</p>
            <p class="text-white/70 text-[10px] flex items-center gap-2 mt-0.5 flex-wrap">
              <span v-if="referenceFile.file_format" class="font-mono">{{ referenceFile.file_format }}</span>
              <span v-if="referenceFile.bitrate">{{ referenceFile.bitrate }} kbps</span>
              <span v-if="referenceFile.duration">{{ formatDuration(referenceFile.duration) }}</span>
              <span v-if="referenceFile.file_size">{{ formatSize(referenceFile.file_size) }}</span>
              <span v-if="referenceFile.has_lyrics">📝</span>
              <span v-if="referenceFile.outdated" class="text-yellow-300">{{ $t('batchPanel.coverOutdated') }}</span>
            </p>
          </div>
        </div>

        <!-- 커버 정보 + 제거/추출 -->
        <div class="flex items-center justify-between mt-1 px-0.5 text-[10px] text-gray-400">
          <span class="flex items-center gap-1.5 min-w-0 truncate">
            <template v-if="currentCover">
              <span>{{ COVER_TYPES.find(ct => ct.id === currentCover.type)?.label || currentCover.type_name }}</span>
              <span v-if="currentCover.source === 'folder'" class="text-gray-300 dark:text-gray-600 truncate">📁 {{ currentCover.name }}</span>
              <span v-if="currentCover.width">{{ currentCover.width }}×{{ currentCover.height }}</span>
              <span v-if="currentCover.size_bytes">{{ formatSize(currentCover.size_bytes) }}</span>
              <span v-if="coverList.length > 1">{{ coverIdx + 1 }}/{{ coverList.length }}</span>
            </template>
          </span>
          <div v-if="activeCoverUrl && currentCover?.source === 'embedded'" class="flex items-center gap-1 shrink-0 ml-1">
            <button
              class="text-[10px] px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/30 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors border border-red-200 dark:border-red-800"
              :title="$t('batchPanel.coverRemove')"
              @click="removeCoverArt"
            >{{ $t('batchPanel.coverRemove') }}</button>
            <button
              class="text-[10px] px-2 py-0.5 rounded bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/50 transition-colors border border-green-200 dark:border-green-800"
              :title="$t('batchPanel.coverExtract')"
              @click="extractCoverArt"
            >{{ $t('batchPanel.coverExtract') }}</button>
          </div>
        </div>
        <!-- 커버 타입 선택 + 업로드 -->
        <div class="flex items-center justify-end mt-0.5 px-0.5 gap-0.5">
          <select
            v-model="selectedCoverType"
            class="flex-1 min-w-0 text-[10px] h-5 px-1 rounded-l bg-gray-100 dark:bg-gray-800 border border-r-0 border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 focus:outline-none cursor-pointer"
            :title="$t('batchPanel.coverTypeLabel')"
          >
            <option v-for="ct in COVER_TYPES" :key="ct.id" :value="ct.id">{{ ct.label }}</option>
          </select>
          <button
            class="shrink-0 flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-r bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors border border-gray-200 dark:border-gray-700"
            :title="$t('batchPanel.coverUpload')"
            @click="triggerCoverInput"
          >⬆ {{ $t('batchPanel.coverUpload') }}</button>
        </div>

        <!-- 대기 중인 커버 목록 -->
        <div v-if="pendingCovers.length > 0" class="mt-1.5 space-y-1 px-0.5">
          <p class="text-[9px] font-semibold text-blue-500 dark:text-blue-400 uppercase tracking-wider">{{ $t('batchPanel.coverPending', { n: pendingCovers.length }) }}</p>
          <div
            v-for="pc in pendingCovers"
            :key="pc.id"
            class="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg px-2 py-1"
          >
            <img :src="pc.preview" class="w-8 h-8 rounded object-cover shrink-0 border border-blue-200 dark:border-blue-700" />
            <span class="flex-1 text-[10px] text-blue-700 dark:text-blue-300 truncate">
              {{ COVER_TYPES.find(ct => ct.id === pc.coverType)?.label }}
            </span>
            <button
              class="text-[10px] text-blue-400 hover:text-red-500 dark:hover:text-red-400 transition-colors px-1"
              @click="removePendingCover(pc.id)"
            >✕</button>
          </div>
        </div>

        <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="onCoverFileSelect" />
      </div>

      <!-- 폴더 이미지 선택 모달 -->
      <Teleport to="body">
        <div
          v-if="showFolderPicker"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="showFolderPicker = false"
        >
          <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-[480px] max-w-[95vw] max-h-[80vh] flex flex-col">
            <!-- 모달 헤더 -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 shrink-0">
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ $t('batchPanel.coverPickTitle') }}</h3>
                <p class="text-xs text-gray-400 mt-0.5">{{ folderImagesFolder }}</p>
              </div>
              <button class="text-gray-400 hover:text-gray-700 dark:hover:text-white p-1" @click="showFolderPicker = false">✕</button>
            </div>
            <!-- 이미지 그리드 -->
            <div class="flex-1 overflow-y-auto p-4">
              <div v-if="folderImagesLoading" class="flex items-center justify-center h-32 text-gray-400 text-sm">
                {{ $t('batchPanel.coverPickLoading') }}
              </div>
              <div v-else-if="folderImages.length === 0" class="flex flex-col items-center justify-center h-32 text-gray-400">
                <p class="text-sm">{{ $t('batchPanel.coverPickEmpty') }}</p>
                <p class="text-xs mt-1">{{ folderImagesFolder }}</p>
              </div>
              <div v-else class="grid grid-cols-3 gap-3">
                <button
                  v-for="img in folderImages"
                  :key="img.path"
                  class="relative aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 border-2 transition-all hover:scale-[1.02]"
                  :class="selectedFolderImage?.path === img.path
                    ? 'border-blue-500 ring-2 ring-blue-400/50'
                    : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'"
                  @click="selectFolderImage(img)"
                >
                  <img :src="img.url" :alt="img.name" class="w-full h-full object-cover" loading="lazy" />
                  <div class="absolute top-1.5 left-1.5 text-[8px] px-1 py-0.5 bg-black/50 rounded text-white">
                    {{ COVER_TYPES.find(ct => ct.id === detectCoverTypeFromName(img.name))?.label }}
                  </div>
                  <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent px-1.5 py-1">
                    <p class="text-white text-[9px] truncate">{{ img.name }}</p>
                  </div>
                  <div v-if="selectedFolderImage?.path === img.path" class="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                    <span class="text-white text-[10px]">✓</span>
                  </div>
                </button>
              </div>
            </div>
            <!-- 모달 푸터 -->
            <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-800 space-y-2 shrink-0">
              <!-- 커버 타입 선택 -->
              <div class="flex items-center gap-2">
                <label class="text-xs text-gray-500 shrink-0">{{ $t('batchPanel.coverTypeLabel') }}</label>
                <select
                  v-model="folderPickerCoverType"
                  class="flex-1 text-xs rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-2 py-1 focus:outline-none"
                >
                  <option v-for="ct in COVER_TYPES" :key="ct.id" :value="ct.id">{{ ct.label }}</option>
                </select>
              </div>
              <div class="flex gap-2">
                <button
                  class="flex-1 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg transition-colors"
                  :disabled="!selectedFolderImage"
                  @click="applyFolderImage"
                >{{ $t('common.apply') }}</button>
                <button
                  class="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg transition-colors"
                  @click="showFolderPicker = false"
                >{{ $t('common.cancel') }}</button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <div class="px-4 space-y-2.5 pb-3">
        <!-- ── 기본 태그 ── -->
        <div class="border-t border-gray-100 dark:border-gray-800 pt-2.5">
          <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">{{ $t('batchPanel.sectionBasic') }}</p>
        </div>

        <div>
          <label class="tag-label">{{ $t('batchPanel.fieldTitle') }}</label>
          <select v-if="showMixedSelect('title')" key="sel-title" :value="getFieldMode('title')" class="mixed-select" :class="getFieldMode('title') === 'clear' ? 'clear' : ''" @change="setFieldMode('title', $event.target.value)">
            <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
            <option value="clear">{{ $t('batchPanel.optClear') }}</option>
            <option value="input">{{ $t('batchPanel.optInput') }}</option>
          </select>
          <input v-else key="inp-title" v-model="form.title" class="field w-full text-sm" placeholder="" />
        </div>
        <div>
          <label class="tag-label">{{ $t('batchPanel.fieldArtist') }}</label>
          <select v-if="showMixedSelect('artist')" key="sel-artist" :value="getFieldMode('artist')" class="mixed-select" :class="getFieldMode('artist') === 'clear' ? 'clear' : ''" @change="setFieldMode('artist', $event.target.value)">
            <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
            <option value="clear">{{ $t('batchPanel.optClear') }}</option>
            <option value="input">{{ $t('batchPanel.optInput') }}</option>
          </select>
          <input v-else key="inp-artist" v-model="form.artist" class="field w-full text-sm" placeholder="" />
        </div>
        <div>
          <label class="tag-label">{{ $t('batchPanel.fieldAlbumArtist') }}</label>
          <select v-if="showMixedSelect('album_artist')" key="sel-album_artist" :value="getFieldMode('album_artist')" class="mixed-select" :class="getFieldMode('album_artist') === 'clear' ? 'clear' : ''" @change="setFieldMode('album_artist', $event.target.value)">
            <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
            <option value="clear">{{ $t('batchPanel.optClear') }}</option>
            <option value="input">{{ $t('batchPanel.optInput') }}</option>
          </select>
          <input v-else key="inp-album_artist" v-model="form.album_artist" class="field w-full text-sm" placeholder="" />
        </div>
        <div>
          <label class="tag-label">{{ $t('batchPanel.fieldAlbum') }}</label>
          <select v-if="showMixedSelect('album_title')" key="sel-album_title" :value="getFieldMode('album_title')" class="mixed-select" :class="getFieldMode('album_title') === 'clear' ? 'clear' : ''" @change="setFieldMode('album_title', $event.target.value)">
            <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
            <option value="clear">{{ $t('batchPanel.optClear') }}</option>
            <option value="input">{{ $t('batchPanel.optInput') }}</option>
          </select>
          <input v-else key="inp-album_title" v-model="form.album_title" class="field w-full text-sm" placeholder="" />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldYear') }}</label>
            <select v-if="showMixedSelect('year')" key="sel-year" :value="getFieldMode('year')" class="mixed-select" :class="getFieldMode('year') === 'clear' ? 'clear' : ''" @change="setFieldMode('year', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
              <option value="clear">{{ $t('batchPanel.optClear') }}</option>
              <option value="input">{{ $t('batchPanel.optInput') }}</option>
            </select>
            <input v-else key="inp-year" v-model.number="form.year" type="number" min="1900" max="2099" class="field w-full text-sm" placeholder="" />
          </div>
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldGenre') }}</label>
            <select v-if="showMixedSelect('genre')" key="sel-genre" :value="getFieldMode('genre')" class="mixed-select" :class="getFieldMode('genre') === 'clear' ? 'clear' : ''" @change="setFieldMode('genre', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
              <option value="clear">{{ $t('batchPanel.optClear') }}</option>
              <option value="input">{{ $t('batchPanel.optInput') }}</option>
            </select>
            <template v-else>
              <input key="inp-genre" v-model="form.genre" list="genre-datalist" class="field w-full text-sm" placeholder="" autocomplete="off" />
            </template>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldDisc') }}</label>
            <select v-if="showMixedSelect('disc_no')" key="sel-disc_no" :value="getFieldMode('disc_no')" class="mixed-select" :class="getFieldMode('disc_no') === 'clear' ? 'clear' : ''" @change="setFieldMode('disc_no', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeepShort') }}</option>
              <option value="clear">{{ $t('batchPanel.optClearShort') }}</option>
              <option value="input">{{ $t('batchPanel.optInputShort') }}</option>
            </select>
            <input v-else key="inp-disc_no" v-model.number="form.disc_no" type="number" min="1" class="field w-full text-sm" placeholder="" />
          </div>
          <div>
            <label class="tag-label">
              {{ $t('batchPanel.fieldTrack') }}
              <button
                v-if="multiMode"
                class="ml-1 text-[10px] text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200 font-normal underline"
                :title="$t('batchPanel.trackAutoTitle')"
                @click.prevent="autoTrackNumber"
              >{{ $t('batchPanel.trackAutoBtn') }}</button>
            </label>
            <select v-if="showMixedSelect('track_no')" key="sel-track_no" :value="getFieldMode('track_no')" class="mixed-select" :class="getFieldMode('track_no') === 'clear' ? 'clear' : ''" @change="setFieldMode('track_no', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeepShort') }}</option>
              <option value="clear">{{ $t('batchPanel.optClearShort') }}</option>
              <option value="input">{{ $t('batchPanel.optInputShort') }}</option>
            </select>
            <input v-else key="inp-track_no" v-model.number="form.track_no" type="number" min="1" class="field w-full text-sm" placeholder="" />
          </div>
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldTotalTrack') }}</label>
            <select v-if="showMixedSelect('total_tracks')" key="sel-total_tracks" :value="getFieldMode('total_tracks')" class="mixed-select" :class="getFieldMode('total_tracks') === 'clear' ? 'clear' : ''" @change="setFieldMode('total_tracks', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeepShort') }}</option>
              <option value="clear">{{ $t('batchPanel.optClearShort') }}</option>
              <option value="input">{{ $t('batchPanel.optInputShort') }}</option>
            </select>
            <input v-else key="inp-total_tracks" v-model.number="form.total_tracks" type="number" min="1" class="field w-full text-sm" placeholder="" />
          </div>
        </div>

        <!-- 설명 -->
        <div>
          <label class="tag-label">{{ $t('batchPanel.fieldComment') }}</label>
          <select v-if="showMixedSelect('comment')" key="sel-comment" :value="getFieldMode('comment')" class="mixed-select" :class="getFieldMode('comment') === 'clear' ? 'clear' : ''" @change="setFieldMode('comment', $event.target.value)">
            <option value="keep">{{ mixedFields.has('comment') ? $t('batchPanel.optKeep') : $t('batchPanel.optKeepSingle') }}</option>
            <option value="clear">{{ $t('batchPanel.optClear') }}</option>
            <option value="input">{{ $t('batchPanel.optInput') }}</option>
          </select>
          <textarea v-else key="inp-comment" v-model="form.comment" class="field w-full text-sm resize-none" rows="3" placeholder=""></textarea>
        </div>

        <!-- ── 추가 태그 (접기/펼치기) ── -->
        <button
          class="w-full flex items-center justify-between py-2 text-xs font-semibold text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 border-t border-gray-100 dark:border-gray-800 transition-colors"
          @click="expandExtra = !expandExtra"
        >
          <span class="uppercase tracking-wider">{{ $t('batchPanel.sectionExtra') }}</span>
          <span class="text-base leading-none">{{ expandExtra ? '▴' : '▾' }}</span>
        </button>

        <div v-show="expandExtra" class="space-y-2.5">
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldReleaseDate') }}</label>
            <select v-if="showMixedSelect('release_date')" key="sel-release_date" :value="getFieldMode('release_date')" class="mixed-select" :class="getFieldMode('release_date') === 'clear' ? 'clear' : ''" @change="setFieldMode('release_date', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
              <option value="clear">{{ $t('batchPanel.optClear') }}</option>
              <option value="input">{{ $t('batchPanel.optInput') }}</option>
            </select>
            <input v-else key="inp-release_date" v-model="form.release_date" class="field w-full text-sm" placeholder="YYYY-MM-DD" />
          </div>
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldLabel') }}</label>
            <select v-if="showMixedSelect('label')" key="sel-label" :value="getFieldMode('label')" class="mixed-select" :class="getFieldMode('label') === 'clear' ? 'clear' : ''" @change="setFieldMode('label', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
              <option value="clear">{{ $t('batchPanel.optClear') }}</option>
              <option value="input">{{ $t('batchPanel.optInput') }}</option>
            </select>
            <input v-else key="inp-label" v-model="form.label" class="field w-full text-sm" placeholder="" />
          </div>
          <div>
            <label class="tag-label">ISRC</label>
            <input v-model="form.isrc" class="field w-full text-sm font-mono" :placeholder="$t('batchPanel.readonlyPlaceholder')" readonly />
          </div>
          <div>
            <label class="tag-label">{{ $t('batchPanel.fieldLyrics') }}</label>
            <select v-if="showMixedSelect('lyrics')" key="sel-lyrics" :value="getFieldMode('lyrics')" class="mixed-select" :class="getFieldMode('lyrics') === 'clear' ? 'clear' : ''" @change="setFieldMode('lyrics', $event.target.value)">
              <option value="keep">{{ $t('batchPanel.optKeep') }}</option>
              <option value="clear">{{ $t('batchPanel.optClear') }}</option>
              <option value="input">{{ $t('batchPanel.optInput') }}</option>
            </select>
            <textarea
              v-else
              key="inp-lyrics"
              v-model="form.lyrics"
              class="field w-full text-sm font-mono resize-y"
              rows="6"
              :placeholder="$t('batchPanel.lyricsPlaceholder')"
            />
          </div>

          <!-- 파일 정보 (읽기 전용) -->
          <div class="border-t border-gray-100 dark:border-gray-800 pt-2">
            <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">{{ $t('batchPanel.sectionFileInfo') }}</p>
            <div class="space-y-1 text-xs">
              <div v-for="row in fileInfoRows" :key="row.label" class="flex justify-between">
                <span class="text-gray-400">{{ row.label }}</span>
                <span class="text-gray-600 dark:text-gray-300 font-mono text-right truncate max-w-[60%]">{{ row.value }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 안내 -->
        <p class="text-[10px] text-gray-400 border-t border-gray-100 dark:border-gray-800 pt-2">
          {{ $t('batchPanel.hintEmpty') }}
          <span v-if="multiMode">{{ $t('batchPanel.hintBatch', { n: targetFiles.length }) }} <span class="text-red-400">{{ $t('batchPanel.optClear') }}</span> {{ $t('batchPanel.hintClear') }}</span>
        </p>
      </div>

    </div>


    <!-- 장르 datalist -->
    <datalist id="genre-datalist">
      <option v-for="g in GENRES" :key="g" :value="g" />
    </datalist>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import { useBrowserStore } from '../stores/browser.js'
import { useHistoryStore } from '../stores/history.js'
import { GENRES } from '../constants/genres.js'
import { useToastStore } from '../stores/toast.js'
import { hasAnyFilenameSpecialChars } from '../utils/tagWarning.js'


function detectCoverTypeFromName(filename) {
  const name = filename.toLowerCase().replace(/\.[^.]+$/, '').trim()
  if (['back', 'back cover', 'backcover', 'rear'].includes(name)) return 4
  if (['front', 'front cover', 'frontcover', 'cover', 'folder', 'albumart', 'album art'].includes(name)) return 3
  return 3
}

// cover / front / front cover 등 같은 의미의 파일명을 하나의 캐노니컬 키로 반환.
// null 반환 시 캐노니컬 중복 대상이 아님 (일반 파일명은 항상 표시).
function getCanonicalStem(filename) {
  const name = filename.toLowerCase().replace(/\.[^.]+$/, '').trim()
  if (['front', 'front cover', 'frontcover', 'cover', 'folder', 'albumart', 'album art'].includes(name)) return 'front_cover'
  if (['back', 'back cover', 'backcover', 'rear'].includes(name)) return 'back_cover'
  return null
}

function deduplicateImages(images) {
  const seen = new Set()
  return images.filter(img => {
    const stem = getCanonicalStem(img.name)
    if (!stem) return true
    if (seen.has(stem)) return false
    seen.add(stem)
    return true
  })
}

// ── 커버 관련 ──────────────────────────────────────────────
const coverInput = ref(null)
const coverDragOver = ref(false)
const coverList = ref([])
const coverIdx = ref(0)
const coverSize = ref(null)
const selectedCoverType = ref(3)

// 대기 중인 커버 목록 (저장 시 일괄 적용)
// [{ id, coverType, source: 'file'|'folder', file, folderPath, preview }]
const pendingCovers = ref([])

function addPendingCover({ source, file = null, folderPath = null, preview, coverType }) {
  // 같은 타입이 이미 있으면 교체
  const idx = pendingCovers.value.findIndex(p => p.coverType === coverType)
  const item = { id: Date.now(), source, file, folderPath, preview, coverType }
  if (idx >= 0) {
    pendingCovers.value.splice(idx, 1, item)
  } else {
    pendingCovers.value.push(item)
  }
}

function removePendingCover(id) {
  pendingCovers.value = pendingCovers.value.filter(p => p.id !== id)
}

// 폴더 이미지 선택 모달
const showFolderPicker = ref(false)
const folderImages = ref([])
const folderImagesLoading = ref(false)
const folderImagesFolder = ref('')
const selectedFolderImage = ref(null)
const folderPickerCoverType = ref(3)  // 픽커 내 타입 선택

async function openFolderImagePicker() {
  const folder = browserStore.selectedFolder?.path || referenceFile.value?.path
  if (!folder) return
  showFolderPicker.value = true
  selectedFolderImage.value = null
  folderPickerCoverType.value = selectedCoverType.value
  folderImagesLoading.value = true
  folderImagesFolder.value = folder
  try {
    const { data } = await browseApi.getFolderImages(folder)
    folderImages.value = Array.isArray(data) ? deduplicateImages(data) : []
  } catch {
    folderImages.value = []
  } finally {
    folderImagesLoading.value = false
  }
}

function selectFolderImage(img) {
  selectedFolderImage.value = img
  folderPickerCoverType.value = detectCoverTypeFromName(img.name)
}

function applyFolderImage() {
  if (!selectedFolderImage.value) return
  addPendingCover({
    source: 'folder',
    folderPath: selectedFolderImage.value.path,
    preview: selectedFolderImage.value.url,
    coverType: folderPickerCoverType.value,
  })
  selectedCoverType.value = folderPickerCoverType.value
  showFolderPicker.value = false
}

function prevCover() {
  coverIdx.value = (coverIdx.value - 1 + coverList.value.length) % coverList.value.length
  const c = coverList.value[coverIdx.value]
  if (c?.type != null) selectedCoverType.value = c.type
}
function nextCover() {
  coverIdx.value = (coverIdx.value + 1) % coverList.value.length
  const c = coverList.value[coverIdx.value]
  if (c?.type != null) selectedCoverType.value = c.type
}
function triggerCoverInput() { coverInput.value?.click() }
function onCoverFileSelect(e) { const f = e.target.files?.[0]; if (f) setCoverFile(f); e.target.value = '' }
function onCoverDrop(e) {
  coverDragOver.value = false
  const f = e.dataTransfer.files?.[0]
  if (f?.type.startsWith('image/')) setCoverFile(f)
}
function setCoverFile(file) {
  const reader = new FileReader()
  reader.onload = (ev) => {
    addPendingCover({
      source: 'file',
      file,
      preview: ev.target.result,
      coverType: selectedCoverType.value,
    })
  }
  reader.readAsDataURL(file)
}

// ── 공통 ───────────────────────────────────────────────────
const { t } = useI18n()

// ── 커버 타입 ──────────────────────────────────────────────
const COVER_TYPES = computed(() => [
  { id: 3,  label: t('batchPanel.coverTypeFront') },
  { id: 4,  label: t('batchPanel.coverTypeBack') },
  { id: 0,  label: t('batchPanel.coverTypeOther') },
  { id: 1,  label: t('batchPanel.coverTypeIcon') },
  { id: 5,  label: t('batchPanel.coverTypeLeaflet') },
  { id: 6,  label: t('batchPanel.coverTypeMedia') },
  { id: 7,  label: t('batchPanel.coverTypeLeadArtist') },
  { id: 9,  label: t('batchPanel.coverTypeConductor') },
  { id: 10, label: t('batchPanel.coverTypeBand') },
  { id: 11, label: t('batchPanel.coverTypeComposer') },
  { id: 12, label: t('batchPanel.coverTypeLyricist') },
  { id: 13, label: t('batchPanel.coverTypeRecordingLocation') },
  { id: 14, label: t('batchPanel.coverTypeDuringRecording') },
  { id: 15, label: t('batchPanel.coverTypeDuringPerformance') },
  { id: 16, label: t('batchPanel.coverTypeVideoCapture') },
  { id: 17, label: t('batchPanel.coverTypeIllustration') },
  { id: 18, label: t('batchPanel.coverTypeBandLogo') },
  { id: 19, label: t('batchPanel.coverTypePublisherLogo') },
])
const props = defineProps({})
const emit = defineEmits(['close', 'saved', 'search-tag'])
const browserStore = useBrowserStore()
const toastStore = useToastStore()
const historyStore = useHistoryStore()
const saving = ref(false)
const hasSpecialCharWarning = computed(() =>
  hasAnyFilenameSpecialChars({ title: form.title, artist: form.artist, album_artist: form.album_artist, album_title: form.album_title })
)
const expandExtra = ref(false)
const fieldMode = ref({})   // { [field]: 'keep'|'clear'|'input' } — 다중 값 필드 처리 모드


function showToast(msg) { toastStore.info(msg) }

// ── 대상 파일 계산 ─────────────────────────────────────────
const files = computed(() => browserStore.files)

// 표시 순서(정렬 적용) 기준의 대상 파일 목록
const targetFiles = computed(() => {
  const displayed = browserStore.displayFiles
  if (browserStore.selectedFile) return [browserStore.selectedFile]
  if (browserStore.checkedPaths.size > 0)
    return displayed.filter(f => browserStore.checkedPaths.has(f.path))
  return displayed
})

const targetPaths = computed(() => targetFiles.value.map(f => f.path))
const multiMode = computed(() => targetFiles.value.length > 1)

const referenceFile = computed(() => targetFiles.value[0] || null)

// ── 커버 URL ───────────────────────────────────────────────
const activeCoverUrl = computed(() => {
  if (coverList.value.length > 0) return coverList.value[coverIdx.value]?.url
  const f = referenceFile.value
  return (f?.has_cover && f?.path)
    ? `/api/browse/file-cover?path=${encodeURIComponent(f.path)}`
    : null
})

const currentCover = computed(() => coverList.value[coverIdx.value] || null)

watch(activeCoverUrl, (url) => {
  coverSize.value = null
  if (!url) return
  const img = new Image()
  img.onload = () => { coverSize.value = { w: img.naturalWidth, h: img.naturalHeight } }
  img.src = url
}, { immediate: true })

// ── 폼 ────────────────────────────────────────────────────
const form = reactive({
  title: '', artist: '', album_artist: '', album_title: '',
  genre: '', year: null, track_no: null, total_tracks: null,
  disc_no: null, release_date: '', label: '', isrc: '', lyrics: '', comment: '',
})

// 다중 선택 시 값이 혼재하는 필드 집합
const mixedFields = computed(() => {
  if (!multiMode.value) return new Set()
  const fields = ['title','artist','album_artist','album_title','genre','year','track_no','total_tracks','disc_no','release_date','label','lyrics','comment']
  const mixed = new Set()
  for (const field of fields) {
    const vals = new Set(targetFiles.value.map(f => String(f[field] ?? '')))
    if (vals.size > 1) mixed.add(field)
  }
  return mixed
})

function mixedPlaceholder(field) {
  return mixedFields.value.has(field) ? '(다중 값)' : ''
}

const NUM_FIELDS = new Set(['year', 'track_no', 'total_tracks', 'disc_no'])

function getFieldMode(field) {
  return fieldMode.value[field] || 'keep'
}

function setFieldMode(field, mode) {
  if (mode === 'keep') {
    const next = { ...fieldMode.value }
    delete next[field]
    fieldMode.value = next
    form[field] = NUM_FIELDS.has(field) ? null : ''
  } else if (mode === 'clear') {
    fieldMode.value = { ...fieldMode.value, [field]: 'clear' }
    form[field] = NUM_FIELDS.has(field) ? null : ''
  } else if (mode === 'input') {
    fieldMode.value = { ...fieldMode.value, [field]: 'input' }
  }
}

// 다중 값 필드에서 select를 보여줄 조건
// comment는 다중 모드에서 파일 중 하나라도 값이 있으면 항상 표시
function showMixedSelect(field) {
  if (!multiMode.value || getFieldMode(field) === 'input') return false
  if (field === 'comment') {
    return mixedFields.value.has(field) || targetFiles.value.some(f => f.comment)
  }
  return mixedFields.value.has(field) && !form[field]
}

// 단일 파일 폼 채우기
function fillFromFile(file) {
  if (!file) return
  form.title        = file.title        || ''
  form.artist       = file.artist       || ''
  form.album_artist = file.album_artist || ''
  form.album_title  = file.album_title  || ''
  form.genre        = file.genre        || ''
  form.year         = file.year         || null
  form.track_no     = file.track_no     || null
  form.total_tracks = file.total_tracks || null
  form.disc_no      = file.disc_no      || null
  form.release_date = file.release_date || ''
  form.label        = file.label        || ''
  form.isrc         = file.isrc         || ''
  form.lyrics       = file.lyrics       || ''
  form.comment      = file.comment      || ''
  if (file.release_date || file.label || file.isrc || file.lyrics) expandExtra.value = true
}

// 다중 파일 폼 채우기 — 공통 값은 채우고, 혼재 값은 빈 칸
function fillFromFiles(fileList) {
  fieldMode.value = {}
  if (!fileList.length) return
  if (fileList.length === 1) { fillFromFile(fileList[0]); return }
  const fields = ['title','artist','album_artist','album_title','genre','year','track_no','total_tracks','disc_no','release_date','label','isrc','lyrics','comment']
  for (const field of fields) {
    const vals = [...new Set(fileList.map(f => f[field] ?? null).filter(v => v !== null && v !== ''))]
    if (vals.length === 1) {
      form[field] = vals[0]
    } else {
      form[field] = typeof form[field] === 'number' ? null : ''
    }
  }
  // 공통 추가 태그가 있으면 펼치기
  if (fileList.some(f => f.release_date || f.label || f.isrc || f.lyrics)) expandExtra.value = true
}

// ── targetFiles 변경 시 폼 갱신 ───────────────────────────
watch(targetFiles, async (fileList) => {
  // 저장/자동번호 실행 중에는 폼 덮어쓰기 생략 — 사용자 미저장 입력이 사라지는 버그 방지
  if (saving.value) return
  coverIdx.value = 0
  coverSize.value = null
  pendingCovers.value = []
  const ref = fileList[0]

  // 내장 커버가 있으면 먼저 표시 — API 응답 전 flicker 방지
  if (ref?.has_cover && ref?.path) {
    coverList.value = [{ source: 'embedded', url: `/api/browse/file-cover?path=${encodeURIComponent(ref.path)}`, index: 0, type: 3, type_name: t('batchPanel.coverTypeFront') }]
  } else {
    coverList.value = []
  }

  if (ref?.path) {
    // 내장 커버 + 폴더 이미지 병렬 로드
    const [embeddedRes, folderRes] = await Promise.allSettled([
      browseApi.getCovers(ref.path),
      browseApi.getFolderImages(ref.path),
    ])

    const embedded = (embeddedRes.status === 'fulfilled' && Array.isArray(embeddedRes.value.data))
      ? embeddedRes.value.data.map(c => ({ ...c, source: 'embedded' }))
      : []

    const folderImgs = (folderRes.status === 'fulfilled' && Array.isArray(folderRes.value.data))
      ? deduplicateImages(folderRes.value.data).map(img => {
          const type = detectCoverTypeFromName(img.name)
          return {
            source: 'folder',
            url: img.url,
            type,
            type_name: COVER_TYPES.value.find(ct => ct.id === type)?.label || t('batchPanel.coverTypeOther'),
            name: img.name,
            folderPath: img.path,
          }
        })
      : []

    const combined = [...embedded, ...folderImgs]
    if (combined.length > 0) {
      coverList.value = combined
    } else if (ref.has_cover) {
      // fallback — 내장 커버는 있는데 list_covers가 빈 경우
      coverList.value = [{ source: 'embedded', url: `/api/browse/file-cover?path=${encodeURIComponent(ref.path)}`, index: 0, type: 3, type_name: t('batchPanel.coverTypeFront') }]
    }
  }
  fillFromFiles(fileList)

}, { immediate: true })

// ── 파일 정보 (읽기 전용) ─────────────────────────────────
const fileInfoRows = computed(() => {
  const f = referenceFile.value
  if (!f) return []
  const rows = []
  if (f.file_format)  rows.push({ label: t('batchPanel.fileInfoFormat'),   value: f.file_format })
  if (f.bitrate)      rows.push({ label: t('batchPanel.fileInfoBitrate'),  value: `${f.bitrate} kbps` })
  if (f.duration)     rows.push({ label: t('batchPanel.fileInfoDuration'), value: formatDuration(f.duration) })
  if (f.file_size)    rows.push({ label: t('batchPanel.fileInfoSize'),     value: formatSize(f.file_size) })
  if (f.isrc)         rows.push({ label: 'ISRC',     value: f.isrc })
  if (f.path) {
    const base = browserStore.breadcrumb[0]?.path
    const rel = base && f.path.startsWith(base) ? f.path.slice(base.length).replace(/^\//, '') : f.path
    rows.push({ label: '경로', value: rel })
  }
  return rows
})

function formatDuration(sec) {
  if (!sec) return ''
  return `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, '0')}`
}
function formatSize(bytes) {
  if (!bytes) return ''
  return bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`
}

// ── 초기화 ────────────────────────────────────────────────
function reset() {
  pendingCovers.value = []
  fillFromFiles(targetFiles.value)
}

// ── 저장 ──────────────────────────────────────────────────
async function save() {
  const updates = {}
  if (form.title)        updates.title        = form.title
  if (form.artist)       updates.artist       = form.artist
  if (form.album_artist) updates.album_artist = form.album_artist
  if (form.album_title)  updates.album_title  = form.album_title
  if (form.genre)        updates.genre        = form.genre
  if (form.year)         updates.year         = form.year
  if (form.track_no)     updates.track_no     = form.track_no
  if (form.total_tracks) updates.total_tracks = form.total_tracks
  if (form.disc_no)      updates.disc_no      = form.disc_no
  if (form.release_date) updates.release_date = form.release_date
  if (form.label)        updates.label        = form.label
  if (form.lyrics)       updates.lyrics       = form.lyrics
  if (form.comment)      updates.comment      = form.comment

  // clear_fields: 다중 값 필드 중 '제거' 모드로 설정된 것 (직접 입력값이 없는 경우만)
  const modeClearFields = multiMode.value
    ? Object.entries(fieldMode.value)
        .filter(([field, mode]) => mode === 'clear' && !updates[field])
        .map(([field]) => field)
    : []
  // 단일 파일 모드: 기존에 값이 있었는데 폼에서 지워진 필드도 clear_fields에 포함
  const singleClearFields = !multiMode.value
    ? (() => {
        const file = targetFiles.value[0]
        if (!file) return []
        const textFields = ['title', 'artist', 'album_artist', 'album_title', 'genre', 'release_date', 'label', 'lyrics', 'comment']
        const numFields = ['year', 'track_no', 'total_tracks', 'disc_no']
        return [
          ...textFields.filter(f => (file[f] || '') !== '' && (form[f] || '') === '' && !updates[f]),
          ...numFields.filter(f => file[f] != null && form[f] == null && !updates[f]),
        ]
      })()
    : []
  const clear_fields = [...modeClearFields, ...singleClearFields]

  if (!Object.keys(updates).length && !clear_fields.length && !pendingCovers.value.length) return

  // 되돌리기용 스냅샷 저장 (저장 전 각 파일의 현재 값)
  const snapshot = {}
  const updatedFields = [...Object.keys(updates), ...clear_fields]
  for (const path of targetPaths.value) {
    const file = browserStore.files.find(f => f.path === path)
    if (file) {
      snapshot[path] = Object.fromEntries(
        updatedFields.map(k => [k, file[k] ?? null])
      )
    }
  }

  saving.value = true
  try {
    const paths = targetPaths.value

    // 1단계: 텍스트 태그 먼저 저장 (커버보다 먼저 — 커버가 마지막 기록이 되어야 함)
    if (Object.keys(updates).length || clear_fields.length) {
      await browseApi.batchWriteTags({ paths, ...updates, clear_fields })
      // 프론트엔드 파일 캐시 무효화 — 폴더 재진입 시 최신 태그 반영
      const folderPath = browserStore.selectedFolder?.path
      if (folderPath) browserStore.invalidateFilesCache(folderPath)
    }

    const clearUpdate = Object.fromEntries(clear_fields.map(f => [f, null]))
    browserStore.updateFiles(paths, { ...updates, ...clearUpdate })
    if (browserStore.selectedFile) {
      browserStore.selectFile({ ...browserStore.selectedFile, ...updates, ...clearUpdate })
    }

    fieldMode.value = {}
    // 저장 완료 후 폼을 저장된 상태로 명시적 동기화 (watcher가 saving 중 스킵하므로 직접 갱신)
    fillFromFiles(targetFiles.value)

    // 2단계: 커버 저장 (텍스트 태그 이후 마지막으로 — 파일에 마지막 기록 보장)
    const coversToApply = [...pendingCovers.value]
    pendingCovers.value = []
    for (const pending of coversToApply) {
      if (pending.source === 'file') {
        // 파일별 업로드 병렬 처리
        await Promise.all(paths.map(path =>
          browseApi.uploadCoverWithType(path, pending.file, pending.coverType)
        ))
      } else if (pending.source === 'folder') {
        await browseApi.coverFromFolderWithType(pending.folderPath, paths, pending.coverType)
      }
    }
    if (coversToApply.length > 0) {
      const folderPath = browserStore.selectedFolder?.path
      if (folderPath) browserStore.invalidateFilesCache(folderPath)
      browserStore.updateFiles(paths, { has_cover: true })
      if (browserStore.selectedFile && paths.includes(browserStore.selectedFile.path)) {
        browserStore.selectFile({ ...browserStore.selectedFile, has_cover: true })
      }
      try {
        const { data } = await browseApi.getCovers(paths[0])
        const reloaded = (Array.isArray(data) ? data : []).map(c => ({ ...c, source: 'embedded' }))
        // 폴더 이미지는 유지 (embedded만 교체)
        coverList.value = [
          ...reloaded,
          ...coverList.value.filter(c => c.source === 'folder'),
        ]
        coverIdx.value = 0
      } catch {}
    }

    // 전역 히스토리에 등록 (undo/redo 지원)
    const ops = Object.entries(snapshot).map(([path, before]) => ({
      path,
      before,
      after: { ...updates, ...clearUpdate },
    }))
    if (ops.length) {
      const n = ops.length
      historyStore.push({
        label: n === 1
          ? `태그 편집: ${browserStore.files.find(f => f.path === ops[0].path)?.filename ?? ops[0].path.split('/').pop()}`
          : `태그 편집 (${n}개 파일)`,
        ops,
      })
    }

    emit('saved')
    showToast('저장 완료')
  } catch (e) {
    showToast(e.response?.data?.detail || t('common.error'))
  } finally {
    saving.value = false
  }
}


// ── 커버아트 추출 (폴더에 이미지 파일로 저장) ───────────────
async function extractCoverArt() {
  const path = referenceFile.value?.path
  if (!path) return
  saving.value = true
  try {
    const { data } = await browseApi.extractCovers(path)
    const names = data.saved.map(s => s.filename).join(', ')
    showToast(t('batchPanel.coverExtractDone', { names }))
  } catch (e) {
    const detail = e.response?.data?.detail || t('batchPanel.coverExtractError')
    // 파일이 이미 존재하면 덮어쓸지 확인
    if (e.response?.status === 409 || detail.includes('exists')) {
      // 충돌 시 overwrite 재시도는 사용하지 않고 안내만
      showToast(detail)
    } else {
      showToast(detail)
    }
  } finally {
    saving.value = false
  }
}

// ── 커버아트 제거 ──────────────────────────────────────────
async function removeCoverArt() {
  if (!await toastStore.confirm(t('batchPanel.coverRemoveConfirm', { n: targetFiles.value.length }), t('batchPanel.coverRemoveTitle'))) return
  saving.value = true
  try {
    const { data } = await browseApi.removeCover(targetPaths.value)
    const results = data?.results || []
    const succeeded = results.filter(r => r.ok).map(r => r.path)
    const failed = results.filter(r => !r.ok)

    if (succeeded.length > 0) {
      browserStore.updateFiles(succeeded, { has_cover: false })
      if (browserStore.selectedFile && succeeded.includes(browserStore.selectedFile.path)) {
        browserStore.selectFile({ ...browserStore.selectedFile, has_cover: false })
      }
      const folderPath = browserStore.selectedFolder?.path
      if (folderPath) browserStore.invalidateFilesCache(folderPath)
      coverList.value = []
      coverIdx.value = 0
    }

    if (failed.length > 0) {
      const errMsg = failed.map(r => `${r.path.split('/').pop()}: ${r.error || t('batchPanel.coverExtractError')}`).join('\n')
      showToast(t('batchPanel.coverRemoveFailed', { n: failed.length, msg: errMsg }))
    } else {
      showToast(t('batchPanel.coverRemoveDone'))
    }
  } catch (e) {
    showToast(t('batchPanel.coverRemoveError'))
  } finally {
    saving.value = false
  }
}

// ── 자동 트랙번호 매기기 ───────────────────────────────────
async function autoTrackNumber() {
  const targets = targetFiles.value  // displayFiles 정렬 순서
  if (targets.length < 2) return
  const total = targets.length

  // 되돌리기용 스냅샷
  const snapshot = {}
  for (const f of targets) {
    snapshot[f.path] = { track_no: f.track_no ?? null, total_tracks: f.total_tracks ?? null }
  }

  saving.value = true
  try {
    for (let i = 0; i < targets.length; i++) {
      const trackUpdates = { track_no: i + 1, total_tracks: total }
      await browseApi.batchWriteTags({ paths: [targets[i].path], ...trackUpdates })
      browserStore.updateFiles([targets[i].path], trackUpdates)
    }

    // form 업데이트 (watcher가 saving 중 스킵하므로 직접 갱신)
    form.total_tracks = total
    if (browserStore.selectedFile) {
      const idx = targets.findIndex(f => f.path === browserStore.selectedFile.path)
      if (idx !== -1) form.track_no = idx + 1
    } else {
      form.track_no = null  // 다중이라 혼재
    }
    // disc_no 등 기타 필드는 그대로 유지 (사용자 미저장 입력 보존)

    // 전역 히스토리에 등록
    historyStore.push({
      label: `트랙번호 자동 매기기 (${total}개)`,
      ops: Object.entries(snapshot).map(([path, before]) => {
        const idx = targets.findIndex(f => f.path === path)
        return { path, before, after: { track_no: idx + 1, total_tracks: total } }
      }),
    })

    showToast(`${total}개 파일에 트랙 번호 1~${total} 적용 완료`)
  } catch (e) {
    showToast('트랙 번호 매기기 실패')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.tag-label {
  @apply text-xs text-gray-500 block mb-1;
}
.mixed-select {
  @apply field w-full text-sm text-gray-400 dark:text-gray-500 cursor-pointer;
}
.mixed-select.clear {
  @apply text-red-500 dark:text-red-400 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/10;
}
</style>
