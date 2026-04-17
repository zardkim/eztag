<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[500] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="onClose"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">

        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800 shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-lg">🏷</span>
            <h2 class="text-base font-bold text-gray-800 dark:text-gray-100">{{ t('filenameAutoTag.title') }}</h2>
          </div>
          <!-- 단계 표시: source → config → running → result -->
          <div class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-gray-500">
            <span :class="step === 'source'  ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : (stepPast('source')  ? 'line-through' : '')">① {{ t('filenameAutoTag.stepSource') }}</span>
            <span>›</span>
            <span :class="step === 'config'  ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : (stepPast('config')  ? 'line-through' : '')">② {{ t('filenameAutoTag.stepConfig') }}</span>
            <span>›</span>
            <span :class="step === 'running' ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : ''">③ {{ t('filenameAutoTag.stepRunning') }}</span>
            <span>›</span>
            <span :class="step === 'result'  ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : ''">④ {{ t('filenameAutoTag.stepResult') }}</span>
          </div>
          <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" @click="onClose">✕</button>
        </div>

        <!-- ── Step 1: 소스 선택 ── -->
        <div v-if="step === 'source'" class="flex-1 flex flex-col px-5 py-6 gap-4">
          <p class="text-sm text-gray-600 dark:text-gray-400">태그 정보를 가져올 검색 소스를 선택하세요.</p>
          <div class="flex flex-wrap gap-3">
            <button
              v-for="p in availableProviders"
              :key="p.key"
              class="flex items-center gap-2.5 px-4 py-3 rounded-2xl border-2 transition-all"
              :class="selectedProviders.includes(p.key)
                ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 dark:border-indigo-600 shadow-sm'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'"
              @click="toggleProvider(p.key)"
            >
              <img :src="p.logo" :alt="p.label" class="w-8 h-8 rounded-xl object-cover" />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ p.label }}</span>
              <span v-if="selectedProviders.includes(p.key)" class="text-indigo-500 ml-1">✓</span>
            </button>
          </div>
          <p v-if="!availableProviders.length" class="text-sm text-gray-400">{{ t('filenameAutoTag.selectProviderFirst') }}</p>
        </div>

        <!-- ── Step 2: 패턴 설정 + 비교 미리보기 ── -->
        <div v-else-if="step === 'config'" class="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-0">

          <!-- 자동감지 배너 -->
          <div v-if="detecting" class="flex items-center gap-2 px-3 py-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl text-xs text-indigo-600 dark:text-indigo-400">
            <svg class="animate-spin w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
            패턴 자동 감지 중...
          </div>
          <div v-else-if="detectedPattern" class="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-xl text-xs text-green-700 dark:text-green-400">
            ✅ {{ t('filenameAutoTag.autoDetected') }}: <strong>{{ detectedPattern }}</strong>
            <span class="text-green-500">({{ t('filenameAutoTag.confidence') }} {{ Math.round(detectedConfidence * 100) }}%)</span>
          </div>

          <!-- 선택된 소스 표시 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-gray-500 dark:text-gray-400">검색 소스:</span>
            <div class="flex gap-1.5 flex-wrap">
              <span
                v-for="key in selectedProviders"
                :key="key"
                class="flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-[11px] font-medium"
              >
                <img :src="providerMeta(key).logo" :alt="providerMeta(key).label" class="w-3.5 h-3.5 rounded object-cover" />
                {{ providerMeta(key).label }}
              </span>
            </div>
            <button class="text-[11px] text-gray-400 underline underline-offset-2 hover:text-gray-600 dark:hover:text-gray-300" @click="step = 'source'">변경</button>
          </div>

          <!-- 패턴 입력 -->
          <div class="space-y-2">
            <label class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{{ t('filenameAutoTag.patternLabel') }}</label>
            <TagVarInput
              v-model="pattern"
              :variables="PATTERN_VARS_WITH_DESC"
              :builtin-presets="PRESETS"
              storage-key="eztag-filename-autotag"
              accent-color="indigo"
              :placeholder="t('filenameAutoTag.patternPlaceholder')"
            />
          </div>

          <!-- 비교 미리보기 테이블 -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{{ t('filenameAutoTag.previewTitle') }}</label>
              <span class="text-[11px] text-gray-400">{{ files.length }}개 파일</span>
            </div>
            <div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
              <div class="overflow-auto max-h-56">
                <table class="w-full text-[11px] border-collapse">
                  <thead>
                    <tr class="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 sticky top-0 z-10">
                      <th class="px-2 py-2 text-left font-medium whitespace-nowrap border-r border-gray-200 dark:border-gray-700" rowspan="2">파일명</th>
                      <th class="px-2 py-1.5 text-center font-medium border-r border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-700/60" colspan="4">{{ t('filenameAutoTag.colCurrent') }}</th>
                      <th class="px-2 py-1.5 text-center font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10" colspan="5">{{ t('filenameAutoTag.colParsed') }}</th>
                    </tr>
                    <tr class="bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-500 text-[10px] sticky top-[33px] z-10">
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('filenameAutoTag.colArtist') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('filenameAutoTag.colTitle') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('filenameAutoTag.colGenre') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap border-r border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-700/60">{{ t('filenameAutoTag.colYear') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('filenameAutoTag.colArtist') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('filenameAutoTag.colTitle') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('filenameAutoTag.colTrack') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('filenameAutoTag.colDisc') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('filenameAutoTag.colYear') }}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                    <tr
                      v-for="row in previewRows"
                      :key="row.path"
                      :class="row.error ? 'bg-red-50/50 dark:bg-red-900/5' : 'hover:bg-gray-50 dark:hover:bg-gray-800/40'"
                    >
                      <td class="px-2 py-1.5 text-gray-400 dark:text-gray-500 max-w-[120px] truncate font-mono text-[10px] border-r border-gray-100 dark:border-gray-800">{{ stemOf(row.filename) }}</td>
                      <!-- 현재 태그 -->
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[90px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ currentTag(row.path, 'artist') }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[100px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ currentTag(row.path, 'title') }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[70px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ currentTag(row.path, 'genre') }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 border-r border-gray-100 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/20">{{ currentTag(row.path, 'year') }}</td>
                      <!-- 파싱 결과 -->
                      <td class="px-2 py-1.5 max-w-[90px] truncate" :class="row.error ? 'text-red-400' : diffClass(row.path, 'artist', row.parsed?.artist)">
                        <span v-if="row.error" class="text-[10px]">✗ 패턴 불일치</span>
                        <span v-else>{{ row.parsed?.artist || '' }}</span>
                      </td>
                      <td class="px-2 py-1.5 max-w-[100px] truncate" :class="diffClass(row.path, 'title', row.parsed?.title)">{{ row.parsed?.title || '' }}</td>
                      <td class="px-2 py-1.5 tabular-nums" :class="diffClass(row.path, 'track_no', row.parsed?.track_no)">{{ row.parsed?.track_no || '' }}</td>
                      <td class="px-2 py-1.5 tabular-nums" :class="diffClass(row.path, 'disc_no', row.parsed?.disc_no)">{{ row.parsed?.disc_no || '' }}</td>
                      <td class="px-2 py-1.5 tabular-nums" :class="diffClass(row.path, 'year', row.parsed?.year)">{{ row.parsed?.year || '' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <p class="text-[10px] text-gray-400 dark:text-gray-500">
              <span class="inline-block w-2 h-2 rounded bg-indigo-200 dark:bg-indigo-700 mr-1"></span>파란색: 현재 태그와 달라지는 값
            </p>
          </div>
        </div>

        <!-- ── Step 3: 진행 중 ── -->
        <div v-else-if="step === 'running'" class="flex-1 flex flex-col items-center justify-center px-5 py-10 gap-5">
          <svg class="animate-spin w-10 h-10 text-indigo-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          <!-- 진행 카운터 -->
          <div class="text-center space-y-1.5 w-full max-w-xs">
            <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {{ t('filenameAutoTag.running') }}
              <span class="text-indigo-600 dark:text-indigo-400 ml-1">{{ progress.current }} / {{ progress.total }}</span>
            </p>
            <!-- 프로그레스 바 -->
            <div class="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-indigo-500 rounded-full transition-all duration-300"
                :style="{ width: progress.total > 0 ? (progress.current / progress.total * 100) + '%' : '0%' }"
              />
            </div>
            <!-- 현재 파일명 -->
            <p v-if="progress.filename" class="text-[11px] text-gray-400 dark:text-gray-500 truncate">{{ progress.filename }}</p>
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 text-center">{{ t('filenameAutoTag.runningNote') }}</p>
        </div>

        <!-- ── Step 4: 결과 ── -->
        <div v-else-if="step === 'result'" class="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-0">
          <!-- 요약 -->
          <div class="flex flex-wrap items-center gap-3">
            <div v-if="revertMessage" class="flex items-center gap-1.5 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-xs text-blue-600 dark:text-blue-400">
              ↩ {{ revertMessage }}
            </div>
            <template v-else>
              <div class="flex items-center gap-1.5 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <span class="text-green-600 dark:text-green-400 font-bold text-sm">{{ summary.applied }}</span>
                <span class="text-xs text-green-600 dark:text-green-400">{{ t('filenameAutoTag.applied') }}</span>
              </div>
              <div v-if="summary.kept_existing" class="flex items-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-xl">
                <span class="text-gray-500 dark:text-gray-400 font-bold text-sm">{{ summary.kept_existing }}</span>
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('filenameAutoTag.keptExisting') }}</span>
              </div>
              <div v-if="summary.applied_parsed" class="flex items-center gap-1.5 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <span class="text-blue-500 dark:text-blue-400 font-bold text-sm">{{ summary.applied_parsed }}</span>
                <span class="text-xs text-blue-500 dark:text-blue-400">{{ t('filenameAutoTag.appliedParsed') }}</span>
              </div>
              <div v-if="summary.parse_error" class="flex items-center gap-1.5 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
                <span class="text-red-500 font-bold text-sm">{{ summary.parse_error }}</span>
                <span class="text-xs text-red-500">{{ t('filenameAutoTag.parseError') }}</span>
              </div>
              <div v-if="summary.error" class="flex items-center gap-1.5 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
                <span class="text-red-500 font-bold text-sm">{{ summary.error }}</span>
                <span class="text-xs text-red-500">{{ t('filenameAutoTag.error') }}</span>
              </div>
            </template>
          </div>

          <!-- 결과 테이블 -->
          <div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
            <div class="overflow-auto max-h-[420px]">
              <table class="w-full text-[11px] border-collapse">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 sticky top-0 z-10">
                    <th class="px-2 py-2 text-left font-medium whitespace-nowrap border-r border-gray-200 dark:border-gray-700" rowspan="2">파일명</th>
                    <th class="px-2 py-1.5 text-center font-medium w-8" rowspan="2">상태</th>
                    <th class="px-2 py-1.5 text-center font-medium border-l border-gray-200 dark:border-gray-700" colspan="6">적용된 태그</th>
                  </tr>
                  <tr class="bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-500 text-[10px] sticky top-[33px] z-10">
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap border-l border-gray-200 dark:border-gray-700">{{ t('filenameAutoTag.colArtist') }}</th>
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap">{{ t('filenameAutoTag.colTitle') }}</th>
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap">{{ t('filenameAutoTag.colAlbum') }}</th>
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap">{{ t('filenameAutoTag.colGenre') }}</th>
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap">{{ t('filenameAutoTag.colYear') }}</th>
                    <th class="px-2 py-1 text-left font-normal whitespace-nowrap">소스</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                  <tr v-for="r in results" :key="r.path" class="hover:bg-gray-50 dark:hover:bg-gray-800/40">
                    <td class="px-2 py-1.5 text-gray-400 dark:text-gray-500 max-w-[130px] truncate font-mono text-[10px] border-r border-gray-100 dark:border-gray-800">{{ stemOf(r.filename) }}</td>
                    <td class="px-2 py-1.5 text-center">
                      <span v-if="r.status === 'applied' || r.status === 'reverted'" class="text-green-500">✅</span>
                      <span v-else-if="r.status === 'kept_existing'" class="text-gray-400 text-xs" :title="t('filenameAutoTag.keptExisting')">⏸</span>
                      <span v-else-if="r.status === 'applied_parsed'" class="text-blue-400 text-xs" :title="t('filenameAutoTag.appliedParsed')">📝</span>
                      <span v-else-if="r.status === 'no_match'" class="text-amber-400 text-xs">—</span>
                      <span v-else class="text-red-400 text-xs">✗</span>
                    </td>
                    <template v-if="r.status === 'applied'">
                      <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300 max-w-[100px] truncate border-l border-gray-100 dark:border-gray-800">{{ r.matched_artist }}</td>
                      <td class="px-2 py-1.5 text-gray-700 dark:text-gray-300 max-w-[110px] truncate">{{ r.matched_title }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[100px] truncate">{{ r.matched_album || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[70px] truncate">{{ r.matched_genre || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-400 tabular-nums">{{ r.matched_year || '' }}</td>
                      <td class="px-2 py-1.5 text-[10px] text-gray-400">{{ r.matched_provider || '' }}</td>
                    </template>
                    <template v-else-if="r.status === 'kept_existing' || r.status === 'applied_parsed'">
                      <td class="px-2 py-1.5 text-gray-600 dark:text-gray-400 max-w-[100px] truncate border-l border-gray-100 dark:border-gray-800">{{ r.matched_artist || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-600 dark:text-gray-400 max-w-[110px] truncate">{{ r.matched_title || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-400 max-w-[100px] truncate">{{ r.matched_album || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-400 max-w-[70px] truncate">{{ r.matched_genre || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-400 tabular-nums">{{ r.matched_year || '' }}</td>
                      <td class="px-2 py-1.5 text-[10px]" :class="r.status === 'kept_existing' ? 'text-gray-400' : 'text-blue-400'">
                        {{ r.status === 'kept_existing' ? t('filenameAutoTag.keptExisting') : t('filenameAutoTag.appliedParsed') }}
                      </td>
                    </template>
                    <template v-else-if="r.status === 'reverted'">
                      <td colspan="6" class="px-2 py-1.5 text-[11px] text-blue-500 dark:text-blue-400 border-l border-gray-100 dark:border-gray-800">↩ 되돌림</td>
                    </template>
                    <template v-else>
                      <td colspan="6" class="px-2 py-1.5 text-xs text-gray-400 border-l border-gray-100 dark:border-gray-800">
                        {{ r.status === 'no_match' ? t('filenameAutoTag.noMatch') : r.error }}
                      </td>
                    </template>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Footer 버튼 -->
        <div class="px-5 py-3.5 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center shrink-0 gap-3">
          <!-- 왼쪽: 미매칭 재시도 + 되돌리기 -->
          <div class="flex gap-2">
            <button
              v-if="step === 'result' && noMatchFiles.length > 0 && !reverting && !revertMessage"
              class="px-3 py-2 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50 rounded-xl transition-colors font-medium"
              @click="retryNoMatch"
            >{{ t('filenameAutoTag.retryNoMatch') }} ({{ noMatchFiles.length }})</button>
            <button
              v-if="step === 'result' && appliedResults.length > 0 && !revertMessage"
              class="px-3 py-2 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors font-medium disabled:opacity-50"
              :disabled="reverting"
              @click="doRevert"
            >
              <span v-if="reverting">{{ t('filenameAutoTag.reverting') }}</span>
              <span v-else>↩ {{ t('filenameAutoTag.revert') }} ({{ appliedResults.length }})</span>
            </button>
          </div>

          <!-- 오른쪽: 닫기 / 다음 / 실행 -->
          <div class="flex gap-2">
            <button
              v-if="step !== 'running'"
              class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              @click="onClose"
            >{{ t('common.close') }}</button>
            <!-- 소스 선택 → 다음 -->
            <button
              v-if="step === 'source'"
              class="px-5 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
              :disabled="selectedProviders.length === 0"
              @click="goToConfig"
            >{{ t('filenameAutoTag.nextBtn') }}</button>
            <!-- 패턴 설정 → 자동태그 실행 -->
            <button
              v-if="step === 'config'"
              class="px-5 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
              :disabled="!canRun"
              @click="run"
            >{{ t('filenameAutoTag.runBtn') }}</button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi } from '../api/index.js'
import { metadataApi } from '../api/metadata.js'
import TagVarInput from './TagVarInput.vue'

const props = defineProps({
  modelValue:         { type: Boolean, default: false },
  files:              { type: Array,   default: () => [] },
  availableProviders: { type: Array,   default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'done', 'retryFiles'])

const { t } = useI18n()

// ── 패턴 변수 (설정 안내문 전체 목록 기준) ──
const PATTERN_VARS_WITH_DESC = computed(() => [
  { var: '%artist%',      desc: t('renameModal.varArtist') },
  { var: '%title%',       desc: t('renameModal.varTitle') },
  { var: '%albumartist%', desc: t('renameModal.varAlbumArtist') },
  { var: '%album%',       desc: t('renameModal.varAlbum') },
  { var: '%track%',       desc: t('renameModal.varTrack') },
  { var: '%disc%',        desc: t('renameModal.varDisc') },
  { var: '%year%',        desc: t('renameModal.varYear') },
  { var: '%genre%',       desc: t('renameModal.varGenre') },
])

// ── 상태 ──
const STEP_ORDER = ['source', 'config', 'running', 'result']
const step               = ref('source')
const pattern            = ref('')
const detectedPattern    = ref('')
const detectedConfidence = ref(0)
const detecting          = ref(false)
const previewRows        = ref([])
const selectedProviders  = ref([])
const results            = ref([])
const summary            = ref({ applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 })
const progress           = ref({ current: 0, total: 0, filename: '' })
const reverting          = ref(false)
const revertMessage      = ref('')

// ── 프리셋 ──
const PRESETS = computed(() => [
  { label: t('filenameAutoTag.presets.melonChart'),       pattern: '%track%-%artist%-%disc%-%title%' },
  { label: t('filenameAutoTag.presets.trackArtistTitle'), pattern: '%track% - %artist% - %title%' },
  { label: t('filenameAutoTag.presets.artistTrackTitle'), pattern: '%artist% - %track% - %title%' },
  { label: t('filenameAutoTag.presets.artistTitle'),      pattern: '%artist% - %title%' },
  { label: t('filenameAutoTag.presets.trackTitle'),       pattern: '%track% - %title%' },
  { label: t('filenameAutoTag.presets.trackTitleNoSpace'),pattern: '%track%-%title%' },
])

const fileMap = computed(() => {
  const m = {}
  for (const f of props.files) m[f.path] = f
  return m
})

const noMatchFiles   = computed(() => results.value.filter(r => r.status === 'kept_existing' || r.status === 'applied_parsed').map(r => r.path))
const appliedResults = computed(() => results.value.filter(r => r.status === 'applied' && r.original))
const canRun         = computed(() => pattern.value.trim() && selectedProviders.value.length > 0 && props.files.length > 0)

/** 현재 step보다 이미 지난 단계인지 */
function stepPast(s) {
  return STEP_ORDER.indexOf(step.value) > STEP_ORDER.indexOf(s)
}

/** provider 메타 정보 조회 */
function providerMeta(key) {
  return props.availableProviders.find(p => p.key === key) || { label: key, logo: '' }
}

function stemOf(filename) {
  return filename ? filename.replace(/\.[^.]+$/, '') : ''
}

function currentTag(path, field) {
  return fileMap.value[path]?.[field] ?? ''
}

function diffClass(path, field, parsedVal) {
  if (parsedVal === undefined || parsedVal === null || parsedVal === '') return 'text-gray-700 dark:text-gray-300'
  const cur = fileMap.value[path]?.[field]
  const isDiff = String(parsedVal) !== String(cur ?? '')
  return isDiff
    ? 'text-indigo-600 dark:text-indigo-400 font-medium'
    : 'text-gray-500 dark:text-gray-400'
}

// ── 다이얼로그 열릴 때 초기화 ──
watch(() => props.modelValue, (open) => {
  if (!open) return
  step.value          = 'source'
  results.value       = []
  revertMessage.value = ''
  previewRows.value   = []
  summary.value       = { applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 }
  progress.value      = { current: 0, total: 0, filename: '' }
  selectedProviders.value = props.availableProviders.map(p => p.key)
})

// ── 소스 선택 → 패턴 설정으로 이동 ──
async function goToConfig() {
  step.value = 'config'
  // 항상 자동감지 시도 (패턴이 이미 있어도 재감지하여 파일 변화 반영)
  await detectPattern()
}

async function detectPattern() {
  if (!props.files.length) return
  detecting.value = true
  try {
    const paths = props.files.map(f => f.path)
    const { data } = await browseApi.detectFilenamePattern(paths)
    detectedPattern.value    = data.pattern
    detectedConfidence.value = data.confidence
    pattern.value            = data.pattern
    await loadPreview()
  } catch {
    pattern.value = '%artist% - %title%'
    await loadPreview()
  } finally {
    detecting.value = false
  }
}

async function loadPreview() {
  if (!pattern.value || !props.files.length) return
  try {
    const paths = props.files.map(f => f.path)
    const { data } = await browseApi.tagFromNamePreview(paths, pattern.value)
    previewRows.value = data.results || []
  } catch {
    previewRows.value = []
  }
}

let _previewTimer = null
function debouncedPreview() {
  clearTimeout(_previewTimer)
  _previewTimer = setTimeout(() => loadPreview(), 400)
}

// 패턴 변경 시 자동으로 미리보기 다시 실행
watch(pattern, debouncedPreview)

function toggleProvider(key) {
  const idx = selectedProviders.value.indexOf(key)
  if (idx === -1) selectedProviders.value.push(key)
  else selectedProviders.value.splice(idx, 1)
}

async function run() {
  if (!canRun.value) return
  step.value          = 'running'
  revertMessage.value = ''
  results.value       = []
  progress.value      = { current: 0, total: props.files.length, filename: '' }

  try {
    await metadataApi.autoTagByFilenameStream(
      {
        paths:           props.files.map(f => f.path),
        pattern:         pattern.value,
        providers:       selectedProviders.value,
        match_threshold: 70.0,
      },
      {
        onProgress(current, total, filename, item) {
          progress.value = { current, total, filename }
          if (item) results.value.push(item)
        },
        onDone(s) {
          summary.value = s || { applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 }
          step.value = 'result'
          emit('done')
        },
      }
    )
  } catch (e) {
    step.value = 'config'
    console.error('auto-tag-by-filename error', e)
  }
}

async function doRevert() {
  if (!appliedResults.value.length) return
  if (!confirm(t('filenameAutoTag.revertConfirm'))) return
  reverting.value = true
  try {
    const items = appliedResults.value.map(r => ({ path: r.path, original: r.original }))
    const { data } = await metadataApi.revertAutoTag(items)
    revertMessage.value = t('filenameAutoTag.revertDone', { n: data.reverted })
    results.value = results.value.map(r =>
      r.status === 'applied' ? { ...r, status: 'reverted' } : r
    )
    emit('done')
  } catch (e) {
    console.error('revert error', e)
  } finally {
    reverting.value = false
  }
}

function retryNoMatch() {
  step.value = 'source'
  emit('retryFiles', noMatchFiles.value)
}

function onClose() {
  if (step.value === 'running') return
  emit('update:modelValue', false)
}
</script>
