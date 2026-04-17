import client from './index.js'

export const metadataApi = {
  search: (params) => client.get('/metadata/search', { params }),
  searchForTrack: (trackId) => client.get(`/metadata/track/${trackId}`),
  getAlbumTracks: (spotifyAlbumId) => client.get('/metadata/album-tracks', { params: { spotify_album_id: spotifyAlbumId } }),
  apply: (trackId, data) => client.post(`/metadata/apply/${trackId}`, data),
  applyAlbumCover: (albumId, coverUrl) => client.post('/metadata/apply-album-cover', { album_id: albumId, cover_url: coverUrl }),
  revertAutoTag: (items) => client.post('/metadata/revert-auto-tag', { items }),

  /**
   * 파일명 자동태그 — SSE 스트리밍
   * onProgress(current, total, filename, item) 콜백으로 진행 상황 전달
   * onDone(summary) 콜백으로 완료 전달
   */
  async autoTagByFilenameStream(data, { onProgress, onDone } = {}) {
    const token = localStorage.getItem('eztag-token')
    const response = await fetch('/api/metadata/auto-tag-by-filename', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // 마지막 미완성 줄 보존
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'progress' && onProgress) {
            onProgress(event.current, event.total, event.filename, event.item)
          } else if (event.type === 'done' && onDone) {
            onDone(event.summary)
          }
        } catch (_) { /* ignore parse errors */ }
      }
    }
  },
}

export const schedulerApi = {
  status: () => client.get('/scheduler/status'),
  trigger: () => client.post('/scheduler/trigger'),
  applyConfig: () => client.post('/scheduler/apply-config'),
}
