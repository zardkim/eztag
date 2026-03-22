import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Bearer token 인터셉터
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('eztag-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 → 로그인 페이지 리다이렉트 (auth 엔드포인트 및 이미 로그인 페이지일 때 제외)
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const isAuthEndpoint = err.config?.url?.startsWith('/auth/')
    const isLoginPage = ['/login', '/setup'].includes(window.location.pathname)
    if (err.response?.status === 401 && !isAuthEndpoint && !isLoginPage) {
      localStorage.removeItem('eztag-token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client

// Metadata
export const metadataApi = {
  search: (params) => client.get('/metadata/search', { params }),
  albumTracks: (id, provider = 'spotify') =>
    client.get('/metadata/album-tracks', {
      params: provider === 'spotify'
        ? { spotify_album_id: id }
        : { provider_id: id, provider },
    }),
  applyByPath: (data) => client.post('/metadata/apply-by-path', data),
}

// Auth
export const authApi = {
  checkSetup: () => client.get('/auth/check-setup'),
  setup: (data) => client.post('/auth/setup', data),
  login: (data) => client.post('/auth/login', data),
  me: () => client.get('/auth/me'),
  changePassword: (data) => client.post('/auth/change-password', data),
}

// Browse
export const browseApi = {
  getRoots: (withChildren = false, force = false) => client.get('/browse/roots', { params: { with_children: withChildren, force } }),
  getChildren: (path, force = false) => client.get('/browse/children', { params: { path, force } }),
  getFiles: (path, force = false) => client.get('/browse/files', { params: { path, force } }),
  getCovers: (path) => client.get('/browse/covers', { params: { path } }),
  writeTags: (data) => client.post('/browse/write-tags', data),
  batchWriteTags: (data) => client.post('/browse/batch-write-tags', data),
  setTrackInfo: (data) => client.post('/browse/set-track-info', data),
  searchYoutubeMV: (artist, title) => client.get('/browse/search-youtube-mv', { params: { artist, title } }),
  rename: (data) => client.post('/browse/rename', data),
  uploadCover: (path, file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post(`/browse/cover-upload?path=${encodeURIComponent(path)}`, form)
  },
  uploadCoverWithType: (path, file, coverType = 3) => {
    const form = new FormData()
    form.append('file', file)
    return client.post(`/browse/cover-upload?path=${encodeURIComponent(path)}&cover_type=${coverType}`, form)
  },
  getFolderImages: (path) => client.get('/browse/folder-images', { params: { path } }),
  folderImageUrl: (path) => `/api/browse/folder-image?path=${encodeURIComponent(path)}`,
  coverFromFolder: (image_path, audio_paths) =>
    client.post('/browse/cover-from-folder', { image_path, audio_paths }),
  coverFromFolderWithType: (image_path, audio_paths, cover_type = 3) =>
    client.post('/browse/cover-from-folder', { image_path, audio_paths, cover_type }),
  removeCover: (paths) => client.post('/browse/cover-remove', { paths }),
  extractCovers: (path, overwrite = false) => client.post('/browse/extract-covers', { path, overwrite }),
  fetchLyrics: (paths, source = 'bugs') => client.post('/browse/fetch-lyrics', { paths, source }, { timeout: 60000 }),
  libraryAudioFiles: (folder, recursive = true) => client.get('/browse/library-audio-files', { params: { folder, recursive } }),
  libraryFetchLyrics: (paths, source = 'bugs') => client.post('/browse/library-fetch-lyrics', { paths, source }, { timeout: 60000 }),
  lrcSubfolders: () => client.get('/browse/lrc-subfolders'),
  streamUrl: (path) => `/api/browse/stream?path=${encodeURIComponent(path)}`,
  lrcContent: (path) => client.get('/browse/lrc-content', { params: { path } }),
  renameByTagsPreview: (paths, pattern) => client.post('/browse/rename-by-tags/preview', { paths, pattern }),
  renameByTags: (paths, pattern) => client.post('/browse/rename-by-tags', { paths, pattern }),
  destChildren: (path) => client.get('/browse/dest-children', { params: { path } }),
  destMkdir: (data) => client.post('/browse/dest-mkdir', data),
  moveFolder: (data) => client.post('/browse/move-folder', data),
  exportFolderHtml: (path) => client.post('/browse/export-html-save', { path }),
  renameFolder: (path, newName) => client.post('/browse/rename-folder', { path, new_name: newName }),
  deleteExtraFile: (path) => client.post('/browse/delete-extra-file', { path }),
}

// Artists
export const artistsApi = {
  list: (params) => client.get('/artists/', { params }),
  get: (id) => client.get(`/artists/${id}`),
}

// Albums
export const albumsApi = {
  list: (params) => client.get('/albums/', { params }),
  get: (id) => client.get(`/albums/${id}`),
  exportHtml: (id) => client.get(`/albums/${id}/export-html`, { responseType: 'blob' }),
  setDescription: (id, description) => client.patch(`/albums/${id}/description`, { description }),
}

// Tracks
export const tracksApi = {
  list: (params) => client.get('/tracks/', { params }),
  get: (id) => client.get(`/tracks/${id}`),
  getLyrics: (id) => client.get(`/tracks/${id}/lyrics`),
  update: (id, data) => client.patch(`/tracks/${id}`, data),
  batchUpdate: (data) => client.post('/tracks/batch-update', data),
}

// Workspace
export const workspaceApi = {
  // 세션
  getCurrentSession: () => client.get('/workspace/current-session'),
  newSession: () => client.post('/workspace/session/new'),
  updateSession: (id, data) => client.patch(`/workspace/session/${id}`, data),
  discardSession: (id) => client.post(`/workspace/session/${id}/discard`),
  applySession: (id) => client.post(`/workspace/session/${id}/apply`, {}, { timeout: 120000 }),

  // 불러오기
  loadFolder: (folder_path, recursive = false) =>
    client.post('/workspace/load-folder', { folder_path, recursive }),
  loadFiles: (file_paths) =>
    client.post('/workspace/load-files', { file_paths }),

  // 아이템
  getItems: () => client.get('/workspace/items'),
  removeItem: (id) => client.delete(`/workspace/items/${id}`),
  clearItems: () => client.delete('/workspace/items'),
  applyItem: (id) => client.post(`/workspace/items/${id}/apply`, {}, { timeout: 30000 }),

  // 스테이징
  stageTags: (id, tags) => client.put(`/workspace/items/${id}/stage-tags`, { tags }),
  stageRename: (id, new_name) => client.put(`/workspace/items/${id}/stage-rename`, { new_name }),
  unstageTags: (id) => client.delete(`/workspace/items/${id}/stage-tags`),
  getDiff: (id) => client.get(`/workspace/items/${id}/diff`),

  // 히스토리
  getHistory: (params) => client.get('/workspace/history', { params }),
  getHistoryDetail: (id) => client.get(`/workspace/history/${id}`),
  deleteHistory: (id) => client.delete(`/workspace/history/${id}`),

  // 라이브러리 피커
  libraryRoots: () => client.get('/workspace/library/roots'),
  libraryChildren: (path) => client.get('/workspace/library/children', { params: { path } }),
}

// Covers
export const coversApi = {
  getAlbumCover: (id) => client.get(`/covers/album/${id}`),
  uploadAlbumCover: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post(`/covers/album/${id}`, form)
  },
  deleteAlbumCover: (id) => client.delete(`/covers/album/${id}`),
}
