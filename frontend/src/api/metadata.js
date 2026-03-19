import client from './index.js'

export const metadataApi = {
  search: (params) => client.get('/metadata/search', { params }),
  searchForTrack: (trackId) => client.get(`/metadata/track/${trackId}`),
  getAlbumTracks: (spotifyAlbumId) => client.get('/metadata/album-tracks', { params: { spotify_album_id: spotifyAlbumId } }),
  apply: (trackId, data) => client.post(`/metadata/apply/${trackId}`, data),
  applyAlbumCover: (albumId, coverUrl) => client.post('/metadata/apply-album-cover', { album_id: albumId, cover_url: coverUrl }),
}

export const schedulerApi = {
  status: () => client.get('/scheduler/status'),
  trigger: () => client.post('/scheduler/trigger'),
  applyConfig: () => client.post('/scheduler/apply-config'),
}
