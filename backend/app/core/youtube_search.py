"""YouTube Data API v3를 이용한 뮤직비디오 검색."""
import logging
import urllib.parse
import urllib.request
import json

_log = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_music_video(artist: str, title: str, api_key: str, max_results: int = 5) -> list[dict]:
    """
    YouTube Data API v3로 뮤직비디오 검색.
    반환: [{"video_id", "title", "url", "thumbnail", "channel"}]
    """
    query = f"{artist} {title} MV Official"
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",  # Music
        "maxResults": max_results,
        "key": api_key,
    })
    url = f"{YOUTUBE_SEARCH_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        _log.error(f"YouTube API 요청 실패: {e}")
        raise RuntimeError(f"YouTube API 오류: {e}")

    results = []
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId")
        snip = item.get("snippet", {})
        if not vid:
            continue
        results.append({
            "video_id": vid,
            "title": snip.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "channel": snip.get("channelTitle", ""),
        })
    return results
