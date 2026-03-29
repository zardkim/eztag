<template>
  <!-- 초기화 전: 빈 화면으로 깜빡임 방지 -->
  <div v-if="!authStore.initialized" class="min-h-screen bg-gray-50 dark:bg-gray-950" />

  <!-- Public pages: setup / login -->
  <div v-else-if="isPublicRoute" class="min-h-screen bg-gray-50 dark:bg-gray-950">
    <RouterView />
  </div>

  <!-- Authenticated layout -->
  <div v-else-if="authStore.isLoggedIn" class="h-screen flex overflow-hidden bg-gray-50 dark:bg-gray-950">

    <!-- ══════════════════════════════════════════════
         MOBILE: 상단 바 (로고 + 툴바 슬롯)
    ══════════════════════════════════════════════ -->
    <header class="lg:hidden fixed top-0 inset-x-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex flex-col" style="padding-top: env(safe-area-inset-top, 0px);">
      <!-- 1행: 로고 + 테마 -->
      <div class="flex items-center justify-between px-4 h-11 shrink-0">
        <img
          :src="themeStore.theme === 'dark' ? '/logo-dark.svg' : '/logo.svg'"
          alt="eztag"
          class="h-7 w-auto"
        />
        <button
          class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
          @click="themeStore.toggle()"
        >
          <span>{{ themeStore.theme === 'dark' ? '☀️' : '🌙' }}</span>
        </button>
      </div>
      <!-- 2행: 툴바 슬롯 (Browser.vue 버튼 삽입 대상) -->
      <div
        v-show="route.path === '/browser'"
        id="app-toolbar-slot-mobile"
        class="shrink-0 h-11 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 flex items-center min-w-0 overflow-x-auto overflow-y-hidden scrollbar-none"
      >
        <!-- Browser.vue가 Teleport로 이 슬롯에 버튼을 주입 -->
      </div>
    </header>


    <!-- ══════════════════════════════════════════════
         MOBILE: 계정 바텀 시트
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        leave-active-class="transition duration-150 ease-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div v-if="mobileUserOpen" class="lg:hidden fixed inset-0 z-50 flex flex-col justify-end">
          <div class="absolute inset-0 bg-black/40" @click="mobileUserOpen = false" />
          <Transition
            enter-active-class="transition duration-200 ease-out"
            leave-active-class="transition duration-150 ease-in"
            enter-from-class="translate-y-full"
            leave-to-class="translate-y-full"
          >
            <div v-if="mobileUserOpen" class="relative bg-white dark:bg-gray-900 rounded-t-2xl shadow-2xl">
              <!-- 유저 정보 -->
              <div class="flex items-center gap-3 px-5 py-4 border-b border-gray-100 dark:border-gray-800">
                <span class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold shrink-0">
                  {{ (authStore.user?.username || '?')[0].toUpperCase() }}
                </span>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ authStore.user?.username }}</p>
                  <p class="text-xs text-gray-400">{{ authStore.user?.role }}</p>
                </div>
              </div>
              <!-- 메뉴 -->
              <div class="px-3 py-2 space-y-0.5">
                <button class="w-full flex items-center gap-3 px-3 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl transition-colors text-left" @click="toggleLanguage">
                  <span class="text-lg">🌐</span>
                  <span>{{ locale === 'ko' ? '한국어' : 'English' }}</span>
                </button>
                <button class="w-full flex items-center gap-3 px-3 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl transition-colors text-left"
                        @click="mobileUserOpen = false; openPasswordModal()">
                  <span class="text-lg">🔑</span>
                  <span>{{ $t('password.title') }}</span>
                </button>
                <button class="w-full flex items-center gap-3 px-3 py-3 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors text-left" @click="logout">
                  <span class="text-lg">🚪</span>
                  <span>{{ $t('auth.logout') }}</span>
                </button>
              </div>
              <div class="h-safe-bottom pb-4"></div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- ══════════════════════════════════════════════
         MOBILE: 폴더/파일 열기 모달
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <LibraryPickerModal
        v-if="mobileShowWorkspacePicker"
        :folder-mode="true"
        area="workspace"
        @close="mobileShowWorkspacePicker = false"
        @select-folder="onMobileSelectWorkspaceFolder"
        @select-folder-recursive="f => { mobileShowWorkspacePicker = false; browserStore.selectFolderRecursive({ name: f.name, path: f.path }, [{ name: f.name, path: f.path }], 'workspace'); router.push('/browser') }"
      />
      <LibraryPickerModal
        v-if="mobileShowLibraryPicker"
        :folder-mode="true"
        area="library"
        @close="mobileShowLibraryPicker = false"
        @select-folder="onMobileSelectLibraryFolder"
        @select-folder-recursive="f => { mobileShowLibraryPicker = false; browserStore.selectFolderRecursive({ name: f.name, path: f.path }, [{ name: f.name, path: f.path }], 'library'); router.push('/browser') }"
      />
    </Teleport>

    <!-- ══════════════════════════════════════════════
         DESKTOP: 사이드바 (lg 이상만)
    ══════════════════════════════════════════════ -->
    <aside
      class="hidden lg:flex fixed inset-y-0 left-0 z-50 w-60 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex-col
             transition-all duration-300 ease-in-out
             lg:relative lg:translate-x-0 lg:z-auto lg:shrink-0"
      :class="sidebarCollapsed ? 'lg:w-14' : 'lg:w-60'"
    >
      <!-- Logo + 폴딩 버튼 -->
      <div class="px-3 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between shrink-0 min-w-0">
        <div v-if="!sidebarCollapsed" class="flex items-center justify-between w-full min-w-0">
          <div class="min-w-0">
            <img
              :src="themeStore.theme === 'dark' ? '/logo-dark.svg' : '/logo.svg'"
              alt="eztag"
              class="h-10 w-auto"
            />
            <p class="text-[10px] text-gray-700 dark:text-gray-400 font-mono mt-0.5">
              <span v-if="appConfigStore.siteName !== 'eztag'" class="mr-1 text-gray-500 dark:text-gray-300 font-sans not-italic font-medium">{{ appConfigStore.siteName }}</span>v{{ appVersion }}
            </p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              class="flex items-center justify-center w-7 h-7 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
              @click="themeStore.toggle()"
            >
              <span class="text-sm">{{ themeStore.theme === 'dark' ? '☀️' : '🌙' }}</span>
            </button>
            <button
              class="flex items-center justify-center w-7 h-7 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
              title="사이드바 접기"
              @click="toggleSidebar"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>

        <div v-else class="flex flex-col items-center w-full gap-2">
          <img src="/logo-icon.svg" alt="eztag" class="w-8 h-8" />
          <button
            class="flex items-center justify-center w-7 h-7 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
            title="사이드바 펼치기"
            @click="toggleSidebar"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Workspace Sidebar -->
      <div class="flex-1 overflow-hidden flex flex-col min-h-0" :class="sidebarCollapsed ? 'hidden' : ''">
        <WorkspaceSidebar ref="workspaceSidebarRef" />
      </div>

      <!-- Bottom nav (데스크톱 사이드바 하단) -->
      <nav class="shrink-0 px-2 py-2 border-t border-gray-200 dark:border-gray-800 space-y-0.5">
        <button
          v-if="sidebarCollapsed"
          class="w-full flex items-center justify-center px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          title="폴더 열기"
          @click="workspaceSidebarRef?.openFolderPicker()"
        ><span class="text-base">📂</span></button>
        <RouterLink
          v-for="item in bottomNav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          :class="sidebarCollapsed ? 'justify-center' : ''"
          :title="sidebarCollapsed ? $t(item.labelKey) : ''"
          active-class="bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white"
        >
          <span class="text-base shrink-0">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed">{{ $t(item.labelKey) }}</span>
        </RouterLink>

        <button
          class="w-full flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
          :class="sidebarCollapsed ? 'justify-center' : ''"
          :title="sidebarCollapsed ? (locale === 'ko' ? '한국어' : 'English') : ''"
          @click="toggleLanguage"
        >
          <span class="text-base shrink-0">🌐</span>
          <span v-if="!sidebarCollapsed" class="flex-1 text-left">{{ locale === 'ko' ? '한국어' : 'English' }}</span>
        </button>

        <!-- 유저 메뉴 (데스크톱) -->
        <div class="relative" ref="userMenuRef">
          <button
            class="w-full flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
            :class="sidebarCollapsed ? 'justify-center' : ''"
            :title="sidebarCollapsed ? (authStore.user?.username || '') : ''"
            @click="userMenuOpen = !userMenuOpen"
          >
            <span class="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
              {{ (authStore.user?.username || '?')[0].toUpperCase() }}
            </span>
            <span v-if="!sidebarCollapsed" class="flex-1 text-left truncate">{{ authStore.user?.username }}</span>
            <span v-if="!sidebarCollapsed" class="text-gray-300 dark:text-gray-600 text-[10px]">▾</span>
          </button>
          <Transition
            enter-from-class="opacity-0 translate-y-1"
            leave-to-class="opacity-0 translate-y-1"
            enter-active-class="transition duration-100"
            leave-active-class="transition duration-100"
          >
            <div
              v-if="userMenuOpen"
              class="absolute bottom-full left-0 right-0 mb-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 py-1 overflow-hidden"
              :class="sidebarCollapsed ? 'w-36 left-full ml-2 bottom-0' : ''"
            >
              <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
                <p class="text-xs font-semibold text-gray-900 dark:text-white truncate">{{ authStore.user?.username }}</p>
                <p class="text-[10px] text-gray-400">{{ authStore.user?.role }}</p>
              </div>
              <button
                class="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                @click="openPasswordModal"
              >🔑 {{ $t('password.title') }}</button>
              <button
                class="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left"
                @click="logout"
              >🚪 {{ $t('auth.logout') }}</button>
            </div>
          </Transition>
        </div>
      </nav>
    </aside>

    <!-- ══════════════════════════════════════════════
         메인 콘텐츠
    ══════════════════════════════════════════════ -->
    <main
      class="flex-1 overflow-hidden flex flex-col min-w-0 lg:!pt-0 lg:!pb-0"
      :style="route.path === '/browser'
        ? 'padding-top: calc(5.5rem + env(safe-area-inset-top, 0px)); padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px));'
        : 'padding-top: calc(2.75rem + env(safe-area-inset-top, 0px)); padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px));'"
    >
      <!-- 데스크톱 툴바 슬롯 -->
      <div id="app-toolbar-slot" class="shrink-0 h-10 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center min-w-0 hidden lg:flex">
        <template v-if="route.path !== '/browser'">
          <RouterLink
            to="/browser"
            class="flex items-center gap-1.5 px-3 py-1.5 ml-1 rounded-lg text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-800 transition-colors"
            active-class="bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white"
          >
            <span>📁</span>
            <span>{{ $t('nav.browser') }}</span>
          </RouterLink>
        </template>
      </div>
      <RouterView />
    </main>

    <!-- ══════════════════════════════════════════════
         MOBILE: 하단 내비게이션 바
    ══════════════════════════════════════════════ -->
    <nav class="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex" style="height: calc(4rem + env(safe-area-inset-bottom, 0px)); padding-bottom: env(safe-area-inset-bottom, 0px);">

      <!-- ① 홈 (파란색) -->
      <RouterLink
        to="/home"
        class="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors"
        :class="route.path === '/home' && !mobileUserOpen
          ? 'text-blue-500 dark:text-blue-400'
          : 'text-gray-400 dark:text-gray-500'"
        @click="mobileUserOpen = false"
      >
        <div class="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/home' && !mobileUserOpen
            ? 'bg-blue-50 dark:bg-blue-900/30'
            : ''">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
        </div>
        <span class="text-[10px] font-medium">{{ $t('nav.home') }}</span>
      </RouterLink>

      <!-- ② + 폴더 열기 (초록색) -->
      <div class="flex-1 flex flex-col items-center justify-center relative">
        <button
          class="flex flex-col items-center justify-center gap-0.5 transition-colors"
          :class="mobileFolderMenuOpen ? 'text-emerald-500 dark:text-emerald-400' : 'text-gray-400 dark:text-gray-500'"
          @click.stop="mobileUserOpen = false; mobileFolderMenuOpen = !mobileFolderMenuOpen"
        >
          <div class="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
            :class="mobileFolderMenuOpen ? 'bg-emerald-500 text-white' : 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-500 dark:text-emerald-400'"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
            </svg>
          </div>
          <span class="text-[10px] font-medium">열기</span>
        </button>
        <!-- 팝업 메뉴 -->
        <Transition enter-from-class="opacity-0 scale-95" leave-to-class="opacity-0 scale-95" enter-active-class="transition duration-150 origin-bottom" leave-active-class="transition duration-100 origin-bottom">
          <div
            v-if="mobileFolderMenuOpen"
            class="absolute bottom-12 left-1/2 -translate-x-1/2 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden w-44 z-50"
            @click.stop
          >
            <button
              class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors text-left"
              @click="mobileFolderMenuOpen = false; mobileShowWorkspacePicker = true"
            ><span class="text-base">📂</span>{{ $t('sidebar.openWorkspace') }}</button>
            <div class="h-px bg-gray-100 dark:bg-gray-700"></div>
            <button
              class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left"
              @click="mobileFolderMenuOpen = false; mobileShowLibraryPicker = true"
            ><span class="text-base">📚</span>{{ $t('sidebar.openLibrary') }}</button>
          </div>
        </Transition>
      </div>

      <!-- ③ 태깅 (보라색) -->
      <button
        class="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors"
        :class="route.path === '/browser' && browserStore.mobileMenuOpen
          ? 'text-violet-500 dark:text-violet-400'
          : (route.path === '/browser' && browserStore.files.length > 0)
            ? 'text-violet-400 dark:text-violet-500'
            : 'text-gray-400 dark:text-gray-500'"
        @click="mobileUserOpen = false; route.path === '/browser' ? browserStore.mobileMenuOpen = !browserStore.mobileMenuOpen : router.push('/browser')"
      >
        <div class="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/browser' && browserStore.mobileMenuOpen
            ? 'bg-violet-500 text-white'
            : 'bg-violet-50 dark:bg-violet-900/30 text-violet-500 dark:text-violet-400'"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/>
          </svg>
        </div>
        <span class="text-[10px] font-medium">{{ $t('nav.more') }}</span>
      </button>

      <!-- ④ 설정 (주황색) -->
      <button
        class="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors"
        :class="route.path === '/settings' && !mobileUserOpen
          ? 'text-orange-500 dark:text-orange-400'
          : 'text-gray-400 dark:text-gray-500'"
        @click="router.push('/settings'); mobileUserOpen = false"
      >
        <div class="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/settings' && !mobileUserOpen
            ? 'bg-orange-50 dark:bg-orange-900/30'
            : ''">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </div>
        <span class="text-[10px] font-medium">{{ $t('nav.settings') }}</span>
      </button>

      <!-- ⑤ 아이디 (분홍색) -->
      <button
        class="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors"
        :class="mobileUserOpen ? 'text-rose-500 dark:text-rose-400' : 'text-gray-400 dark:text-gray-500'"
        @click="mobileUserOpen = !mobileUserOpen"
      >
        <span
          class="w-8 h-8 rounded-xl text-white flex items-center justify-center text-xs font-bold transition-colors"
          :class="mobileUserOpen ? 'bg-rose-500' : 'bg-rose-400 dark:bg-rose-500'"
        >
          {{ (authStore.user?.username || '?')[0].toUpperCase() }}
        </span>
        <span class="text-[10px] font-medium truncate max-w-[52px]">{{ authStore.user?.username }}</span>
      </button>
    </nav>

    <!-- ── 전역 토스트 ── -->
    <ToastContainer />
    <!-- ── 백그라운드 작업 인디케이터 ── -->
    <JobIndicator />

    <!-- ── 비밀번호 변경 모달 ── -->
    <Transition enter-from-class="opacity-0" leave-to-class="opacity-0" enter-active-class="transition duration-150" leave-active-class="transition duration-150">
      <div v-if="showPasswordModal" class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4" @click.self="showPasswordModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl p-6">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">🔑 {{ $t('password.title') }}</h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-gray-500 block mb-1">{{ $t('password.currentLabel') }}</label>
              <input v-model="passwordForm.current" type="password" class="field w-full" :placeholder="$t('password.currentPlaceholder')" @keyup.enter="changePassword" />
            </div>
            <div>
              <label class="text-xs text-gray-500 block mb-1">{{ $t('password.newLabel') }}</label>
              <input v-model="passwordForm.next" type="password" class="field w-full" :placeholder="$t('password.newPlaceholder')" @keyup.enter="changePassword" />
            </div>
            <div>
              <label class="text-xs text-gray-500 block mb-1">{{ $t('password.confirmLabel') }}</label>
              <input v-model="passwordForm.confirm" type="password" class="field w-full" :placeholder="$t('password.confirmPlaceholder')" @keyup.enter="changePassword" />
            </div>
            <p v-if="passwordError" class="text-xs text-red-500">{{ passwordError }}</p>
          </div>
          <div class="flex justify-end gap-2 mt-5">
            <button class="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors" @click="showPasswordModal = false">{{ $t('common.cancel') }}</button>
            <button
              class="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors disabled:opacity-60"
              :disabled="passwordSaving"
              @click="changePassword"
            >{{ passwordSaving ? $t('password.saving') : $t('password.save') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useThemeStore } from './stores/theme.js'
import { useAuthStore } from './stores/auth.js'
import { useBrowserStore } from './stores/browser.js'
import { useAppConfigStore } from './stores/appConfig.js'
import { authApi, workspaceApi } from './api/index.js'
import { configApi } from './api/config.js'
import WorkspaceSidebar from './components/WorkspaceSidebar.vue'
import ToastContainer from './components/ToastContainer.vue'
import LibraryPickerModal from './components/LibraryPickerModal.vue'
import JobIndicator from './components/JobIndicator.vue'

/* global __APP_VERSION__ */
const appVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.3.0'
const appConfigStore = useAppConfigStore()

const { locale, t } = useI18n()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const browserStore = useBrowserStore()
const route = useRoute()
const router = useRouter()
const sidebarCollapsed = ref(localStorage.getItem('eztag-sidebar-collapsed') === 'true')
const workspaceSidebarRef = ref(null)

// 모바일 시트 상태
const mobileUserOpen = ref(false)
const mobileShowFolderPicker = ref(false)
const mobileFolderMenuOpen = ref(false)
const mobileShowWorkspacePicker = ref(false)
const mobileShowLibraryPicker = ref(false)

function onMobileSelectFolder(folder) {
  mobileShowFolderPicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }])
  router.push('/browser')
}

function onMobileSelectWorkspaceFolder(folder) {
  mobileShowWorkspacePicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'workspace')
  router.push('/browser')
}

function onMobileSelectLibraryFolder(folder) {
  mobileShowLibraryPicker.value = false
  browserStore.selectFolder({ name: folder.name, path: folder.path }, [{ name: folder.name, path: folder.path }], 'library')
  router.push('/browser')
}

function closeMobileFolderMenu() {
  mobileFolderMenuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', closeMobileFolderMenu)
})
onUnmounted(() => {
  document.removeEventListener('click', closeMobileFolderMenu)
})

// 최근 폴더 저장
const RECENT_FOLDERS_KEY = 'eztag-recent-folders'
const LAST_FOLDER_KEY = 'eztag-last-folder'

function saveRecentFolder(folder, area) {
  try {
    const list = JSON.parse(localStorage.getItem(RECENT_FOLDERS_KEY) || '[]')
    const filtered = list.filter(f => f.path !== folder.path)
    const updated = [{ name: folder.name, path: folder.path, area: area || null, timestamp: Date.now() }, ...filtered].slice(0, 15)
    localStorage.setItem(RECENT_FOLDERS_KEY, JSON.stringify(updated))
    // 서버에도 저장 (기기 간 동기화)
    configApi.update({ recent_folders: JSON.stringify(updated) }).catch(() => {})
  } catch { /* ignore */ }
}

// 폴더 선택 시 최근 목록 + 마지막 열기 폴더 저장
watch(() => browserStore.selectedFolder, (folder) => {
  if (folder) {
    saveRecentFolder(folder, browserStore.currentArea)
    // 마지막 열기 폴더 저장 (새로고침 후 복원용)
    try {
      localStorage.setItem(LAST_FOLDER_KEY, JSON.stringify({
        folder: { name: folder.name, path: folder.path },
        breadcrumb: browserStore.breadcrumb,
        area: browserStore.currentArea,
      }))
    } catch { /* ignore */ }
  }
})

// 라우트 변경 시 시트 닫기
watch(() => route.path, () => {
  mobileUserOpen.value = false
  browserStore.mobileMenuOpen = false
})

// ── 언어 변경 ──────────────────────────────────────
async function toggleLanguage() {
  const next = locale.value === 'ko' ? 'en' : 'ko'
  locale.value = next
  localStorage.setItem('eztag-lang', next)
  try {
    await configApi.update({ app_language: next })
  } catch (e) {
    console.warn('언어 설정 저장 실패:', e)
  }
}

// ── 유저 메뉴 (데스크톱) ────────────────────────────
const userMenuOpen = ref(false)
const userMenuRef  = ref(null)

function onClickOutside(e) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    userMenuOpen.value = false
  }
}

// ── 비밀번호 변경 ───────────────────────────────────
const showPasswordModal = ref(false)
const passwordSaving    = ref(false)
const passwordError     = ref('')
const passwordForm      = reactive({ current: '', next: '', confirm: '' })

function openPasswordModal() {
  userMenuOpen.value = false
  passwordForm.current = ''
  passwordForm.next    = ''
  passwordForm.confirm = ''
  passwordError.value  = ''
  showPasswordModal.value = true
}

function validatePassword(pwd) {
  if (pwd.length < 8) return t('password.errTooShort')
  if (!/[!@#$%^&*()\-_=+[\]{}|;:'",.<>?/\\`~]/.test(pwd)) return t('password.errNoSpecial')
  return null
}

async function changePassword() {
  passwordError.value = ''
  if (!passwordForm.current || !passwordForm.next || !passwordForm.confirm) {
    passwordError.value = t('password.errRequired')
    return
  }
  const pwErr = validatePassword(passwordForm.next)
  if (pwErr) { passwordError.value = pwErr; return }
  if (passwordForm.next !== passwordForm.confirm) {
    passwordError.value = t('password.errMismatch')
    return
  }
  passwordSaving.value = true
  try {
    await authApi.changePassword({ current_password: passwordForm.current, new_password: passwordForm.next })
    showPasswordModal.value = false
  } catch (e) {
    passwordError.value = e.response?.data?.detail || t('password.errFailed')
  } finally {
    passwordSaving.value = false
  }
}

// ───────────────────────────────────────────────────
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('eztag-sidebar-collapsed', String(sidebarCollapsed.value))
}

async function loadAppConfig() {
  try {
    const { data } = await configApi.get()
    appConfigStore.apply(data.config)
    document.title = document.title.replace(/ - .+$/, ` - ${appConfigStore.browserTitle}`)
    // 시작 폴더 자동 열기 (폴더가 아직 선택되지 않은 경우만)
    if (!browserStore.selectedFolder) {
      const startupFolder = data.config.startup_folder?.value || 'none'
      if (startupFolder === 'workspace') {
        try {
          const { data: ws } = await workspaceApi.workspaceRoots()
          if (ws.configured && ws.roots?.length > 0) {
            const root = ws.roots[0]
            browserStore.selectFolder({ name: root.name, path: root.path }, [{ name: root.name, path: root.path }], 'workspace')
          }
        } catch { /* ignore */ }
      } else if (startupFolder === 'library') {
        try {
          const { data: lib } = await workspaceApi.libraryRoots()
          if (lib.roots?.length > 0) {
            const root = lib.roots[0]
            browserStore.selectFolder({ name: root.name, path: root.path }, [{ name: root.name, path: root.path }], 'library')
          }
        } catch { /* ignore */ }
      } else {
        // 시작 폴더 미설정 → 마지막으로 열었던 폴더 복원
        try {
          const saved = JSON.parse(localStorage.getItem(LAST_FOLDER_KEY) || 'null')
          if (saved?.folder?.path) {
            browserStore.selectFolder(saved.folder, saved.breadcrumb || [saved.folder], saved.area || null)
          }
        } catch { /* ignore */ }
      }
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  themeStore.apply()
  document.addEventListener('click', onClickOutside, true)
  if (authStore.isLoggedIn) {
    loadAppConfig()
  }
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
})

const isPublicRoute = computed(() => ['/setup', '/login'].includes(route.path))

const bottomNav = [
  { to: '/settings', icon: '⚙️', labelKey: 'nav.settings' },
]

function logout() {
  userMenuOpen.value  = false
  mobileUserOpen.value = false
  authStore.logout()
  router.replace('/login')
}
</script>
