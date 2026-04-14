"""YouTube Data API v3를 이용한 뮤직비디오 검색."""
import logging
import re
import unicodedata
import urllib.parse
import urllib.request
import json

_log = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# 공식 MV로 판단하는 제목 키워드
_MV_KEYWORDS = ["mv", "m/v", "뮤직비디오", "music video", "official video", "official mv"]
# 비공식/커버/라이브 등을 제외하는 키워드
_EXCLUDE_KEYWORDS = ["cover", "live", "reaction", "lyrics", "lyric", "karaoke", "piano",
                     "instrumental", "remix", "dance practice", "fancam", "fan cam", "직캠",
                     "teaser", "making", "behind"]


def _normalize(text: str) -> str:
    """소문자 변환, 괄호 내용·특수문자 제거."""
    text = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', text)
    text = text.lower()
    # 유니코드 NFC 정규화
    text = unicodedata.normalize("NFC", text)
    # 알파벳·숫자·한글·공백만 유지
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_official_mv(video_title: str, channel_title: str, artist: str = "") -> bool:
    """제목/채널명 기반으로 공식 뮤직비디오 여부 판별."""
    t_lower = video_title.lower()
    ch_lower = channel_title.lower()

    # 비공식 키워드가 제목에 있으면 제외
    for kw in _EXCLUDE_KEYWORDS:
        if kw in t_lower:
            return False

    # 채널 검증: 공식 채널 판별
    official_channel_words = ["official", "vevo", "labels", "entertainment", "music"]
    is_official_channel = any(w in ch_lower for w in official_channel_words)
    if artist:
        is_official_channel = is_official_channel or (_normalize(artist) in _normalize(channel_title))

    # 제목 검증: MV 키워드 포함 + 티저 아님
    is_official_video = any(kw in t_lower for kw in _MV_KEYWORDS) and "teaser" not in t_lower

    return is_official_channel or is_official_video


def _title_matches(track_title: str, video_title: str, artist: str = "", channel: str = "") -> bool:
    """트랙 제목의 핵심 단어가 YouTube 영상 제목에 충분히 포함되는지 확인."""
    norm_track = _normalize(track_title)
    norm_video = _normalize(video_title)

    words = [w for w in norm_track.split() if len(w) >= 2]
    if not words:
        return False  # 제목이 너무 짧으면 거부

    # 모든 핵심 단어가 영상 제목에 포함되어야 함 (100% 매치)
    if not all(w in norm_video for w in words):
        return False

    # 아티스트 이름이 영상 제목 또는 채널명에 포함되어야 함 (전체 아티스트명 단위 검사)
    if artist:
        norm_artist = _normalize(artist)
        norm_channel = _normalize(channel)
        in_title = norm_artist in norm_video
        in_channel = norm_artist in norm_channel if channel else False
        if not in_title and not in_channel:
            return False

    return True


def search_music_video(artist: str, title: str, api_key: str, max_results: int = 10) -> list[dict]:
    """
    YouTube Data API v3로 공식 뮤직비디오 검색.
    - 제목 불일치 결과 필터링
    - 공식 MV 우선 정렬 후 최대 5개 반환
    반환: [{"video_id", "title", "url", "thumbnail", "channel"}]
    """
    # 정확한 매칭을 위해 따옴표 사용, 비공식 키워드 제외
    query = f'"{artist}" "{title}" official mv -cover -lyrics -reaction -live'
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",  # Music
        "regionCode": "KR",
        "maxResults": max_results,
        "key": api_key,
    })
    url = f"{YOUTUBE_SEARCH_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Referer": "https://localhost/",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        _log.error(f"YouTube API 요청 실패: {e}")
        raise RuntimeError(f"YouTube API 오류: {e}")

    official = []
    others = []
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId")
        snip = item.get("snippet", {})
        if not vid:
            continue
        video_title = snip.get("title", "")
        channel = snip.get("channelTitle", "")

        # 제목 불일치 결과 제외
        if not _title_matches(title, video_title, artist, channel):
            _log.debug(f"제목 불일치 제외: '{video_title}' (검색: '{artist} {title}')")
            continue

        is_official = _is_official_mv(video_title, channel, artist)
        entry = {
            "video_id": vid,
            "title": video_title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "channel": channel,
            "is_official": is_official,
        }
        if is_official:
            official.append(entry)
        else:
            others.append(entry)

    # 공식 MV 우선, 없으면 기타 결과로 fallback (최대 5개)
    return (official if official else others)[:5]
