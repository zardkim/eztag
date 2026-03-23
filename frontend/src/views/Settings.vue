<template>
  <div class="flex flex-col lg:flex-row h-full overflow-hidden">

    <!-- ── 탭 메뉴: 모바일 콤보박스 ── -->
    <div class="lg:hidden shrink-0 border-b border-gray-200 dark:border-gray-800 px-3 py-2 bg-gray-50 dark:bg-gray-900">
      <select v-model="activeTab" class="field w-full text-sm">
        <option v-for="tab in tabs" :key="tab.key" :value="tab.key">
          {{ tab.icon }} {{ tab.label }}
        </option>
      </select>
    </div>

    <!-- ── 탭 메뉴: 데스크톱 좌측 세로 ── -->
    <nav class="hidden lg:flex lg:flex-col shrink-0 bg-gray-50 dark:bg-gray-900 lg:w-44 lg:border-r border-gray-200 dark:border-gray-800 lg:py-4 lg:gap-0.5">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm w-full text-left transition-colors"
        :class="activeTab === tab.key
          ? 'bg-blue-600 text-white font-medium'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'"
        @click="activeTab = tab.key"
      >
        <span class="text-base leading-none shrink-0">{{ tab.icon }}</span>
        <span class="truncate">{{ tab.label }}</span>
      </button>
    </nav>

    <!-- ── 콘텐츠 영역 ── -->
    <div class="flex-1 overflow-y-auto">
      <div class="max-w-2xl p-4 sm:p-6">

        <!-- ── 일반 ── -->
        <template v-if="activeTab === 'general'">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-5">{{ $t('settings.general') }}</h2>

          <!-- 사이트 이름 / 브라우저 타이틀 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mb-4">
            <div class="space-y-4">
              <ConfigRow :label="$t('settings.siteName')" :desc="$t('settings.siteNameDesc')">
                <input v-model="form.site_name" type="text" class="field w-48" placeholder="eztag" @blur="saveGeneralConfig" @keydown.enter="saveGeneralConfig" />
              </ConfigRow>
              <ConfigRow :label="$t('settings.browserTitle')" :desc="$t('settings.browserTitleDesc')">
                <input v-model="form.browser_title" type="text" class="field w-48" placeholder="eztag" @blur="saveGeneralConfig" @keydown.enter="saveGeneralConfig" />
              </ConfigRow>
            </div>
          </section>

          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mb-4">
            <div class="space-y-4">
              <ConfigRow :label="$t('settings.appLanguage')" :desc="$t('settings.appLanguageDesc')">
                <select v-model="form.app_language" class="field w-36" @change="onLanguageChange">
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              </ConfigRow>
              <ConfigRow :label="$t('settings.theme')" :desc="$t('settings.themeDesc')">
                <div class="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-700 text-sm">
                  <button
                    class="px-3 py-1.5 transition-colors"
                    :class="themeStore.theme === 'dark'
                      ? 'bg-gray-700 text-white'
                      : 'bg-white text-gray-400 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-400'"
                    @click="themeStore.theme = 'dark'"
                  >🌙 {{ $t('settings.themeDark') }}</button>
                  <button
                    class="px-3 py-1.5 transition-colors"
                    :class="themeStore.theme === 'light'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-400 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-400'"
                    @click="themeStore.theme = 'light'"
                  >☀️ {{ $t('settings.themeLight') }}</button>
                </div>
              </ConfigRow>
            </div>
          </section>

        </template>

        <!-- ── 메타데이터 소스 ── -->
        <template v-else-if="activeTab === 'metadata'">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-5">{{ $t('settings.metadata.title') }}</h2>
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm">
            <!-- Spotify -->
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <img src="/logo/spotify.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Spotify" />
                  <span class="text-sm font-medium text-gray-900 dark:text-white">Spotify</span>
                  <span class="text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 px-1.5 py-0.5 rounded">{{ $t('settings.metadata.spotifyDefault') }}</span>
                </div>
                <button class="flex items-center gap-2 cursor-pointer" @click="form.spotify_enabled = !form.spotify_enabled; saveMetaConfig()">
                  <span class="text-xs" :class="form.spotify_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.spotify_enabled ? 'ON' : 'OFF' }}</span>
                  <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.spotify_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                    <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.spotify_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                  </span>
                </button>
              </div>
              <div class="space-y-2">
                <div>
                  <label class="text-xs text-gray-500 block mb-1">Client ID</label>
                  <div class="relative">
                    <input v-model="form.spotify_client_id" :type="showSpotifyId ? 'text' : 'password'" class="field w-full font-mono text-xs pr-8" placeholder="Spotify Developer Dashboard에서 확인" @blur="saveMetaConfig" />
                    <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="showSpotifyId = !showSpotifyId">
                      <svg v-if="showSpotifyId" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    </button>
                  </div>
                </div>
                <div>
                  <label class="text-xs text-gray-500 block mb-1">Client Secret</label>
                  <div class="relative">
                    <input v-model="form.spotify_client_secret" :type="showSpotifySecret ? 'text' : 'password'" class="field w-full font-mono text-xs pr-8" placeholder="••••••••••••••••••••••••••••••••" @blur="saveMetaConfig" />
                    <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="showSpotifySecret = !showSpotifySecret">
                      <svg v-if="showSpotifySecret" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
              <p class="text-xs text-gray-400 mt-2">
                <a href="https://developer.spotify.com/dashboard" target="_blank" class="text-blue-500 hover:underline">developer.spotify.com/dashboard</a>
                {{ $t('settings.metadata.spotifyHint') }}
              </p>
            </div>
            <!-- 기타 소스 -->
            <div class="space-y-2">
              <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5">
                <div class="flex items-center gap-2">
                  <img src="/logo/bugs.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Bugs" />
                  <span class="text-sm text-gray-600 dark:text-gray-300">Bugs</span>
                  <span class="text-xs bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">{{ $t('settings.metadata.available') }}</span>
                </div>
                <button class="flex items-center gap-2 cursor-pointer" @click="form.bugs_enabled = !form.bugs_enabled; saveMetaConfig()">
                  <span class="text-xs" :class="form.bugs_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.bugs_enabled ? 'ON' : 'OFF' }}</span>
                  <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.bugs_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                    <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.bugs_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                  </span>
                </button>
              </div>
              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <img src="/logo/apple%20music.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Apple Music" />
                    <span class="text-sm text-gray-600 dark:text-gray-300">Apple Music</span>
                    <span class="text-xs bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">{{ $t('settings.metadata.available') }}</span>
                  </div>
                  <button class="flex items-center gap-2 cursor-pointer" @click="form.apple_music_enabled = !form.apple_music_enabled; saveMetaConfig()">
                    <span class="text-xs" :class="form.apple_music_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.apple_music_enabled ? 'ON' : 'OFF' }}</span>
                    <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.apple_music_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                      <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.apple_music_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                    </span>
                  </button>
                </div>
                <div v-if="form.apple_music_enabled" class="mt-2 flex items-center gap-2">
                  <label class="text-xs text-gray-500">{{ $t('settings.metadata.storefront') }}</label>
                  <select v-model="form.apple_music_storefront" class="field text-xs py-1 w-28" @change="saveMetaConfig">
                    <option value="kr">한국 (kr)</option>
                    <option value="us">미국 (us)</option>
                    <option value="jp">일본 (jp)</option>
                    <option value="gb">영국 (gb)</option>
                    <option value="de">독일 (de)</option>
                  </select>
                </div>
              </div>
              <!-- Apple Music Classical -->
              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <img src="/logo/Apple%20Music%20Classical.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Apple Music Classical" />
                    <span class="text-sm text-gray-600 dark:text-gray-300">Apple Music Classical</span>
                    <span class="text-xs bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">{{ $t('settings.metadata.available') }}</span>
                  </div>
                  <button class="flex items-center gap-2 cursor-pointer" @click="form.apple_music_classical_enabled = !form.apple_music_classical_enabled; saveMetaConfig()">
                    <span class="text-xs" :class="form.apple_music_classical_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.apple_music_classical_enabled ? 'ON' : 'OFF' }}</span>
                    <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.apple_music_classical_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                      <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.apple_music_classical_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                    </span>
                  </button>
                </div>
                <div v-if="form.apple_music_classical_enabled" class="mt-2 flex items-center gap-2">
                  <label class="text-xs text-gray-500">{{ $t('settings.metadata.storefront') }}</label>
                  <select v-model="form.apple_music_classical_storefront" class="field text-xs py-1 w-28" @change="saveMetaConfig">
                    <option value="us">미국 (us)</option>
                    <option value="gb">영국 (gb)</option>
                    <option value="de">독일 (de)</option>
                    <option value="jp">일본 (jp)</option>
                    <option value="kr">한국 (kr)</option>
                    <option value="fr">프랑스 (fr)</option>
                    <option value="au">호주 (au)</option>
                  </select>
                </div>
              </div>
              <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5">
                <div class="flex items-center gap-2">
                  <img src="/logo/melon.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Melon" />
                  <span class="text-sm text-gray-600 dark:text-gray-300">Melon</span>
                  <span class="text-xs bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 px-1.5 py-0.5 rounded">{{ $t('settings.metadata.available') }}</span>
                </div>
                <button class="flex items-center gap-2 cursor-pointer" @click="form.melon_enabled = !form.melon_enabled; saveMetaConfig()">
                  <span class="text-xs" :class="form.melon_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.melon_enabled ? 'ON' : 'OFF' }}</span>
                  <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.melon_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                    <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.melon_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                  </span>
                </button>
              </div>
            </div>
            <!-- YouTube MV -->
            <div class="border border-red-100 dark:border-red-900/40 rounded-lg p-4 mt-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <svg class="w-6 h-6 text-red-600 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
                  </svg>
                  <span class="text-sm font-medium text-gray-900 dark:text-white">YouTube</span>
                  <span class="text-xs text-gray-400">{{ $t('settings.metadata.youtubeHint') }}</span>
                </div>
                <button class="flex items-center gap-2 cursor-pointer" @click="form.youtube_enabled = !form.youtube_enabled; saveMetaConfig()">
                  <span class="text-xs" :class="form.youtube_enabled ? 'text-green-500' : 'text-gray-400'">{{ form.youtube_enabled ? 'ON' : 'OFF' }}</span>
                  <span class="relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200" :class="form.youtube_enabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                    <span class="inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200 mt-0.5" :class="form.youtube_enabled ? 'translate-x-4' : 'translate-x-0.5'"></span>
                  </span>
                </button>
              </div>
              <div>
                <label class="text-xs text-gray-500 block mb-1">API Key</label>
                <div class="relative">
                  <input v-model="form.youtube_api_key" :type="showYoutubeKey ? 'text' : 'password'" class="field w-full font-mono text-xs pr-8" placeholder="AIza..." @blur="saveMetaConfig" />
                  <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="showYoutubeKey = !showYoutubeKey">
                    <svg v-if="showYoutubeKey" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                  </button>
                </div>
              </div>
              <p class="text-xs text-gray-400 mt-2">
                <a href="https://console.cloud.google.com" target="_blank" class="text-blue-500 hover:underline">console.cloud.google.com</a>
                {{ $t('settings.metadata.youtubeApiHint') }}
              </p>
            </div>

          </section>

          <!-- LRC 소스 우선순위 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mt-4">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-1">🎵 {{ $t('settings.lrcSource.title') }}</h3>
            <p class="text-xs text-gray-500 mb-4">{{ $t('settings.lrcSource.desc') }}</p>
            <div class="space-y-3">
              <ConfigRow :label="$t('settings.lrcSource.primary')" :desc="$t('settings.lrcSource.primaryDesc')">
                <select v-model="form.lrc_primary_source" class="field w-40" @change="saveLrcSources">
                  <option value="bugs">🎵 Bugs 뮤직 (한국어)</option>
                  <option value="lrclib">🌐 LRCLIB.net (국제)</option>
                </select>
              </ConfigRow>
              <ConfigRow :label="$t('settings.lrcSource.fallback')" :desc="$t('settings.lrcSource.fallbackDesc')">
                <select v-model="form.lrc_fallback_source" class="field w-40" @change="saveLrcSources">
                  <option value="none">{{ $t('settings.lrcSource.fallbackNone') }}</option>
                  <option value="bugs">🎵 Bugs 뮤직 (한국어)</option>
                  <option value="lrclib">🌐 LRCLIB.net (국제)</option>
                </select>
              </ConfigRow>
            </div>
          </section>
        </template>

        <!-- ── 데이터 관리 ── -->
        <template v-else-if="activeTab === 'data'">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-5">{{ $t('settings.backup.title') }}</h2>
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">{{ $t('settings.backup.title') }}</h3>
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
              <div>
                <p class="text-sm text-gray-900 dark:text-white">{{ $t('settings.backup.backupTitle') }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ $t('settings.backup.backupDesc') }}</p>
              </div>
              <button
                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors shrink-0 disabled:opacity-60"
                :class="backupRunning ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white'"
                :disabled="backupRunning"
                @click="createBackup"
              >
                <span v-if="backupRunning" class="flex items-center gap-2">
                  <span class="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
                  {{ $t('settings.backup.creating') }}
                </span>
                <span v-else>{{ $t('settings.backup.create') }}</span>
              </button>
            </div>
            <div v-if="backups.length" class="space-y-2">
              <div
                v-for="bk in backups"
                :key="bk.filename"
                class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5"
              >
                <div>
                  <p class="text-sm text-gray-900 dark:text-white font-mono">{{ bk.filename }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">{{ bk.size_mb }} MB · {{ fmtDatetime(bk.created_at) }}</p>
                </div>
                <div class="flex items-center gap-3">
                  <button class="text-xs text-blue-500 hover:text-blue-400 transition-colors" @click="downloadBackup(bk.filename)">{{ $t('settings.backup.download') }}</button>
                  <button class="text-xs text-yellow-500 hover:text-yellow-400 transition-colors" @click="restoreBackup(bk.filename)">{{ $t('settings.backup.restore') }}</button>
                  <button class="text-xs text-red-500 hover:text-red-400 transition-colors" @click="deleteBackup(bk.filename)">{{ $t('settings.backup.delete') }}</button>
                </div>
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 dark:text-gray-600">{{ $t('settings.backup.empty') }}</p>
          </section>
        </template>

        <!-- ── 활동 로그 ── -->
        <template v-else-if="activeTab === 'logs'">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ $t('settings.activityLog.title') }}</h2>
            <button
              class="text-xs px-3 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-900/40 dark:hover:bg-red-900/70 text-red-600 dark:text-red-400 rounded-lg transition-colors disabled:opacity-50"
              :disabled="clearingLogs"
              @click="clearLogs"
            >{{ clearingLogs ? $t('settings.activityLog.clearing') : $t('settings.activityLog.clearAll') }}</button>
          </div>

          <!-- 필터 -->
          <div class="flex flex-wrap gap-2 mb-4">
            <select v-model="logFilter.type" class="field text-xs py-1.5 w-36" @change="loadLogs(1)">
              <option value="">{{ $t('settings.activityLog.allTypes') }}</option>
              <option value="tag_write">{{ $t('settings.activityLog.typeTagWrite') }}</option>
              <option value="rename">{{ $t('settings.activityLog.typeRename') }}</option>
              <option value="lrc_search">{{ $t('settings.activityLog.typeLrc') }}</option>
              <option value="login">{{ $t('settings.activityLog.typeLogin') }}</option>
              <option value="error">{{ $t('settings.activityLog.typeError') }}</option>
            </select>
            <input
              v-model="logFilter.search"
              class="field text-xs py-1.5 flex-1 min-w-32"
              :placeholder="$t('settings.activityLog.searchPlaceholder')"
              @keydown.enter="loadLogs(1)"
            />
            <button class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-lg transition-colors" @click="loadLogs(1)">{{ $t('common.search') }}</button>
          </div>

          <!-- 로그 목록 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl shadow-sm overflow-hidden">
            <div v-if="logsLoading" class="flex justify-center py-10">
              <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <div v-else-if="logItems.length === 0" class="py-10 text-center text-sm text-gray-400">{{ $t('settings.activityLog.empty') }}</div>
            <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
              <div v-for="item in logItems" :key="item.id" class="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div class="flex items-start gap-3">
                  <span class="text-base shrink-0 mt-0.5">{{ logTypeIcon(item.log_type) }}</span>
                  <div class="flex-1 min-w-0">
                    <div class="flex flex-wrap items-center gap-2 mb-0.5">
                      <span class="text-xs font-semibold px-1.5 py-0.5 rounded" :class="logTypeBadgeClass(item.log_type)">{{ $t('settings.activityLog.type_' + item.log_type) }}</span>
                      <span v-if="item.username" class="text-xs text-gray-500">{{ item.username }}</span>
                      <span class="text-xs text-gray-400 ml-auto">{{ fmtDatetime(item.created_at) }}</span>
                    </div>
                    <p class="text-sm text-gray-900 dark:text-white">{{ translateLog(item) }}</p>
                    <p v-if="item.file_path" class="text-xs text-gray-400 font-mono truncate mt-0.5">{{ item.file_path }}</p>
                    <p v-if="item.detail" class="text-xs text-gray-400 truncate mt-0.5">{{ item.detail }}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 페이지네이션 -->
          <div v-if="logTotal > logPageSize" class="flex items-center justify-center gap-2 mt-4">
            <button class="text-xs px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" :disabled="logPage <= 1" @click="loadLogs(logPage - 1)">◀</button>
            <span class="text-xs text-gray-500">{{ logPage }} / {{ Math.ceil(logTotal / logPageSize) }}</span>
            <button class="text-xs px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" :disabled="logPage >= Math.ceil(logTotal / logPageSize)" @click="loadLogs(logPage + 1)">▶</button>
          </div>
          <p class="text-center text-xs text-gray-400 mt-2">{{ $t('settings.activityLog.total', { n: logTotal }) }}</p>
        </template>

        <!-- ── 시스템 정보 ── -->
        <template v-else-if="activeTab === 'system'">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-5">{{ $t('settings.version.title') }}</h2>
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">{{ $t('settings.version.title') }}</h3>
            <div class="space-y-3 text-sm">
              <div class="flex items-center gap-4 py-2 border-b border-gray-100 dark:border-gray-800">
                <span class="text-gray-500 w-32">{{ $t('settings.version.app') }}</span>
                <span class="text-gray-900 dark:text-white font-mono">v{{ appVersion }}</span>
              </div>
              <div class="flex items-center gap-4 py-2 border-b border-gray-100 dark:border-gray-800">
                <span class="text-gray-500 w-32">{{ $t('settings.version.server') }}</span>
                <span class="text-gray-900 dark:text-white font-mono">{{ serverVersion || '-' }}</span>
              </div>
              <div class="flex items-center gap-4 py-2 border-b border-gray-100 dark:border-gray-800">
                <span class="text-gray-500 w-32">{{ $t('settings.version.build') }}</span>
                <span class="text-gray-600 dark:text-gray-400">{{ buildDate || '-' }}</span>
              </div>
              <div class="flex items-center gap-4 py-2 border-b border-gray-100 dark:border-gray-800">
                <span class="text-gray-500 w-32">{{ $t('settings.version.license') }}</span>
                <span class="text-gray-900 dark:text-white">MIT</span>
              </div>
              <div class="flex items-center gap-4 py-2">
                <span class="text-gray-500 w-32">{{ $t('settings.version.github') }}</span>
                <a
                  href="https://github.com/zardkim/eztag"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-1.5 text-blue-500 hover:text-blue-400 transition-colors"
                >
                  <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
                  </svg>
                  <span class="text-sm">zardkim/eztag</span>
                  <span class="text-xs text-gray-400">— {{ $t('settings.version.githubLink') }}</span>
                </a>
              </div>
            </div>
          </section>
        </template>

        <!-- ── 사용 설명서 ── -->
        <template v-else-if="activeTab === 'help'">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-5">{{ $t('settings.help.title') }}</h2>

          <!-- 태그 변수 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mb-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">{{ $t('settings.help.tagVars.title') }}</h3>
            <p class="text-xs text-gray-500 mb-3">{{ $t('settings.help.tagVars.desc') }}</p>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-gray-400 border-b border-gray-100 dark:border-gray-800">
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.tagVars.varCol') }}</th>
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.tagVars.fieldCol') }}</th>
                    <th class="pb-2 font-medium">{{ $t('settings.help.tagVars.exampleCol') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-gray-800">
                  <tr v-for="row in tagVarRows" :key="row.variable" class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td class="py-1.5 pr-4 font-mono text-blue-600 dark:text-blue-400 whitespace-nowrap">{{ row.variable }}</td>
                    <td class="py-1.5 pr-4 text-gray-700 dark:text-gray-300">{{ row.field }}</td>
                    <td class="py-1.5 text-gray-500">{{ row.example }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- 지원 파일 포맷 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mb-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">{{ $t('settings.help.formats.title') }}</h3>
            <p class="text-xs text-gray-500 mb-3">{{ $t('settings.help.formats.desc') }}</p>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-gray-400 border-b border-gray-100 dark:border-gray-800">
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.formats.formatCol') }}</th>
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.formats.extCol') }}</th>
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.formats.tagCol') }}</th>
                    <th class="pb-2 font-medium">{{ $t('settings.help.formats.noteCol') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-gray-800">
                  <tr v-for="row in formatRows" :key="row.ext" class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td class="py-1.5 pr-4 font-semibold text-gray-900 dark:text-white">{{ row.format }}</td>
                    <td class="py-1.5 pr-4 font-mono text-green-600 dark:text-green-400">{{ row.ext }}</td>
                    <td class="py-1.5 pr-4 text-gray-600 dark:text-gray-300">{{ row.tag }}</td>
                    <td class="py-1.5 text-gray-500">{{ row.note }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- 지원 메타데이터 소스 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm mb-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">{{ $t('settings.help.metaSources.title') }}</h3>
            <p class="text-xs text-gray-500 mb-3">{{ $t('settings.help.metaSources.desc') }}</p>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-gray-400 border-b border-gray-100 dark:border-gray-800">
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.metaSources.nameCol') }}</th>
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.metaSources.typeCol') }}</th>
                    <th class="pb-2 pr-4 font-medium">{{ $t('settings.help.metaSources.regionCol') }}</th>
                    <th class="pb-2 font-medium">{{ $t('settings.help.metaSources.noteCol') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-gray-800">
                  <tr v-for="row in metaSourceRows" :key="row.name" class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td class="py-1.5 pr-4 font-medium text-gray-900 dark:text-white">{{ row.name }}</td>
                    <td class="py-1.5 pr-4 text-gray-600 dark:text-gray-300">{{ row.type }}</td>
                    <td class="py-1.5 pr-4 text-gray-500">{{ row.region }}</td>
                    <td class="py-1.5 text-gray-400">{{ row.note }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- 파일명 변경 사용법 -->
          <section class="bg-white dark:bg-gray-900 rounded-xl p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">{{ $t('settings.help.rename.title') }}</h3>

            <!-- 사용 절차 -->
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{{ $t('settings.help.rename.stepsTitle') }}</p>
            <ol class="space-y-1.5 mb-4">
              <li v-for="(step, i) in $tm('settings.help.rename.steps')" :key="i" class="flex gap-2.5 text-xs text-gray-700 dark:text-gray-300">
                <span class="shrink-0 w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center font-semibold text-[10px]">{{ i + 1 }}</span>
                <span>{{ step }}</span>
              </li>
            </ol>

            <!-- 패턴 예시 -->
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{{ $t('settings.help.rename.presetsTitle') }}</p>
            <div class="space-y-1.5 mb-4">
              <div v-for="p in renamePresets" :key="p.name" class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
                <span class="text-xs text-gray-500 w-32 shrink-0">{{ p.name }}</span>
                <code class="text-xs font-mono text-blue-600 dark:text-blue-400">{{ p.pattern }}</code>
              </div>
            </div>

            <!-- 주의 사항 -->
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{{ $t('settings.help.rename.notesTitle') }}</p>
            <ul class="space-y-1">
              <li v-for="(note, i) in $tm('settings.help.rename.notes')" :key="i" class="flex gap-2 text-xs text-gray-500">
                <span class="text-yellow-500 shrink-0">⚠</span>
                <span>{{ note }}</span>
              </li>
            </ul>
          </section>
        </template>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { configApi } from '../api/config.js'
import { backupApi } from '../api/backup.js'
import client from '../api/index.js'
import ConfigRow from '../components/ConfigRow.vue'
import { useThemeStore } from '../stores/theme.js'
import { useToastStore } from '../stores/toast.js'
import { useAppConfigStore } from '../stores/appConfig.js'

const { t, locale } = useI18n()
const themeStore = useThemeStore()
const toastStore = useToastStore()
const appConfigStore = useAppConfigStore()

const route = useRoute()
const activeTab = ref(route.query.tab || 'general')

const tabs = computed(() => [
  { key: 'general',     icon: '⚙️',  label: t('settings.general') },
  { key: 'metadata',    icon: '🏷',  label: t('settings.metadata.title') },
  { key: 'data',        icon: '💾',  label: t('settings.backup.title') },
  { key: 'logs',        icon: '📋',  label: t('settings.activityLog.title') },
  { key: 'system',      icon: '🖥',  label: t('settings.version.title') },
  { key: 'help',        icon: '📖',  label: t('settings.help.title') },
])

/* global __APP_VERSION__ */
const appVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.3.0'
const serverVersion = ref('')
const buildDate = ref('')

const form = reactive({
  site_name: 'eztag',
  browser_title: 'eztag',
  app_language: 'ko',
  spotify_client_id: '',
  spotify_client_secret: '',
  spotify_enabled: true,
  bugs_enabled: true,
  apple_music_enabled: false,
  apple_music_storefront: 'kr',
  apple_music_classical_enabled: false,
  apple_music_classical_storefront: 'us',
  melon_enabled: true,
  youtube_enabled: false,
  youtube_api_key: '',
  lrc_primary_source: 'bugs',
  lrc_fallback_source: 'lrclib',
})
const savingMeta = ref(false)
const lrcSourceSaving = ref(false)
const showSpotifyId     = ref(false)
const showSpotifySecret = ref(false)
const showYoutubeKey    = ref(false)

async function saveLrcSources() {
  lrcSourceSaving.value = true
  try {
    await configApi.update({
      lrc_primary_source: form.lrc_primary_source,
      lrc_fallback_source: form.lrc_fallback_source,
    })
    toastStore.success(t('settings.toast.saved'))
  } catch (e) {
    toastStore.error(t('settings.toast.saveFailed', { error: e.response?.data?.detail || e.message }))
  } finally {
    lrcSourceSaving.value = false
  }
}

const backups = ref([])
const backupRunning = ref(false)

function fmtDatetime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

async function onLanguageChange() {
  locale.value = form.app_language
  localStorage.setItem('eztag-lang', form.app_language)
  try {
    await configApi.update({ app_language: form.app_language })
  } catch (e) {
    console.warn('언어 설정 저장 실패:', e)
  }
}

// 사이드바 등 외부에서 locale이 변경되면 콤보박스에 반영
watch(locale, (val) => {
  form.app_language = val
})

async function saveGeneralConfig() {
  try {
    await configApi.update({ site_name: form.site_name || 'eztag', browser_title: form.browser_title || 'eztag' })
    appConfigStore.apply({
      site_name:    { value: form.site_name    || 'eztag' },
      browser_title: { value: form.browser_title || 'eztag' },
    })
    toastStore.success(t('settings.toast.saved'))
  } catch (e) {
    toastStore.error(t('settings.toast.saveFailed', { error: e.response?.data?.detail || e.message }))
  }
}

async function loadConfig() {
  try {
    const { data } = await configApi.get()
    const c = data.config
    form.site_name = c.site_name?.value ?? 'eztag'
    form.browser_title = c.browser_title?.value ?? 'eztag'
    form.app_language = c.app_language?.value ?? 'ko'
    locale.value = form.app_language
    localStorage.setItem('eztag-lang', form.app_language)
    form.spotify_client_id = c.spotify_client_id?.value ?? ''
    form.spotify_client_secret = c.spotify_client_secret?.value ?? ''
    form.spotify_enabled = c.spotify_enabled?.value === 'true'
    form.bugs_enabled = (c.bugs_enabled?.value ?? 'true') === 'true'
    form.apple_music_enabled = c.apple_music_enabled?.value === 'true'
    form.apple_music_storefront = c.apple_music_storefront?.value ?? 'kr'
    form.apple_music_classical_enabled = c.apple_music_classical_enabled?.value === 'true'
    form.apple_music_classical_storefront = c.apple_music_classical_storefront?.value ?? 'us'
    form.melon_enabled = (c.melon_enabled?.value ?? 'true') === 'true'
    form.youtube_enabled = c.youtube_enabled?.value === 'true'
    form.youtube_api_key = c.youtube_api_key?.value ?? ''
    form.lrc_primary_source = c.lrc_primary_source?.value ?? 'bugs'
    form.lrc_fallback_source = c.lrc_fallback_source?.value ?? 'lrclib'
  } catch (e) {
    console.error('Config load failed', e)
  }
}

async function saveMetaConfig() {
  savingMeta.value = true
  try {
    await configApi.update({
      spotify_client_id: form.spotify_client_id,
      spotify_client_secret: form.spotify_client_secret,
      spotify_enabled: String(form.spotify_enabled),
      bugs_enabled: String(form.bugs_enabled),
      apple_music_enabled: String(form.apple_music_enabled),
      apple_music_storefront: form.apple_music_storefront,
      apple_music_classical_enabled: String(form.apple_music_classical_enabled),
      apple_music_classical_storefront: form.apple_music_classical_storefront,
      melon_enabled: String(form.melon_enabled),
      youtube_enabled: String(form.youtube_enabled),
      youtube_api_key: form.youtube_api_key,
    })
    toastStore.success(t('settings.toast.metaSaved'))
  } catch (e) {
    toastStore.error(t('settings.toast.saveFailed', { error: e.response?.data?.detail || e.message }))
  } finally {
    savingMeta.value = false
  }
}

async function loadBackups() {
  try {
    const { data } = await backupApi.list()
    backups.value = data.backups
  } catch (e) {
    console.error('Backup list failed', e)
  }
}

async function createBackup() {
  backupRunning.value = true
  try {
    const { data } = await backupApi.create()
    toastStore.success(t('settings.toast.backupComplete', { filename: data.filename }))
    await loadBackups()
  } catch (e) {
    toastStore.error(t('settings.toast.backupFailed', { error: e.response?.data?.detail || e.message }))
  } finally {
    backupRunning.value = false
  }
}

function downloadBackup(filename) { backupApi.download(filename) }

async function restoreBackup(filename) {
  if (!await toastStore.confirm(t('settings.confirm.restoreBackup', { filename }), '복원 확인')) return
  try {
    await backupApi.restore(filename)
    toastStore.success(t('settings.toast.restoreComplete'))
  } catch (e) {
    toastStore.error(t('settings.toast.restoreFailed', { error: e.response?.data?.detail || e.message }))
  }
}

async function deleteBackup(filename) {
  if (!await toastStore.confirm(t('settings.confirm.deleteBackup', { filename }), '삭제 확인')) return
  await backupApi.delete(filename)
  toastStore.success(t('settings.toast.backupDeleted'))
  await loadBackups()
}

// 도움말 탭 데이터 (locale 반응형)
const isKo = computed(() => locale.value === 'ko')

const tagVarRows = computed(() => [
  { variable: '%title%',       field: t('common.title'),       example: 'Shape of You' },
  { variable: '%artist%',      field: t('common.artist'),      example: 'Ed Sheeran' },
  { variable: '%albumartist%', field: t('common.albumArtist'), example: 'Ed Sheeran' },
  { variable: '%album%',       field: t('common.album'),       example: 'Divide' },
  { variable: '%track%',       field: isKo.value ? '트랙 번호' : 'Track No.',    example: '03' },
  { variable: '%totaltracks%', field: isKo.value ? '총 트랙 수' : 'Total Tracks', example: '16' },
  { variable: '%disc%',        field: isKo.value ? '디스크 번호' : 'Disc No.',   example: '1' },
  { variable: '%year%',        field: t('common.year'),        example: '2017' },
  { variable: '%genre%',       field: t('common.genre'),       example: 'Pop' },
  { variable: '%publisher%',   field: isKo.value ? '레이블' : 'Label',           example: 'Atlantic Records' },
  { variable: '%_filename%',   field: isKo.value ? '현재 파일명 (확장자 제외)' : 'Current filename (no ext)', example: '01 Shape of You' },
  { variable: '%_ext%',        field: isKo.value ? '확장자' : 'Extension',       example: 'mp3' },
  { variable: '%_bitrate%',    field: isKo.value ? '비트레이트 (kbps)' : 'Bitrate (kbps)', example: '320' },
  { variable: '%_codec%',      field: isKo.value ? '코덱' : 'Codec',             example: 'MP3' },
])

const formatRows = computed(() => [
  { format: 'MP3',  ext: '.mp3',  tag: 'ID3v2.3',        note: isKo.value ? '가장 널리 사용되는 포맷' : 'Most widely used format' },
  { format: 'FLAC', ext: '.flac', tag: 'Vorbis Comment', note: isKo.value ? '무손실 압축' : 'Lossless compression' },
  { format: 'M4A',  ext: '.m4a',  tag: 'iTunes Atoms',   note: isKo.value ? 'AAC 기반, Apple 포맷' : 'AAC-based, Apple format' },
  { format: 'AAC',  ext: '.aac',  tag: 'ID3v2 / Atoms',  note: isKo.value ? 'AAC 오디오' : 'AAC audio' },
  { format: 'OGG',  ext: '.ogg',  tag: 'Vorbis Comment', note: isKo.value ? 'Ogg Vorbis 포맷' : 'Ogg Vorbis format' },
  { format: 'WAV',  ext: '.wav',  tag: 'ID3v2',          note: isKo.value ? '비압축 포맷' : 'Uncompressed format' },
  { format: 'WMA',  ext: '.wma',  tag: 'ASF',            note: 'Windows Media Audio' },
])

const metaSourceRows = computed(() => [
  { name: 'Spotify',               type: isKo.value ? '태그 + 커버' : 'Tags + Cover', region: isKo.value ? '글로벌' : 'Global', note: isKo.value ? 'Client ID/Secret 설정 필요' : 'Requires Client ID/Secret' },
  { name: 'Bugs',                  type: isKo.value ? '태그 + 커버' : 'Tags + Cover', region: isKo.value ? '한국' : 'Korea',  note: isKo.value ? '기본 활성화' : 'Enabled by default' },
  { name: 'Melon',                 type: isKo.value ? '태그 + 커버' : 'Tags + Cover', region: isKo.value ? '한국' : 'Korea',  note: isKo.value ? '기본 활성화' : 'Enabled by default' },
  { name: 'Apple Music',           type: isKo.value ? '태그 + 커버' : 'Tags + Cover', region: isKo.value ? '글로벌' : 'Global', note: isKo.value ? '국가 스토어 선택 가능' : 'Storefront selectable' },
  { name: 'Apple Music Classical', type: isKo.value ? '태그 + 커버' : 'Tags + Cover', region: isKo.value ? '글로벌' : 'Global', note: isKo.value ? '클래식 음악 전용' : 'Classical music only' },
  { name: 'LRCLIB',                type: isKo.value ? 'LRC 가사' : 'LRC Lyrics',    region: isKo.value ? '글로벌' : 'Global', note: isKo.value ? '싱크 가사 지원' : 'Synced lyrics' },
  { name: 'Bugs LRC',              type: isKo.value ? 'LRC 가사' : 'LRC Lyrics',    region: isKo.value ? '한국' : 'Korea',  note: isKo.value ? '벅스 싱크 가사' : 'Bugs synced lyrics' },
])

const renamePresets = computed(() => [
  { name: isKo.value ? '트랙 - 제목' : 'Track - Title',                    pattern: '%track% - %title%' },
  { name: isKo.value ? '아티스트 - 제목' : 'Artist - Title',                pattern: '%artist% - %title%' },
  { name: isKo.value ? '트랙 - 아티스트 - 제목' : 'Track - Artist - Title', pattern: '%track% - %artist% - %title%' },
  { name: isKo.value ? '디스크-트랙 - 제목' : 'Disc-Track - Title',         pattern: '%disc%-%track% - %title%' },
])

async function loadServerVersion() {
  try {
    const { data } = await client.get('/health')
    serverVersion.value = data.version
    buildDate.value = data.build_date
  } catch {}
}

// ── 로그 탭 ──────────────────────────────────────────────
const logItems = ref([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = 50
const logsLoading = ref(false)
const clearingLogs = ref(false)
const logFilter = reactive({ type: '', search: '' })

const LOG_TYPE_ICONS = {
  tag_write: '🏷',
  rename: '✏️',
  lrc_search: '🎵',
  login: '🔑',
  error: '⚠️',
}
const LOG_TYPE_BADGE = {
  tag_write:  'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
  rename:     'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
  lrc_search: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
  login:      'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
  error:      'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
}

function logTypeIcon(type) { return LOG_TYPE_ICONS[type] || '📄' }
function logTypeBadgeClass(type) { return LOG_TYPE_BADGE[type] || 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400' }

function parseDetail(detail) {
  if (!detail) return {}
  const result = {}
  for (const part of detail.split(', ')) {
    const idx = part.indexOf('=')
    if (idx > 0) result[part.slice(0, idx)] = part.slice(idx + 1)
  }
  return result
}

function translateLog(item) {
  const action = item.action
  if (!action) return item.message
  const d = parseDetail(item.detail)
  const fname = item.file_path ? item.file_path.split('/').pop() : ''
  if (action === 'login_failed')
    return t('settings.activityLog.action.login_failed', { username: item.username || '' })
  if (action === 'login_success')
    return t('settings.activityLog.action.login_success', { username: item.username || '' })
  if (action.startsWith('fetch_lyrics_')) {
    const source = action.slice('fetch_lyrics_'.length)
    const fallback = d.fallback && d.fallback !== 'none' ? `→${d.fallback}` : ''
    return t('settings.activityLog.action.fetch_lyrics', { source: source + fallback, saved: d.saved || '0', notfound: d.not_found || '0', error: d.error || '0' })
  }
  if (action.startsWith('library_fetch_lyrics_')) {
    const source = action.slice('library_fetch_lyrics_'.length)
    return t('settings.activityLog.action.library_fetch_lyrics', { source, saved: d.saved || '0', notfound: d.not_found || '0', error: d.error || '0' })
  }
  if (action === 'rename_by_tags')
    return t('settings.activityLog.action.rename_by_tags', { success: d.success || '0', failed: d.failed || '0', pattern: d.pattern || '' })
  if (action === 'update_track') {
    const m = item.message.match(/\[(.+)\]$/)
    return t('settings.activityLog.action.update_track', { filename: fname, fields: m ? m[1] : '' })
  }
  if (action === 'write_tags') {
    const m = item.message.match(/\[(.+)\]$/)
    return t('settings.activityLog.action.write_tags', { filename: fname, fields: m ? m[1] : '' })
  }
  if (action === 'batch_write_tags') {
    const m = item.message.match(/\[(.+)\]$/)
    return t('settings.activityLog.action.batch_write_tags', { n: d.written || d.total || '0', fields: m ? m[1] : '' })
  }
  if (action === 'rename') {
    const m = item.message.match(/:\s*(.+?)\s*→\s*(.+)$/)
    if (m) return t('settings.activityLog.action.rename', { oldname: m[1].trim(), newname: m[2].trim() })
  }
  return item.message
}

async function loadLogs(page = 1) {
  logsLoading.value = true
  logPage.value = page
  try {
    const params = { page, page_size: logPageSize }
    if (logFilter.type) params.log_type = logFilter.type
    if (logFilter.search) params.search = logFilter.search
    const { data } = await client.get('/logs/activity', { params })
    logItems.value = data.items
    logTotal.value = data.total
  } catch (e) {
    console.error('Failed to load logs', e)
  } finally {
    logsLoading.value = false
  }
}

async function clearLogs() {
  if (!await toastStore.confirm(t('settings.logs.confirmClear'), t('settings.logs.clearAll'))) return
  clearingLogs.value = true
  try {
    const params = {}
    if (logFilter.type) params.log_type = logFilter.type
    await client.delete('/logs/activity', { params })
    toastStore.success(t('settings.logs.cleared'))
    await loadLogs(1)
  } catch (e) {
    toastStore.error(e.response?.data?.detail || e.message)
  } finally {
    clearingLogs.value = false
  }
}

watch(() => activeTab.value, (tab) => {
  if (tab === 'logs') loadLogs(1)
})

// 사이드바 등 외부에서 query.tab이 바뀌면 탭 전환
watch(() => route.query.tab, (tab) => {
  if (tab) activeTab.value = tab
})

onMounted(async () => {
  await Promise.all([loadConfig(), loadBackups(), loadServerVersion()])
})
</script>
