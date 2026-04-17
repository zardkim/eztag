<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[500] flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-0 sm:p-4"
      @click.self="onClose"
    >
      <div class="bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-xl max-h-[96vh] sm:max-h-[90vh] flex flex-col overflow-hidden">

        <!-- ── Header ── -->
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 dark:border-gray-800 shrink-0 gap-3">
          <!-- 뒤로 버튼 -->
          <button
            v-if="canGoBack"
            class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors text-sm shrink-0 -ml-1"
            @click="goBack"
          >← {{ t('common.back') }}</button>
          <div v-else class="flex items-center gap-2 shrink-0">
            <span class="text-lg">🏷</span>
            <h2 class="text-sm font-bold text-gray-800 dark:text-gray-100">{{ t('autoTag.title') }}</h2>
          </div>

          <!-- 단계 표시 -->
          <div class="flex-1 flex items-center justify-center gap-1 text-[11px] text-gray-400 dark:text-gray-500 overflow-hidden">
            <template v-for="(crumb, i) in breadcrumbs" :key="i">
              <span v-if="i > 0" class="shrink-0">›</span>
              <span
                class="shrink-0"
                :class="crumb.active ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : crumb.done ? 'line-through opacity-60' : ''"
              >{{ crumb.label }}</span>
            </template>
          </div>

          <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors shrink-0" @click="onClose">✕</button>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             STEP: select  (방식 + 소스 선택)
        ══════════════════════════════════════════════════════════ -->
        <div v-if="step === 'select'" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          <!-- 방식 선택 -->
          <div class="space-y-1.5">
            <p class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('autoTag.modeLabel') }}</p>
            <div class="flex gap-2">
              <button
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border-2 transition-all"
                :class="mode === 'album'
                  ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-600'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'"
                @click="mode = 'album'"
              >
                <span class="text-sm">💿</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ t('autoTag.modeAlbum') }}</span>
                <span v-if="mode === 'album'" class="text-blue-500 text-xs">✓</span>
              </button>
              <button
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border-2 transition-all"
                :class="mode === 'filename'
                  ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 dark:border-indigo-600'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'"
                @click="mode = 'filename'"
              >
                <span class="text-sm">📄</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ t('autoTag.modeFilename') }}</span>
                <span v-if="mode === 'filename'" class="text-indigo-500 text-xs">✓</span>
              </button>
            </div>
          </div>

          <!-- 검색 소스 선택 -->
          <div class="space-y-1.5">
            <p class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ t('autoTag.sourceLabel') }}</p>
            <div v-if="allProviders.length" class="flex flex-wrap gap-1.5">
              <button
                v-for="p in allProviders"
                :key="p.key"
                class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border-2 transition-all text-sm"
                :class="selectedProviders.includes(p.key)
                  ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 dark:border-indigo-600'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'"
                @click="toggleProvider(p.key)"
              >
                <img :src="p.logo" :alt="p.label" class="w-5 h-5 rounded object-cover shrink-0" />
                <span class="font-medium text-gray-700 dark:text-gray-300">{{ p.label }}</span>
                <span v-if="selectedProviders.includes(p.key)" class="text-indigo-500 text-xs">✓</span>
              </button>
            </div>
            <p v-else class="text-sm text-gray-400">{{ t('autoTag.noProviders') }}</p>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             STEP: fn_config  (파일명 패턴 설정)
        ══════════════════════════════════════════════════════════ -->
        <div v-else-if="step === 'fn_config'" class="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-0">
          <!-- 자동감지 배너 -->
          <div v-if="fn.detecting" class="flex items-center gap-2 px-3 py-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl text-xs text-indigo-600 dark:text-indigo-400">
            <svg class="animate-spin w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
            {{ t('autoTag.detecting') }}
          </div>
          <div v-else-if="fn.detectedPattern" class="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-xl text-xs text-green-700 dark:text-green-400">
            ✅ {{ t('autoTag.autoDetected') }}: <strong>{{ fn.detectedPattern }}</strong>
            <span class="text-green-500">({{ t('autoTag.confidence') }} {{ Math.round(fn.detectedConfidence * 100) }}%)</span>
          </div>

          <!-- 선택 소스 -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('autoTag.sourceLabel') }}:</span>
            <div class="flex gap-1.5 flex-wrap">
              <span v-for="key in selectedProviders" :key="key"
                class="flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-[11px] font-medium"
              >
                <img :src="providerMeta(key).logo" :alt="providerMeta(key).label" class="w-3.5 h-3.5 rounded object-cover" />
                {{ providerMeta(key).label }}
              </span>
            </div>
            <button class="text-[11px] text-gray-400 underline underline-offset-2 hover:text-gray-600 dark:hover:text-gray-300" @click="step = 'select'">{{ t('autoTag.change') }}</button>
          </div>

          <!-- 패턴 입력 -->
          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{{ t('autoTag.patternLabel') }}</label>
            <input
              v-model="fn.pattern"
              type="text"
              class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:text-gray-200 font-mono"
              :placeholder="t('autoTag.patternPlaceholder')"
              @input="debouncedPreview"
            />
            <div class="flex flex-wrap gap-1.5 pt-0.5">
              <button
                v-for="p in FN_PRESETS"
                :key="p.pattern"
                class="px-2.5 py-1 text-[11px] rounded-lg border transition-colors"
                :class="fn.pattern === p.pattern
                  ? 'bg-indigo-100 dark:bg-indigo-900/40 border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300'
                  : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
                @click="selectPreset(p.pattern)"
              >{{ p.label }}</button>
            </div>
          </div>

          <!-- 파싱 미리보기 -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{{ t('autoTag.previewTitle') }}</label>
              <span class="text-[11px] text-gray-400">{{ props.files.length }}{{ t('autoTag.filesCount') }}</span>
            </div>
            <div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
              <div class="overflow-auto max-h-56">
                <table class="w-full text-[11px] border-collapse">
                  <thead>
                    <tr class="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 sticky top-0 z-10">
                      <th class="px-2 py-2 text-left font-medium whitespace-nowrap border-r border-gray-200 dark:border-gray-700" rowspan="2">{{ t('autoTag.colFilename') }}</th>
                      <th class="px-2 py-1.5 text-center font-medium border-r border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-700/60" colspan="4">{{ t('autoTag.colCurrent') }}</th>
                      <th class="px-2 py-1.5 text-center font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10" colspan="5">{{ t('autoTag.colParsed') }}</th>
                    </tr>
                    <tr class="bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-500 text-[10px] sticky top-[33px] z-10">
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('autoTag.colArtist') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('autoTag.colTitle') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap bg-gray-100 dark:bg-gray-700/60">{{ t('autoTag.colGenre') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap border-r border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-700/60">{{ t('autoTag.colYear') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('autoTag.colArtist') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('autoTag.colTitle') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('autoTag.colTrack') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('autoTag.colDisc') }}</th>
                      <th class="px-2 py-1 text-left font-normal whitespace-nowrap text-indigo-500 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10">{{ t('autoTag.colYear') }}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                    <tr v-for="row in fn.previewRows" :key="row.path"
                      :class="row.error ? 'bg-red-50/50 dark:bg-red-900/5' : 'hover:bg-gray-50 dark:hover:bg-gray-800/40'"
                    >
                      <td class="px-2 py-1.5 text-gray-400 dark:text-gray-500 max-w-[120px] truncate font-mono text-[10px] border-r border-gray-100 dark:border-gray-800">{{ stemOf(fileMap[row.path]?.filename || '') }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[90px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ fileMap[row.path]?.artist || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[100px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ fileMap[row.path]?.title || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 max-w-[70px] truncate bg-gray-50/30 dark:bg-gray-800/20">{{ fileMap[row.path]?.genre || '' }}</td>
                      <td class="px-2 py-1.5 text-gray-500 dark:text-gray-400 border-r border-gray-100 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/20">{{ fileMap[row.path]?.year || '' }}</td>
                      <td class="px-2 py-1.5 max-w-[90px] truncate" :class="row.error ? 'text-red-400' : diffClass(row.path, 'artist', row.parsed?.artist)">
                        <span v-if="row.error" class="text-[10px]">✗ {{ t('autoTag.parseNoMatch') }}</span>
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
              <span class="inline-block w-2 h-2 rounded bg-indigo-200 dark:bg-indigo-700 mr-1"></span>{{ t('autoTag.previewLegend') }}
            </p>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             STEP: fn_running  (파일명 모드 실행 중)
        ══════════════════════════════════════════════════════════ -->
        <div v-else-if="step === 'fn_running'" class="flex-1 flex flex-col items-center justify-center px-5 py-10 gap-5">
          <svg class="animate-spin w-10 h-10 text-indigo-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          <div class="text-center space-y-1.5 w-full max-w-xs">
            <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {{ t('autoTag.running') }}
              <span class="text-indigo-600 dark:text-indigo-400 ml-1">{{ fn.progress.current }} / {{ fn.progress.total }}</span>
            </p>
            <div class="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-500 rounded-full transition-all duration-300"
                :style="{ width: fn.progress.total > 0 ? (fn.progress.current / fn.progress.total * 100) + '%' : '0%' }" />
            </div>
            <p v-if="fn.progress.filename" class="text-[11px] text-gray-400 dark:text-gray-500 truncate">{{ fn.progress.filename }}</p>
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 text-center">{{ t('autoTag.runningNote') }}</p>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             STEP: fn_result  (파일명 모드 결과)
        ══════════════════════════════════════════════════════════ -->
        <div v-else-if="step === 'fn_result'" class="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-0">
          <div class="flex flex-wrap items-center gap-2">
            <div v-if="fn.revertMessage" class="flex items-center gap-1.5 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-xs text-blue-600 dark:text-blue-400">↩ {{ fn.revertMessage }}</div>
            <template v-else>
              <div v-if="fn.summary.applied" class="flex items-center gap-1.5 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <span class="text-green-600 dark:text-green-400 font-bold text-sm">{{ fn.summary.applied }}</span>
                <span class="text-xs text-green-600 dark:text-green-400">{{ t('autoTag.applied') }}</span>
              </div>
              <div v-if="fn.summary.kept_existing" class="flex items-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-xl">
                <span class="text-gray-500 font-bold text-sm">{{ fn.summary.kept_existing }}</span>
                <span class="text-xs text-gray-500">{{ t('autoTag.keptExisting') }}</span>
              </div>
              <div v-if="fn.summary.applied_parsed" class="flex items-center gap-1.5 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <span class="text-blue-500 font-bold text-sm">{{ fn.summary.applied_parsed }}</span>
                <span class="text-xs text-blue-500">{{ t('autoTag.appliedParsed') }}</span>
              </div>
              <div v-if="fn.summary.error" class="flex items-center gap-1.5 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-xl">
                <span class="text-red-500 font-bold text-sm">{{ fn.summary.error }}</span>
                <span class="text-xs text-red-500">{{ t('autoTag.error') }}</span>
              </div>
            </template>
          </div>
          <div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
            <div class="overflow-auto max-h-[400px]">
              <table class="w-full text-[11px] border-collapse">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 sticky top-0 z-10">
                    <th class="px-2 py-2 text-left font-medium whitespace-nowrap border-r border-gray-200 dark:border-gray-700">{{ t('autoTag.colFilename') }}</th>
                    <th class="px-2 py-1.5 text-center font-medium w-8">{{ t('autoTag.colStatus') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium border-l border-gray-200 dark:border-gray-700">{{ t('autoTag.colArtist') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium">{{ t('autoTag.colTitle') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium">{{ t('autoTag.colAlbum') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium">{{ t('autoTag.colGenre') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium">{{ t('autoTag.colYear') }}</th>
                    <th class="px-2 py-1.5 text-left font-medium">{{ t('autoTag.colSource') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                  <tr v-for="r in fn.results" :key="r.path" class="hover:bg-gray-50 dark:hover:bg-gray-800/40">
                    <td class="px-2 py-1.5 text-gray-400 dark:text-gray-500 max-w-[130px] truncate font-mono text-[10px] border-r border-gray-100 dark:border-gray-800">{{ stemOf(r.filename) }}</td>
                    <td class="px-2 py-1.5 text-center">
                      <span v-if="r.status === 'applied' || r.status === 'reverted'" class="text-green-500">✅</span>
                      <span v-else-if="r.status === 'kept_existing'" class="text-gray-400 text-xs" :title="t('autoTag.keptExisting')">⏸</span>
                      <span v-else-if="r.status === 'applied_parsed'" class="text-blue-400 text-xs" :title="t('autoTag.appliedParsed')">📝</span>
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
                        {{ r.status === 'kept_existing' ? t('autoTag.keptExisting') : t('autoTag.appliedParsed') }}
                      </td>
                    </template>
                    <template v-else-if="r.status === 'reverted'">
                      <td colspan="6" class="px-2 py-1.5 text-[11px] text-blue-500 dark:text-blue-400 border-l border-gray-100 dark:border-gray-800">↩ {{ t('autoTag.reverted') }}</td>
                    </template>
                    <template v-else>
                      <td colspan="6" class="px-2 py-1.5 text-xs text-gray-400 border-l border-gray-100 dark:border-gray-800">
                        {{ r.status === 'no_match' ? t('autoTag.noMatch') : r.error }}
                      </td>
                    </template>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             STEP: alb_search  (앨범 검색)
        ══════════════════════════════════════════════════════════ -->
        <template v-else-if="step === 'alb_search'">
          <!-- 검색바 -->
          <div class="px-5 py-3 border-b border-gray-100 dark:border-gray-800 shrink-0 space-y-2">
            <!-- 검색 방식 칩 -->
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-[10px] text-gray-400 shrink-0">{{ t('tagSearch.searchMode') }}</span>
              <button
                v-for="sm in searchModes"
                :key="sm.key"
                class="px-2 py-0.5 rounded-full border text-[10px] font-medium transition-all"
                :class="alb.searchMode === sm.key
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-blue-400'"
                @click="setSearchMode(sm.key)"
              >{{ sm.label }}</button>
            </div>
            <!-- 검색 입력 -->
            <div class="flex gap-2">
              <input v-if="alb.searchMode === 'melon_id' || alb.searchMode === 'bugs_id'"
                v-model="alb.idInput"
                class="field flex-1 text-sm font-mono"
                :placeholder="alb.searchMode === 'melon_id' ? t('tagSearch.melonIdPlaceholder') : t('tagSearch.bugsIdPlaceholder')"
                @keyup.enter="doAlbumSearch"
                ref="albSearchInput"
              />
              <input v-else
                v-model="alb.query"
                class="field flex-1 text-sm"
                :placeholder="t('tagSearch.searchPlaceholder')"
                @keyup.enter="doAlbumSearch"
                ref="albSearchInput"
              />
              <button
                class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60 shrink-0"
                :disabled="alb.loading"
                @click="doAlbumSearch"
              >{{ alb.loading ? t('tagSearch.searching') : t('tagSearch.search') }}</button>
            </div>
            <!-- 소스 선택 (ID 모드 아닐 때) -->
            <div v-if="alb.searchMode !== 'melon_id' && alb.searchMode !== 'bugs_id'" class="flex items-center gap-2 flex-wrap">
              <span class="text-xs text-gray-400 shrink-0">{{ t('tagSearch.sourceLabel') }}</span>
              <button
                v-for="p in albProviders"
                :key="p.key"
                class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all"
                :class="alb.selectedSources.includes(p.key)
                  ? `${p.activeBg} ${p.activeText} ${p.activeBorder} shadow-sm`
                  : 'bg-white dark:bg-gray-800 text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300'"
                @click="toggleAlbSource(p.key)"
              >
                <img :src="p.logo" :alt="p.label" class="w-4 h-4 rounded object-cover shrink-0" />
                <span>{{ p.label }}</span>
              </button>
            </div>
          </div>

          <!-- 결과 목록 -->
          <div class="flex-1 overflow-y-auto px-5 py-4 space-y-2">
            <div v-if="alb.loading" class="flex items-center justify-center py-16 text-sm text-gray-400">{{ t('tagSearch.searching') }}</div>
            <div v-else-if="alb.error" class="text-center py-10 text-sm text-red-500">{{ alb.error }}</div>
            <div v-else-if="alb.results.length === 0 && alb.searched" class="text-center py-10 text-sm text-gray-400">{{ t('tagSearch.noResults') }}</div>
            <div
              v-for="result in alb.results"
              :key="(result.provider || 'sp') + '_' + (result.provider_id || result.spotify_id)"
              class="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 cursor-pointer transition-colors group"
              @click="selectAlbum(result)"
            >
              <img v-if="result.cover_url" :src="result.cover_url" class="w-14 h-14 rounded-lg object-cover shrink-0 shadow" />
              <div v-else class="w-14 h-14 rounded-lg bg-gray-200 dark:bg-gray-700 shrink-0 flex items-center justify-center text-gray-400">🎵</div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ result.album_title || result.title }}</p>
                  <span v-if="result.album_type" class="text-[10px] px-1.5 bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 rounded capitalize shrink-0">{{ result.album_type }}</span>
                  <span class="inline-flex items-center gap-1 text-[10px] pl-1 pr-1.5 py-0.5 rounded shrink-0" :class="providerBadgeClass(result.provider)">
                    <img v-if="providerLogo(result.provider)" :src="providerLogo(result.provider)" class="w-3.5 h-3.5 rounded object-cover" />
                    {{ providerLabel(result.provider) }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 truncate">{{ result.album_artist || result.artist }}</p>
                <div class="flex gap-2 mt-0.5 text-xs text-gray-400 flex-wrap">
                  <span v-if="result.release_date">{{ result.release_date }}</span>
                  <span v-if="result.total_tracks">· {{ t('tagSearch.trackCount', { n: result.total_tracks }) }}</span>
                  <span v-if="result.label">· {{ result.label }}</span>
                </div>
              </div>
              <span class="text-xs text-blue-500 group-hover:text-blue-600 dark:text-blue-400 shrink-0 pr-1">{{ t('tagSearch.selectArrow') }}</span>
            </div>
          </div>
        </template>

        <!-- ══════════════════════════════════════════════════════════
             STEP: alb_compare  (트랙 매칭 미리보기)
        ══════════════════════════════════════════════════════════ -->
        <template v-else-if="step === 'alb_compare' && alb.selectedAlbum">
          <div class="flex-1 overflow-y-auto">
            <!-- 앨범 정보 헤더 -->
            <div class="px-5 py-4 bg-gray-50 dark:bg-gray-800 flex gap-4 items-start border-b border-gray-200 dark:border-gray-700">
              <img v-if="alb.selectedAlbum.cover_url" :src="alb.selectedAlbum.cover_url" class="w-20 h-20 rounded-xl object-cover shadow shrink-0" />
              <div v-else class="w-20 h-20 rounded-xl bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-2xl shrink-0">💿</div>
              <div class="flex-1 min-w-0 text-sm">
                <div class="flex items-center gap-2 mb-0.5">
                  <p class="font-bold text-gray-900 dark:text-white text-base truncate">{{ alb.selectedAlbum.album_title || alb.selectedAlbum.title }}</p>
                  <span class="inline-flex items-center gap-1 text-[10px] pl-1 pr-1.5 py-0.5 rounded shrink-0" :class="providerBadgeClass(alb.selectedAlbum.provider)">
                    <img v-if="providerLogo(alb.selectedAlbum.provider)" :src="providerLogo(alb.selectedAlbum.provider)" class="w-3.5 h-3.5 rounded object-cover" />
                    {{ providerLabel(alb.selectedAlbum.provider) }}
                  </span>
                </div>
                <p class="text-gray-500 truncate">{{ alb.selectedAlbum.album_artist || alb.selectedAlbum.artist }}</p>
                <div class="flex gap-3 mt-1 text-xs text-gray-400 flex-wrap">
                  <span v-if="alb.selectedAlbum.release_date">📅 {{ alb.selectedAlbum.release_date }}</span>
                  <span v-if="alb.selectedAlbum.total_tracks">🎵 {{ t('tagSearch.trackCount', { n: alb.selectedAlbum.total_tracks }) }}</span>
                  <span v-if="alb.selectedAlbum.label">🏷 {{ alb.selectedAlbum.label }}</span>
                  <span v-if="alb.selectedAlbum.genres && alb.selectedAlbum.genres.length">🎸 {{ alb.selectedAlbum.genres.join(', ') }}</span>
                </div>
              </div>
            </div>

            <!-- 앨범 공통 태그 변경사항 -->
            <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700">
              <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{{ t('tagSearch.albumCommonTags') }}</p>
              <table class="w-full text-xs border-collapse">
                <thead>
                  <tr class="border-b border-gray-100 dark:border-gray-800">
                    <th class="text-left pb-2 pr-3 w-28 text-gray-400 font-medium">{{ t('tagSearch.colField') }}</th>
                    <th class="text-left pb-2 px-3 text-gray-400 font-medium w-1/2">{{ t('tagSearch.colBefore') }}</th>
                    <th class="text-left pb-2 pl-3 text-gray-400 font-medium w-1/2">{{ t('tagSearch.colAfter') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in albumRows" :key="row.key" class="border-b border-gray-50 dark:border-gray-800/50 last:border-0" :class="row.changed ? 'bg-green-50 dark:bg-green-900/10' : ''">
                    <td class="py-1.5 pr-3 text-gray-500 dark:text-gray-400 whitespace-nowrap align-top">{{ row.label }}</td>
                    <td class="py-1.5 px-3 align-top max-w-0">
                      <div class="truncate" :class="row.changed ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-600 dark:text-gray-300'">
                        <span v-if="row.current != null && row.current !== ''">{{ row.current }}</span>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                      </div>
                    </td>
                    <td class="py-1.5 pl-3 align-top max-w-0">
                      <div class="truncate" :class="row.changed ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-700 dark:text-gray-300'">
                        <span v-if="row.new != null && row.new !== ''">{{ row.new }}</span>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 트랙별 매칭 -->
            <div class="px-5 py-3">
              <div class="flex items-center justify-between mb-2">
                <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ t('tagSearch.trackTags') }}</p>
                <span class="text-xs text-gray-400">{{ t('tagSearch.matchCount', { matched: albMatchedCount, total: albTrackMatches.length }) }}</span>
              </div>
              <table class="w-full text-xs border-collapse">
                <thead>
                  <tr class="border-b border-gray-100 dark:border-gray-800">
                    <th class="text-right pb-2 pr-3 w-8 text-gray-400 font-medium">#</th>
                    <th class="text-left pb-2 px-3 text-gray-400 font-medium w-1/2">{{ t('tagSearch.colBefore') }}</th>
                    <th class="text-left pb-2 pl-3 text-gray-400 font-medium w-1/2">{{ t('tagSearch.colAfter') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(match, i) in albTrackMatches" :key="i"
                    class="border-b border-gray-50 dark:border-gray-800/50 last:border-0"
                    :class="!match.local || !match.remote ? 'opacity-40' : ''"
                  >
                    <td class="py-1.5 pr-3 text-gray-400 text-right whitespace-nowrap align-top">
                      <span v-if="match.remote?.disc_no > 1" class="text-gray-300 dark:text-gray-600">{{ match.remote.disc_no }}-</span>{{ match.remote?.track_no || (i + 1) }}.
                    </td>
                    <td class="py-1.5 px-3 text-gray-600 dark:text-gray-300 align-top max-w-0">
                      <div class="truncate">
                        <span v-if="match.local">{{ match.local.title || match.local.filename }}</span>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">{{ t('tagSearch.noMatch') }}</span>
                      </div>
                    </td>
                    <td class="py-1.5 pl-3 align-top max-w-0"
                      :class="match.local && match.remote && match.local.title !== match.remote.title ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-700 dark:text-gray-300'"
                    >
                      <div class="truncate">
                        <span v-if="match.remote">{{ match.remote.title }}</span>
                        <span v-else class="italic text-gray-300 dark:text-gray-600">—</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- ══════════════════════════════════════════════════════════
             STEP: alb_result  (앨범 모드 적용 결과)
        ══════════════════════════════════════════════════════════ -->
        <div v-else-if="step === 'alb_result'" class="flex-1 overflow-y-auto px-5 py-6 flex flex-col items-center justify-center gap-4 min-h-0">
          <div v-if="alb.reverted" class="flex flex-col items-center gap-2 text-center">
            <span class="text-3xl">↩</span>
            <p class="text-sm font-semibold text-blue-600 dark:text-blue-400">{{ t('autoTag.revertDone', { n: alb.applyCount }) }}</p>
          </div>
          <template v-else>
            <span class="text-3xl">✅</span>
            <p class="text-sm font-semibold text-gray-800 dark:text-gray-100">
              {{ t('autoTag.albApplyDone', { album: alb.selectedAlbum?.album_title || alb.selectedAlbum?.title || '', n: alb.applyCount }) }}
            </p>
            <button
              class="mt-2 px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 rounded-xl transition-colors disabled:opacity-40 font-medium"
              :disabled="alb.reverting || !historyStore.canUndo"
              @click="albDoRevert"
            >
              <span v-if="alb.reverting">{{ t('autoTag.reverting') }}</span>
              <span v-else>↩ {{ t('autoTag.revert') }} ({{ alb.applyCount }})</span>
            </button>
          </template>
        </div>

        <!-- ══════════════════════════════════════════════════════════
             Footer
        ══════════════════════════════════════════════════════════ -->
        <div class="px-5 py-3.5 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center shrink-0 gap-3">
          <!-- 왼쪽: 되돌리기 / 미매칭 재시도 -->
          <div class="flex gap-2">
            <button
              v-if="step === 'fn_result' && fnNoMatchFiles.length > 0 && !fn.reverting && !fn.revertMessage"
              class="px-3 py-2 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 rounded-xl transition-colors font-medium"
              @click="fnRetryNoMatch"
            >{{ t('autoTag.retryNoMatch') }} ({{ fnNoMatchFiles.length }})</button>
            <button
              v-if="step === 'fn_result' && fnAppliedResults.length > 0 && !fn.revertMessage"
              class="px-3 py-2 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 rounded-xl transition-colors font-medium disabled:opacity-50"
              :disabled="fn.reverting"
              @click="fnDoRevert"
            >
              <span v-if="fn.reverting">{{ t('autoTag.reverting') }}</span>
              <span v-else>↩ {{ t('autoTag.revert') }} ({{ fnAppliedResults.length }})</span>
            </button>
          </div>

          <!-- 오른쪽: 닫기 / 다음 / 실행 -->
          <div class="flex gap-2">
            <button
              v-if="step !== 'fn_running' && step !== 'alb_compare'"
              class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              @click="onClose"
            >{{ step === 'alb_result' || step === 'fn_result' ? t('common.close') : t('common.close') }}</button>

            <!-- select → 다음 -->
            <button
              v-if="step === 'select'"
              class="px-5 py-2 text-sm font-semibold rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              :class="mode === 'filename' ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : 'bg-blue-600 hover:bg-blue-500 text-white'"
              :disabled="!mode || selectedProviders.length === 0"
              @click="goFromSelect"
            >{{ t('autoTag.next') }}</button>

            <!-- fn_config → 실행 -->
            <button
              v-if="step === 'fn_config'"
              class="px-5 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
              :disabled="!canRunFn"
              @click="runFilename"
            >{{ t('autoTag.runBtn') }}</button>

            <!-- alb_compare → 적용 / 닫기 -->
            <template v-if="step === 'alb_compare'">
              <button class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors" @click="onClose">{{ t('common.cancel') }}</button>
              <button
                class="px-5 py-2 text-sm bg-green-600 hover:bg-green-500 disabled:opacity-60 text-white font-semibold rounded-xl transition-colors"
                :disabled="alb.applying"
                @click="applyAlbum"
              >{{ alb.applying ? t('tagSearch.applying') : t('tagSearch.applyAll') }}</button>
            </template>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { browseApi, metadataApi, albumsApi } from '../api/index.js'
import { metadataApi as metaApiFull } from '../api/metadata.js'
import { configApi } from '../api/config.js'
import { useBrowserStore } from '../stores/browser.js'
import { useToastStore } from '../stores/toast.js'
import { useHistoryStore } from '../stores/history.js'

const props = defineProps({
  modelValue:  { type: Boolean, default: false },
  files:       { type: Array,   default: () => [] },  // 대상 파일 목록
  folderName:  { type: String,  default: '' },         // 폴더명 (앨범 검색 자동완성용)
})
const emit = defineEmits(['update:modelValue', 'done'])

const { t } = useI18n()
const browserStore = useBrowserStore()
const toastStore = useToastStore()
const historyStore = useHistoryStore()

// ── 공통 상태 ─────────────────────────────────────────────
const step = ref('select')   // 'select' | 'fn_config' | 'fn_running' | 'fn_result' | 'alb_search' | 'alb_compare'
const mode = ref('album') // 'filename' | 'album'
const selectedProviders = ref([])

// ── Provider 메타 ──────────────────────────────────────────
const PROVIDER_META = {
  spotify:               { key: 'spotify',               label: 'Spotify',               logo: '/logo/spotify.jpg',              activeBg: 'bg-green-50 dark:bg-green-900/30',     activeText: 'text-green-700 dark:text-green-300',     activeBorder: 'border-green-400 dark:border-green-600' },
  bugs:                  { key: 'bugs',                  label: 'Bugs',                  logo: '/logo/bugs.jpg',                 activeBg: 'bg-orange-50 dark:bg-orange-900/30',   activeText: 'text-orange-700 dark:text-orange-300',   activeBorder: 'border-orange-400 dark:border-orange-600' },
  apple_music:           { key: 'apple_music',           label: 'Apple Music',           logo: '/logo/apple%20music.jpg',        activeBg: 'bg-red-50 dark:bg-red-900/30',         activeText: 'text-red-700 dark:text-red-300',         activeBorder: 'border-red-400 dark:border-red-600' },
  apple_music_classical: { key: 'apple_music_classical', label: 'Apple Music Classical', logo: '/logo/Apple%20Music%20Classical.jpg', activeBg: 'bg-pink-50 dark:bg-pink-900/30',   activeText: 'text-pink-700 dark:text-pink-300',       activeBorder: 'border-pink-400 dark:border-pink-600' },
  melon:                 { key: 'melon',                 label: 'Melon',                 logo: '/logo/melon.jpg',                activeBg: 'bg-emerald-50 dark:bg-emerald-900/30', activeText: 'text-emerald-700 dark:text-emerald-300', activeBorder: 'border-emerald-400 dark:border-emerald-600' },
}

const allProviders = ref([])    // 활성화된 provider 목록 (설정에서 로드)

function providerMeta(key) { return PROVIDER_META[key] || { label: key, logo: '' } }
function providerLabel(key) { return PROVIDER_META[key]?.label || key || '' }
function providerLogo(key) { return PROVIDER_META[key]?.logo || null }
function providerBadgeClass(provider) {
  return { spotify: 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400', bugs: 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400', melon: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400', apple_music: 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400', apple_music_classical: 'bg-pink-100 dark:bg-pink-900/40 text-pink-600 dark:text-pink-400' }[provider] || 'bg-gray-100 dark:bg-gray-800 text-gray-500'
}

function toggleProvider(key) {
  const idx = selectedProviders.value.indexOf(key)
  if (idx === -1) selectedProviders.value.push(key)
  else selectedProviders.value.splice(idx, 1)
}

// ── 파일 맵 ───────────────────────────────────────────────
const fileMap = computed(() => {
  const m = {}
  for (const f of props.files) m[f.path] = f
  return m
})

// ── Breadcrumb ────────────────────────────────────────────
const breadcrumbs = computed(() => {
  const STEPS = {
    filename: [
      { key: 'select',     label: t('autoTag.stepSelect') },
      { key: 'fn_config',  label: t('autoTag.stepConfig') },
      { key: 'fn_running', label: t('autoTag.stepRunning') },
      { key: 'fn_result',  label: t('autoTag.stepResult') },
    ],
    album: [
      { key: 'select',      label: t('autoTag.stepSelect') },
      { key: 'alb_search',  label: t('autoTag.stepSearch') },
      { key: 'alb_compare', label: t('autoTag.stepCompare') },
      { key: 'alb_result',  label: t('autoTag.stepResult') },
    ],
  }
  const list = STEPS[mode.value] || STEPS.filename
  const cur = list.findIndex(s => s.key === step.value)
  return list.map((s, i) => ({ ...s, active: i === cur, done: i < cur }))
})

const canGoBack = computed(() =>
  ['fn_config', 'alb_search', 'alb_compare'].includes(step.value)
)

function goBack() {
  if (step.value === 'fn_config') step.value = 'select'
  else if (step.value === 'alb_search') step.value = 'select'
  else if (step.value === 'alb_compare') step.value = 'alb_search'
}

// ── 다이얼로그 열릴 때 초기화 ────────────────────────────
watch(() => props.modelValue, async (open) => {
  if (!open) return
  step.value = 'select'
  mode.value = 'album'
  fn.pattern = ''
  fn.previewRows = []
  fn.results = []
  fn.revertMessage = ''
  fn.summary = { applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 }
  fn.progress = { current: 0, total: 0, filename: '' }
  alb.query = ''
  alb.results = []
  alb.selectedAlbum = null
  alb.remoteTracks = []
  alb.searched = false
  alb.applyCount = 0
  alb.reverted = false
  alb.reverting = false
  await loadProviders()
})

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
    allProviders.value = Object.entries(enabled).filter(([, v]) => v).map(([k]) => PROVIDER_META[k]).filter(Boolean)
  } catch {
    allProviders.value = [PROVIDER_META.spotify, PROVIDER_META.bugs, PROVIDER_META.melon].filter(Boolean)
  }
  selectedProviders.value = []
}

// ═══════════════════════════════════════════════════════════
//  SELECT → 다음 단계
// ═══════════════════════════════════════════════════════════
async function goFromSelect() {
  if (mode.value === 'filename') {
    step.value = 'fn_config'
    if (!fn.pattern) await detectPattern()
    else await loadFnPreview()
  } else {
    step.value = 'alb_search'
    alb.selectedSources = [...selectedProviders.value]
    initAlbumQuery()
    await nextTick()
    albSearchInput.value?.focus()
    if (alb.query) doAlbumSearch()
  }
}

// ═══════════════════════════════════════════════════════════
//  파일명 모드 (fn_*)
// ═══════════════════════════════════════════════════════════
const fn = reactive({
  pattern:          '',
  detectedPattern:  '',
  detectedConfidence: 0,
  detecting:        false,
  previewRows:      [],
  results:          [],
  summary:          { applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 },
  progress:         { current: 0, total: 0, filename: '' },
  reverting:        false,
  revertMessage:    '',
})

const FN_PRESETS = computed(() => [
  { label: t('filenameAutoTag.presets.melonChart'),       pattern: '%track%-%artist%-%disc%-%title%' },
  { label: t('filenameAutoTag.presets.trackArtistTitle'), pattern: '%track% - %artist% - %title%' },
  { label: t('filenameAutoTag.presets.artistTrackTitle'), pattern: '%artist% - %track% - %title%' },
  { label: t('filenameAutoTag.presets.artistTitle'),      pattern: '%artist% - %title%' },
  { label: t('filenameAutoTag.presets.trackTitle'),       pattern: '%track% - %title%' },
  { label: t('filenameAutoTag.presets.trackTitleNoSpace'),pattern: '%track%-%title%' },
])

const canRunFn = computed(() => fn.pattern.trim() && selectedProviders.value.length > 0 && props.files.length > 0)
const fnNoMatchFiles   = computed(() => fn.results.filter(r => r.status === 'kept_existing' || r.status === 'applied_parsed').map(r => r.path))
const fnAppliedResults = computed(() => fn.results.filter(r => (r.status === 'applied' || r.status === 'applied_parsed') && r.original))

function stemOf(filename) { return filename ? filename.replace(/\.[^.]+$/, '') : '' }

function diffClass(path, field, parsedVal) {
  if (parsedVal === undefined || parsedVal === null || parsedVal === '') return 'text-gray-700 dark:text-gray-300'
  const cur = fileMap.value[path]?.[field]
  return String(parsedVal) !== String(cur ?? '')
    ? 'text-indigo-600 dark:text-indigo-400 font-medium'
    : 'text-gray-500 dark:text-gray-400'
}

async function detectPattern() {
  if (!props.files.length) return
  fn.detecting = true
  try {
    const paths = props.files.map(f => f.path)
    const { data } = await browseApi.detectFilenamePattern(paths)
    fn.detectedPattern    = data.pattern
    fn.detectedConfidence = data.confidence
    fn.pattern            = data.pattern
    await loadFnPreview()
  } catch {
    fn.pattern = '%artist% - %title%'
    await loadFnPreview()
  } finally {
    fn.detecting = false
  }
}

async function loadFnPreview() {
  if (!fn.pattern || !props.files.length) return
  try {
    const paths = props.files.map(f => f.path)
    const { data } = await browseApi.tagFromNamePreview(paths, fn.pattern)
    fn.previewRows = data.results || []
  } catch {
    fn.previewRows = []
  }
}

let _previewTimer = null
function debouncedPreview() {
  clearTimeout(_previewTimer)
  _previewTimer = setTimeout(loadFnPreview, 400)
}

function selectPreset(p) {
  fn.pattern = p
  loadFnPreview()
}

async function runFilename() {
  if (!canRunFn.value) return
  step.value = 'fn_running'
  fn.revertMessage = ''
  fn.results = []
  fn.progress = { current: 0, total: props.files.length, filename: '' }

  try {
    await metaApiFull.autoTagByFilenameStream(
      {
        paths:           props.files.map(f => f.path),
        pattern:         fn.pattern,
        providers:       selectedProviders.value,
        match_threshold: 70.0,
      },
      {
        onProgress(current, total, filename, item) {
          fn.progress = { current, total, filename }
          if (item) fn.results.push(item)
        },
        onDone(s) {
          fn.summary = s || { applied: 0, kept_existing: 0, applied_parsed: 0, parse_error: 0, error: 0 }
          step.value = 'fn_result'
          emit('done')
        },
      }
    )
  } catch (e) {
    step.value = 'fn_config'
    console.error('auto-tag-by-filename error', e)
  }
}

async function fnDoRevert() {
  if (!fnAppliedResults.value.length) return
  if (!confirm(t('autoTag.revertConfirm'))) return
  fn.reverting = true
  try {
    const items = fnAppliedResults.value.map(r => ({ path: r.path, original: r.original }))
    const { data } = await metaApiFull.revertAutoTag(items)
    fn.revertMessage = t('autoTag.revertDone', { n: data.reverted })
    fn.results = fn.results.map(r => r.status === 'applied' ? { ...r, status: 'reverted' } : r)
    emit('done')
  } catch (e) {
    console.error('revert error', e)
  } finally {
    fn.reverting = false
  }
}

function fnRetryNoMatch() {
  step.value = 'select'
  mode.value = 'album'
}

// ═══════════════════════════════════════════════════════════
//  앨범 검색 모드 (alb_*)
// ═══════════════════════════════════════════════════════════
const alb = reactive({
  query:         '',
  idInput:       '',
  searchMode:    'album',    // 'album' | 'artist_album' | 'title_album' | 'melon_id' | 'bugs_id'
  selectedSources: [],
  loading:       false,
  applying:      false,
  error:         '',
  results:       [],
  searched:      false,
  selectedAlbum: null,
  remoteTracks:  [],
  loadingProvider: 'spotify',
  applyCount:    0,
  reverted:      false,
  reverting:     false,
})

const albSearchInput = ref(null)

const searchModes = computed(() => [
  { key: 'album',        label: t('tagSearch.modeAlbum') },
  { key: 'artist_album', label: t('tagSearch.modeArtistAlbum') },
  { key: 'title_album',  label: t('tagSearch.modeTitleAlbum') },
  { key: 'melon_id',     label: t('tagSearch.modeMelonId') },
  { key: 'bugs_id',      label: t('tagSearch.modeBugsId') },
])

const albProviders = computed(() =>
  allProviders.value.filter(p => ['spotify', 'bugs', 'melon', 'apple_music', 'apple_music_classical'].includes(p.key))
)

function toggleAlbSource(key) {
  const idx = alb.selectedSources.indexOf(key)
  if (idx >= 0) {
    if (alb.selectedSources.length > 1) alb.selectedSources.splice(idx, 1)
  } else {
    alb.selectedSources.push(key)
  }
}

function setSearchMode(sm) {
  alb.searchMode = sm
  if (sm === 'melon_id') {
    alb.selectedSources = ['melon']
    alb.idInput = ''
  } else if (sm === 'bugs_id') {
    alb.selectedSources = ['bugs']
    alb.idInput = ''
  } else {
    updateAlbQuery(sm)
  }
}

function parseFolderNameToQuery(name) {
  if (!name) return ''
  let s = name
  s = s.replace(/[\[(]\d{4}[\d.\s/-]*[\])]/g, '')
  s = s.replace(/[\[(][^\]([]*?(flac|mp3|aac|wav|alac|ape|ogg|wma|\d+kbps?|\d+bit|\d+-\d+|hq|hi-?res|hifi|lossless)[^\]([]*[\])]/gi, '')
  s = s.replace(/[\[(](bugs|melon|genie|flo|spotify|itunes|apple\s*music|youtube|soundcloud|tidal)[\])]/gi, '')
  s = s.replace(/\((deluxe|special|standard|limited|expanded|remaster(?:ed)?|edition|version|re-?release|anniversary|single|mini)[^)]*\)/gi, '')
  s = s.replace(/[\[(](disc|disk|cd|vol\.?)\s*\d+[\])]/gi, '')
  s = s.replace(/[\[(]\s*[\])]/g, '').replace(/\s{2,}/g, ' ').trim()
  s = s.replace(/[-_.]+$/, '').trim()
  return s
}

function initAlbumQuery() {
  const firstFile = props.files[0]
  const artist = firstFile?.album_artist || firstFile?.artist || ''
  const album  = firstFile?.album_title || parseFolderNameToQuery(props.folderName) || ''
  if (artist && album) {
    alb.searchMode = 'artist_album'
    alb.query = [artist, album].filter(Boolean).join(' ')
  } else {
    alb.searchMode = 'album'
    alb.query = album || firstFile?.title || ''
  }
}

function updateAlbQuery(sm) {
  const firstFile = props.files[0]
  const albumTitle = firstFile?.album_title || parseFolderNameToQuery(props.folderName) || ''
  const artist = firstFile?.album_artist || firstFile?.artist || ''
  const title  = firstFile?.title || ''
  if (sm === 'artist_album') alb.query = [artist, albumTitle].filter(Boolean).join(' ')
  else if (sm === 'title_album') alb.query = [title, albumTitle].filter(Boolean).join(' ')
  else alb.query = albumTitle
}

const albActiveProviders = computed(() =>
  alb.selectedSources.filter(p => allProviders.value.some(ap => ap.key === p))
)

async function doAlbumSearch() {
  if (alb.searchMode === 'melon_id' || alb.searchMode === 'bugs_id') {
    const id = alb.idInput.trim()
    if (!id) return
    const provider = alb.searchMode === 'melon_id' ? 'melon' : 'bugs'
    alb.loading = true
    alb.error = ''
    try {
      const { data } = await metadataApi.albumTracks(id, provider)
      const albumInfo = data.album || {}
      await selectAlbum({ provider, provider_id: id, album_title: albumInfo.album_title || albumInfo.title || id, artist: albumInfo.album_artist || albumInfo.artist, cover_url: albumInfo.cover_url, ...albumInfo })
    } catch (e) {
      alb.error = e.response?.data?.detail || t('tagSearch.searchFailed')
      alb.searched = true
    } finally {
      alb.loading = false
    }
    return
  }

  const q = alb.query.trim()
  if (!q || !albActiveProviders.value.length) return
  alb.loading = true
  alb.error = ''
  alb.results = []
  alb.searched = false

  try {
    const searches = albActiveProviders.value.map(async (provider) => {
      const { data } = await metadataApi.search({ q, type: 'album', limit: 8, provider })
      if (data.results.length) return data.results
      const { data: td } = await metadataApi.search({ q, type: 'track', limit: 5, provider })
      return td.results
    })
    const allResults = await Promise.all(searches)
    alb.results = allResults.flat()
    alb.searched = true
  } catch {
    alb.error = t('tagSearch.searchFailed')
  } finally {
    alb.loading = false
  }
}

async function selectAlbum(album) {
  alb.selectedAlbum = album
  alb.remoteTracks = []
  const provider = album.provider || 'spotify'
  const id = album.provider_id || album.spotify_id
  alb.loadingProvider = provider

  if (id && (album.album_type || album.total_tracks || album.type === 'album')) {
    try {
      const { data } = await metadataApi.albumTracks(id, provider)
      alb.remoteTracks = data.tracks || []
      if (data.album && Object.keys(data.album).length) {
        alb.selectedAlbum = { ...album, ...data.album }
      }
    } catch {
      alb.remoteTracks = []
    }
  } else if (album.title) {
    alb.remoteTracks = [album]
  }

  step.value = 'alb_compare'
}

// 로컬 파일 (체크된 파일 우선, 없으면 전체)
const localFiles = computed(() =>
  browserStore.checkedPaths.size > 0 ? browserStore.checkedFiles : props.files
)

const albTrackMatches = computed(() => {
  const locals = [...localFiles.value].sort((a, b) => {
    if (a.track_no && b.track_no) return a.track_no - b.track_no
    return (a.filename || '').localeCompare(b.filename || '')
  })
  const remote = [...alb.remoteTracks].sort((a, b) => {
    if (a.disc_no !== b.disc_no) return (a.disc_no || 1) - (b.disc_no || 1)
    return (a.track_no || 0) - (b.track_no || 0)
  })
  const matches = []
  const usedRemote = new Set()
  const trackKey = (t) => t.provider_id || t.spotify_id || t.title

  for (const local of locals) {
    let rm = null
    if (local.track_no) rm = remote.find(r => !usedRemote.has(trackKey(r)) && r.track_no === local.track_no)
    if (rm) usedRemote.add(trackKey(rm))
    matches.push({ local, remote: rm || null })
  }
  const unmatched = remote.filter(r => !usedRemote.has(trackKey(r)))
  let ui = 0
  for (const m of matches) {
    if (!m.remote && ui < unmatched.length) m.remote = unmatched[ui++]
  }
  for (; ui < unmatched.length; ui++) matches.push({ local: null, remote: unmatched[ui] })
  return matches
})

const albMatchedCount = computed(() => albTrackMatches.value.filter(m => m.local && m.remote).length)

const albumRows = computed(() => {
  if (!alb.selectedAlbum || !props.files.length) return []
  const c = props.files[0]
  const s = alb.selectedAlbum
  const genre = s.genre || (s.genres && s.genres[0]) || null
  const truncate = (v, n = 80) => v && v.length > n ? v.slice(0, n) + '…' : v
  return [
    { key: 'artist',       label: t('tagSearch.fieldArtist'),      current: c.artist,       new: s.album_artist || s.artist },
    { key: 'album_artist', label: t('tagSearch.fieldAlbumArtist'), current: c.album_artist, new: s.album_artist },
    { key: 'album_title',  label: t('tagSearch.fieldAlbum'),       current: c.album_title,  new: s.album_title || s.title },
    { key: 'genre',        label: t('tagSearch.fieldGenre'),       current: c.genre,        new: genre,        alwaysShow: true },
    { key: 'year',         label: t('tagSearch.fieldYear'),        current: c.year,         new: s.year },
    { key: 'release_date', label: t('tagSearch.fieldReleaseDate'), current: null,           new: s.release_date },
    { key: 'total_tracks', label: t('tagSearch.fieldTotalTracks'), current: null,           new: s.total_tracks },
    { key: 'label',        label: t('tagSearch.fieldLabel'),       current: null,           new: s.label },
    { key: 'description',  label: t('tagSearch.fieldDescription'), current: null,           new: truncate(s.description), alwaysShow: true },
  ]
    .filter(r => r.alwaysShow || (r.new != null && r.new !== ''))
    .map(r => ({ ...r, changed: r.current != null ? String(r.current) !== String(r.new) : false }))
})

async function applyAlbum() {
  if (!alb.selectedAlbum) return
  alb.applying = true
  const s = alb.selectedAlbum
  const genre = s.genre || (s.genres && s.genres[0]) || null

  const albumUpdates = {}
  if (s.album_artist || s.artist) albumUpdates.artist       = s.album_artist || s.artist
  if (s.album_artist)             albumUpdates.album_artist = s.album_artist
  if (s.album_title || s.title)   albumUpdates.album_title  = s.album_title || s.title
  if (genre)                      albumUpdates.genre        = genre
  if (s.year)                     albumUpdates.year         = s.year
  if (s.release_date)             albumUpdates.release_date = s.release_date
  if (s.total_tracks)             albumUpdates.total_tracks = s.total_tracks
  if (s.label)                    albumUpdates.label        = s.label

  // 되돌리기용 스냅샷 (적용 전 현재 태그 상태 수집)
  const snapshotFields = ['artist', 'album_artist', 'album_title', 'genre', 'year', 'release_date', 'total_tracks', 'label', 'title', 'track_no', 'disc_no']
  const beforeSnapshot = {}
  for (const f of localFiles.value) {
    beforeSnapshot[f.path] = Object.fromEntries(snapshotFields.map(k => [k, f[k] ?? null]))
  }

  try {
    const paths = localFiles.value.map(f => f.path)

    if (Object.keys(albumUpdates).length) {
      if (s.cover_url) {
        await Promise.allSettled(paths.map(path => metadataApi.applyByPath({ path, ...albumUpdates, cover_url: s.cover_url })))
        browserStore.updateFiles(paths, { ...albumUpdates, has_cover: true })
        const folderPath = browserStore.selectedFolder?.path
        if (folderPath) browserStore.invalidateFilesCache(folderPath)
      } else {
        await browseApi.batchWriteTags({ paths, ...albumUpdates })
        browserStore.updateFiles(paths, albumUpdates)
      }
    }

    const trackWriteJobs = albTrackMatches.value
      .filter(m => m.local && m.remote)
      .map(m => {
        const rm = m.remote
        const tu = {}
        if (rm.title)    tu.title    = rm.title
        if (rm.track_no) tu.track_no = rm.track_no
        if (rm.disc_no)  tu.disc_no  = rm.disc_no
        if (rm.artist && rm.artist !== (s.album_artist || s.artist)) tu.artist = rm.artist
        if (!Object.keys(tu).length) return null
        return browseApi.writeTags({ path: m.local.path, ...tu })
          .then(() => browserStore.updateFile({ path: m.local.path, ...tu }))
      })
      .filter(Boolean)
    if (trackWriteJobs.length) await Promise.allSettled(trackWriteJobs)

    const titleTrackJobs = albTrackMatches.value
      .filter(m => m.local && m.remote && m.remote.is_title_track !== undefined)
      .map(m =>
        browseApi.setTrackInfo({ path: m.local.path, is_title_track: !!m.remote.is_title_track })
          .then(() => browserStore.updateFile({ path: m.local.path, is_title_track: !!m.remote.is_title_track }))
          .catch(e => console.warn('is_title_track 저장 실패:', m.local.path, e))
      )
    if (titleTrackJobs.length) await Promise.allSettled(titleTrackJobs)

    if (s.description) {
      let albumId = props.files[0]?.album_id
      if (!albumId) {
        const title  = (s.album_title || s.title || '').trim()
        const artist = (s.album_artist || s.artist || '').trim()
        if (title) {
          try { const { data } = await albumsApi.ensureAlbum(title, artist); albumId = data.id } catch {}
        }
      }
      if (albumId) {
        try { await albumsApi.setDescription(albumId, s.description) } catch {}
      }
    }

    const folderPath = browserStore.selectedFolder?.path
    if (folderPath) {
      browserStore.invalidateFilesCache(folderPath)
      if (browserStore.folderGroups.length > 0) await browserStore.loadRecursiveFiles(folderPath)
      else await browserStore.loadFiles(folderPath, true)
    }

    alb.applyCount = localFiles.value.length
    alb.reverted = false

    // 히스토리 등록 (되돌리기/다시 실행 지원)
    const historyOps = localFiles.value.map(f => {
      const after = { ...beforeSnapshot[f.path], ...albumUpdates }
      // 트랙별 개별 변경분 반영
      const trackMatch = albTrackMatches.value.find(m => m.local?.path === f.path)
      if (trackMatch?.remote) {
        const rm = trackMatch.remote
        if (rm.title)    after.title    = rm.title
        if (rm.track_no) after.track_no = rm.track_no
        if (rm.disc_no)  after.disc_no  = rm.disc_no
        if (rm.artist && rm.artist !== (s.album_artist || s.artist)) after.artist = rm.artist
      }
      return { path: f.path, before: beforeSnapshot[f.path], after }
    })
    if (historyOps.length) {
      const albumName = s.album_title || s.title || ''
      historyStore.push({
        label: t('autoTag.historyAlbum', { album: albumName, n: historyOps.length }),
        ops: historyOps,
      })
    }

    emit('done')
    step.value = 'alb_result'
  } catch (e) {
    toastStore.error(e.response?.data?.detail || t('common.error'))
  } finally {
    alb.applying = false
  }
}

async function albDoRevert() {
  if (!historyStore.canUndo || alb.reverted) return
  alb.reverting = true
  try {
    await historyStore.undo(browserStore)
    alb.reverted = true
    emit('done')
  } finally {
    alb.reverting = false
  }
}

// ── 닫기 ──────────────────────────────────────────────────
function onClose() {
  if (step.value === 'fn_running') return
  emit('update:modelValue', false)
}
</script>
