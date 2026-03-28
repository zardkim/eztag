"""HTML Export - 앨범/폴더를 자체 완결형 HTML 파일로 내보내기."""
import base64
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)


# ── 커버아트 추출 ─────────────────────────────────────────────
def _cover_to_b64(cover_path: Optional[str] = None, track_paths: Optional[list[str]] = None) -> Optional[str]:
    """커버아트를 base64 data URI로 반환. 없으면 None."""
    # 1) DB cover_path
    if cover_path:
        try:
            p = Path(cover_path)
            if not p.is_absolute():
                from app.core.config_store import get_config_value
                data_dir = get_config_value("data_dir", "/app/data")
                p = Path(data_dir) / "covers" / cover_path
            if p.exists():
                data = p.read_bytes()
                suffix = p.suffix.lower().lstrip(".")
                mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(suffix, "image/jpeg")
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        except Exception as e:
            _log.debug(f"cover_path read failed: {e}")

    # 2) 트랙 파일에서 추출
    if track_paths:
        from app.core.tag_reader import extract_cover_at
        for path in track_paths:
            try:
                result = extract_cover_at(path, 0)
                if result:
                    data, mime = result
                    return f"data:{mime};base64,{base64.b64encode(data).decode()}"
            except Exception:
                continue
    return None


# ── 유틸 함수 ─────────────────────────────────────────────────
def _fmt_duration(sec: Optional[float]) -> str:
    if not sec:
        return "-"
    s = int(sec)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _fmt_size(size: Optional[int]) -> str:
    if not size:
        return "-"
    if size >= 1024 ** 3:
        return f"{size / 1024 ** 3:.1f} GB"
    if size >= 1024 ** 2:
        return f"{size / 1024 ** 2:.1f} MB"
    return f"{size / 1024:.0f} KB"


def _fmt_date(ts: Optional[float]) -> str:
    if not ts:
        return "-"
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return "-"


def _safe(v) -> str:
    if v is None:
        return ""
    s = str(v)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "export"


def _total_duration(tracks: list[dict]) -> str:
    total = sum(t.get("duration") or 0 for t in tracks)
    return _fmt_duration(total) if total else ""


# ── CSS ───────────────────────────────────────────────────────
_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f5f5f7;
  --surface: #ffffff;
  --border: #e2e2e8;
  --text: #111111;
  --text2: #55556a;
  --text3: #99999e;
  --accent: #ff4757;
  --row-hover: #f7f7fb;
  --hero-overlay: rgba(10,10,20,0.42);
  --hero-cover-size: 240px;
  --badge-mp3: #fff0eb; --badge-mp3-t: #c2410c;
  --badge-flac: #eff6ff; --badge-flac-t: #1d4ed8;
  --badge-m4a: #faf5ff; --badge-m4a-t: #7c3aed;
  --badge-ogg: #f0fdf4; --badge-ogg-t: #15803d;
  --badge-other: #f3f4f6; --badge-other-t: #374151;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0a0a0f;
    --surface: #18181f;
    --border: #2a2a38;
    --text: #f0f0f5;
    --text2: #8a8a9e;
    --text3: #55556a;
    --accent: #ff4757;
    --row-hover: #1e1e28;
    --hero-overlay: rgba(0,0,0,0.52);
    --badge-mp3: #431407; --badge-mp3-t: #fed7aa;
    --badge-flac: #1e3a5f; --badge-flac-t: #bfdbfe;
    --badge-m4a: #3b0764; --badge-m4a-t: #e9d5ff;
    --badge-ogg: #052e16; --badge-ogg-t: #bbf7d0;
    --badge-other: #1f2937; --badge-other-t: #d1d5db;
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}

/* ── Hero Banner ── */
.hero {
  position: relative;
  overflow: hidden;
  min-height: 280px;
  margin-bottom: 28px;
}
.hero-bg {
  position: absolute;
  inset: -30px;
  background-size: cover;
  background-position: center;
  filter: blur(32px) brightness(0.45) saturate(3.0);
  z-index: 0;
}
.hero-bg-grad {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.hero-bg-vignette {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.08) 0%, rgba(0,0,0,0.55) 100%);
  z-index: 0;
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background: var(--hero-overlay);
  z-index: 1;
}
.hero-inner {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 44px 32px 40px;
  display: flex;
  gap: 36px;
  align-items: flex-end;
}
.hero-cover {
  width: var(--hero-cover-size);
  height: var(--hero-cover-size);
  min-width: var(--hero-cover-size);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.55), 0 4px 16px rgba(0,0,0,0.3);
  background: rgba(255,255,255,0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72px;
  flex-shrink: 0;
}
.hero-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hero-info { flex: 1; min-width: 0; }
.hero-type-badge {
  display: inline-block;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; color: rgba(255,255,255,0.7);
  border: 1px solid rgba(255,255,255,0.35);
  padding: 3px 10px; border-radius: 20px;
  margin-bottom: 12px;
}
.hero-title {
  font-size: 34px; font-weight: 900; line-height: 1.15;
  color: #ffffff;
  text-shadow: 0 2px 16px rgba(0,0,0,0.45);
  margin-bottom: 10px;
  word-break: break-word;
}
.hero-artist {
  font-size: 18px; font-weight: 600;
  color: rgba(255,255,255,0.85);
  margin-bottom: 12px;
  display: block;
}
.hero-meta {
  font-size: 13px; color: rgba(255,255,255,0.6);
  margin-bottom: 12px;
}
.hero-meta .sep { margin: 0 4px; opacity: 0.5; }
.hero-stats {
  font-size: 13px; color: rgba(255,255,255,0.5);
  display: flex; align-items: center; flex-wrap: wrap; gap: 12px;
}
.hero-badge { margin-left: auto; }

/* ── 페이지 본문 ── */
.page { max-width: 1200px; margin: 0 auto; padding: 0 16px 60px; }

/* ── 섹션 타이틀 ── */
.section-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: var(--text3);
  margin-bottom: 8px; padding-left: 2px;
}

/* ── 앨범 소개 (PC) ── */
.desc-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px 24px; margin-bottom: 24px;
  font-size: 13px; color: var(--text2); line-height: 1.8;
  white-space: pre-wrap; word-break: break-word;
}

/* ── 앨범 소개 (모바일, 접기/펼치기) ── */
details.desc-details {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; overflow: hidden; margin-bottom: 24px;
}
details.desc-details summary {
  padding: 13px 18px; cursor: pointer;
  font-size: 13px; font-weight: 600; color: var(--text2);
  user-select: none; list-style: none;
  display: flex; align-items: center; gap: 7px;
}
details.desc-details summary::-webkit-details-marker { display: none; }
details.desc-details summary::before {
  content: "▶"; font-size: 9px; color: var(--text3);
  transition: transform 0.2s; flex-shrink: 0;
}
details.desc-details[open] summary::before { transform: rotate(90deg); }
details.desc-details .desc-box {
  margin: 0; border: none; border-radius: 0;
  border-top: 1px solid var(--border);
}

/* ── PC 트랙 테이블 ── */
.track-table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin-bottom: 24px;
}
.track-table {
  width: 100%; min-width: 480px;
  border-collapse: collapse; font-size: 13px;
}
.track-table thead th {
  padding: 12px 12px;
  text-align: left;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: var(--text3);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  background: transparent;
}
.track-table thead th.num { text-align: center; width: 44px; }
.track-table thead th.dur { text-align: right; width: 60px; }
.track-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}
.track-table tbody tr:last-child { border-bottom: none; }
.track-table tbody tr:hover { background: var(--row-hover); }
.track-table td { padding: 11px 12px; vertical-align: middle; color: var(--text); }
.track-table td.num {
  text-align: center; color: var(--text3);
  font-variant-numeric: tabular-nums; width: 44px;
}
.track-table td.dur {
  text-align: right; color: var(--text3);
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, monospace; font-size: 12px;
}

/* 트랙번호 hover → ▶ 전환 */
.num .num-idx { display: inline; }
.num .num-play { display: none; color: var(--accent); font-size: 11px; }
.track-table tbody tr:hover .num .num-idx { display: none; }
.track-table tbody tr:hover .num .num-play { display: inline; }

/* 제목 셀 */
.title-cell { display: flex; flex-direction: column; gap: 1px; }
.title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; font-weight: 600; }

/* ── 타이틀곡 뱃지 ── */
.title-track-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--accent); color: #fff;
  vertical-align: middle; flex-shrink: 0; line-height: 1;
}

/* ── 가사 뱃지 ── */
.lyrics-badge {
  display: inline-block; padding: 1px 5px; border-radius: 3px;
  background: #e8f0fe; color: #1a73e8;
  font-size: 9px; font-weight: 700; letter-spacing: 0.3px;
  vertical-align: middle; font-family: ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) {
  .lyrics-badge { background: #1e3a5f; color: #bfdbfe; }
}

/* ── 코덱 뱃지 ── */
.badge {
  display: inline-block; padding: 2px 6px; border-radius: 5px;
  font-size: 10px; font-weight: 700;
  font-family: ui-monospace, monospace; text-transform: uppercase;
}
.badge-mp3  { background: var(--badge-mp3);  color: var(--badge-mp3-t); }
.badge-flac { background: var(--badge-flac); color: var(--badge-flac-t); }
.badge-m4a  { background: var(--badge-m4a);  color: var(--badge-m4a-t); }
.badge-ogg  { background: var(--badge-ogg);  color: var(--badge-ogg-t); }
.badge-other{ background: var(--badge-other); color: var(--badge-other-t); }

/* ── 옵션 컬럼 ── */
.col-disc    { text-align: center; width: 52px; color: var(--text3); font-size: 12px; }
.col-artist  { color: var(--text2); }
.col-aa      { min-width: 100px; color: var(--text2); font-size: 12px; }
.col-album   { min-width: 120px; color: var(--text2); font-size: 12px; }
.col-year    { text-align: center; width: 56px; color: var(--text2); font-size: 12px; }
.col-genre   { min-width: 80px; color: var(--text2); font-size: 12px; }
.col-rd      { white-space: nowrap; text-align: center; width: 90px; color: var(--text2); font-size: 12px; }
.col-isrc    { font-family: ui-monospace, monospace; font-size: 11px; color: var(--text2); white-space: nowrap; }
.col-comment { color: var(--text2); font-size: 12px; max-width: 200px; }
.col-br      { text-align: center; width: 80px; color: var(--text3); font-size: 12px; }
.col-hz      { text-align: center; width: 72px; color: var(--text3); font-size: 12px; }
.col-size    { text-align: right; width: 72px; color: var(--text3); font-size: 12px; font-family: ui-monospace, monospace; }
.col-yt      { text-align: center; width: 38px; }
.yt-play-btn {
  background: none; border: none; padding: 0; cursor: pointer;
  display: inline-flex; align-items: center; color: #ff0000;
  opacity: 0.8; transition: opacity 0.15s, transform 0.1s;
}
.yt-play-btn:hover { opacity: 1; transform: scale(1.15); }

/* ── 모바일 카드 리스트 ── */
.track-card-list { display: none; margin-bottom: 24px; }
.track-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 8px;
  overflow: hidden;
}
.tc-main {
  display: flex; align-items: center; gap: 10px;
  padding: 13px 14px;
}
.tc-num {
  width: 28px; min-width: 28px; text-align: center;
  font-size: 13px; color: var(--text3); font-variant-numeric: tabular-nums;
}
.tc-info { flex: 1; min-width: 0; }
.tc-title {
  font-size: 14px; font-weight: 600; color: var(--text);
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
  margin-bottom: 3px;
}
.tc-artist { font-size: 12px; color: var(--text3); }
.tc-right {
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}
.tc-dur {
  font-size: 12px; color: var(--text3);
  font-family: ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}
/* 카드 기술정보 아코디언 */
details.tc-details { border-top: 1px solid var(--border); }
details.tc-details summary {
  padding: 8px 14px; cursor: pointer;
  font-size: 11px; color: var(--text3); font-weight: 600;
  user-select: none; list-style: none;
  display: flex; align-items: center; gap: 5px;
}
details.tc-details summary::-webkit-details-marker { display: none; }
details.tc-details summary::before {
  content: "▶"; font-size: 8px; transition: transform 0.15s; flex-shrink: 0;
}
details.tc-details[open] summary::before { transform: rotate(90deg); }
.tc-tech {
  padding: 10px 14px 14px;
  display: grid; grid-template-columns: auto 1fr; gap: 5px 14px;
  font-size: 11px;
}
.tc-tech-label { color: var(--text3); font-weight: 500; white-space: nowrap; }
.tc-tech-val { color: var(--text2); word-break: break-all; }

/* ── YouTube 다이얼로그 ── */
.yt-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.88); z-index: 9000;
  align-items: center; justify-content: center;
}
.yt-overlay.open { display: flex; }
.yt-dialog {
  position: relative; width: min(854px, 95vw);
  aspect-ratio: 16/9; background: #000;
  border-radius: 10px; overflow: hidden;
  box-shadow: 0 30px 80px rgba(0,0,0,0.6);
}
.yt-dialog iframe { width: 100%; height: 100%; border: none; display: block; }
.yt-close {
  position: absolute; top: -40px; right: 0;
  background: none; border: none; color: rgba(255,255,255,0.85);
  font-size: 28px; line-height: 1; cursor: pointer; padding: 4px 8px;
}
.yt-close:hover { color: #fff; }

/* ── eztag 배지 ── */
.eztag-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(79,70,229,0.08);
  border: 1px solid rgba(79,70,229,0.2);
  color: #4f46e5;
  font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
  padding: 4px 10px 4px 5px; border-radius: 20px; text-decoration: none;
  opacity: 0.9;
}
.eztag-badge:hover { opacity: 1; }
@media (prefers-color-scheme: dark) {
  .eztag-badge { background: rgba(129,140,248,0.12); border-color: rgba(129,140,248,0.25); color: #818cf8; }
}
.eztag-badge-lg { padding: 6px 14px 6px 8px; font-size: 13px; gap: 8px; }

/* ── Hero 내 eztag 배지: 배경이 어두우므로 밝은 색상 강제 ── */
.hero .eztag-badge {
  background: rgba(255,255,255,0.15);
  border-color: rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.9);
}
.hero .eztag-badge:hover {
  background: rgba(255,255,255,0.25);
  color: #ffffff;
}

/* ── 푸터 ── */
.footer {
  text-align: center; font-size: 11px; color: var(--text3);
  padding-top: 20px; border-top: 1px solid var(--border);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.footer a { color: var(--accent); text-decoration: none; }

/* ── 모바일 반응형 (767px 이하) ── */
@media (max-width: 767px) {
  .hero-inner {
    flex-direction: column; align-items: center;
    text-align: center; padding: 32px 20px 28px;
  }
  :root { --hero-cover-size: 160px; }
  .hero-title { font-size: 24px; }
  .hero-meta { display: block; }
  .hero-stats { justify-content: center; }
  .hero-badge { margin-left: 0; }
  /* PC 테이블 숨기기 */
  .track-table-wrap { display: none; }
  /* 모바일 카드 표시 */
  .track-card-list { display: block; }
  /* PC 앨범소개 숨기기 */
  .desc-box-pc { display: none; }
}

@media (min-width: 768px) {
  /* 모바일 접기/펼치기 앨범소개 숨기기 */
  details.desc-details { display: none; }
}

/* ── 인쇄 최적화 ── */
@media print {
  body { background: white; color: black; }
  .hero-bg, .hero-bg-grad, .hero-overlay { display: none !important; }
  .hero { background: #f5f5f7 !important; min-height: auto; }
  .hero-title, .hero-artist { color: black !important; text-shadow: none !important; }
  .hero-meta, .hero-stats, .hero-type-badge { color: #444 !important; border-color: #999 !important; }
  .track-table-wrap { display: block !important; break-inside: avoid; }
  .track-card-list { display: none !important; }
  details.desc-details { display: block !important; }
  details.desc-details summary { display: none; }
  details.tc-details[open] { display: block; }
}
"""


# ── 인라인 로고 SVG ───────────────────────────────────────────
def _logo_svg(size: int = 18) -> str:
    """eztag 아이콘을 인라인 SVG로 반환."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" '
        'xmlns="http://www.w3.org/2000/svg" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0;border-radius:{size//5}px;">'
        '<defs>'
        '<linearGradient id="ezl-bg" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#4f46e5"/>'
        '<stop offset="100%" stop-color="#7c3aed"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="100" height="100" rx="22" fill="url(#ezl-bg)"/>'
        '<path d="M20 26 L60 26 L80 50 L60 74 L20 74 Q15 74 15 69 L15 31 Q15 26 20 26 Z" '
        'fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.6)" stroke-width="2.5" stroke-linejoin="round"/>'
        '<circle cx="25" cy="50" r="5.5" fill="#4338ca"/>'
        '<circle cx="25" cy="50" r="4" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/>'
        '<ellipse cx="52" cy="60" rx="7.5" ry="5.5" fill="white" transform="rotate(-18,52,60)"/>'
        '<line x1="58.5" y1="57" x2="58.5" y2="30" stroke="white" stroke-width="3.5" stroke-linecap="round"/>'
        '<path d="M58.5 30 C70 34 74 42 66 50 C66 44 60 40 58.5 38 Z" fill="white"/>'
        '</svg>'
    )


def _extract_youtube_id(url: Optional[str]) -> Optional[str]:
    """YouTube URL에서 video ID 추출."""
    if not url:
        return None
    import re as _re
    patterns = [
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/watch\?.*v=([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = _re.search(pat, url)
        if m:
            return m.group(1)
    return None


_I18N: dict[str, dict[str, str]] = {
    "ko": {
        "lang":            "ko",
        "tracks":          "{n}곡",
        "duration":        "재생시간 {dur}",
        "album_intro":     "앨범 소개",
        "track_list":      "트랙 목록",
        "col_disc":        "디스크",
        "col_track":       "트랙",
        "col_title":       "제목",
        "col_artist":      "아티스트",
        "col_aa":          "앨범아티스트",
        "col_album":       "앨범",
        "col_year":        "연도",
        "col_genre":       "장르",
        "col_rel_date":    "발매일",
        "col_isrc":        "ISRC",
        "col_comment":     "설명",
        "col_dur":         "길이",
        "col_br":          "비트레이트",
        "col_hz":          "주파수",
        "col_size":        "용량",
        "col_codec":       "포맷",
        "has_lyrics":      "가사 있음",
        "title_track":     "타이틀",
        "play_mv":         "뮤직비디오 재생",
        "close":           "닫기",
        "more_info":       "태그 정보",
        "type_single":     "싱글",
        "type_ep":         "EP",
        "type_album":      "정규앨범",
    },
    "en": {
        "lang":            "en",
        "tracks":          "{n} tracks",
        "duration":        "Duration {dur}",
        "album_intro":     "About",
        "track_list":      "Track List",
        "col_disc":        "Disc",
        "col_track":       "Track",
        "col_title":       "Title",
        "col_artist":      "Artist",
        "col_aa":          "Album Artist",
        "col_album":       "Album",
        "col_year":        "Year",
        "col_genre":       "Genre",
        "col_rel_date":    "Release Date",
        "col_isrc":        "ISRC",
        "col_comment":     "Comment",
        "col_dur":         "Duration",
        "col_br":          "Bitrate",
        "col_hz":          "Frequency",
        "col_size":        "Size",
        "col_codec":       "Format",
        "has_lyrics":      "Has Lyrics",
        "title_track":     "Title",
        "play_mv":         "Play Music Video",
        "close":           "Close",
        "more_info":       "Tag Info",
        "type_single":     "Single",
        "type_ep":         "EP",
        "type_album":      "Album",
    },
}

# YouTube 아이콘 SVG
_YT_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15">'
    '<path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501'
    's-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805'
    ' 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502'
    ' 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0'
    ' .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>'
    '</svg>'
)

# 앨범 제목 첫 글자로 Hero 그라디언트 결정 (커버 없을 때)
_HERO_GRADIENTS = [
    "#667eea,#764ba2", "#f093fb,#f5576c", "#4facfe,#00f2fe",
    "#43e97b,#38f9d7", "#fa709a,#fee140", "#a18cd1,#fbc2eb",
    "#fda085,#f6d365", "#96fbc4,#f9f7ff", "#ff6b6b,#feca57",
    "#48dbfb,#ff9ff3",
]


def build_html(
    tracks: list[dict],
    album_title: str,
    album_artist: Optional[str] = None,
    year: Optional[int] = None,
    genre: Optional[str] = None,
    label: Optional[str] = None,
    cover_b64: Optional[str] = None,
    source_path: Optional[str] = None,
    description: Optional[str] = None,
    youtube_url: Optional[str] = None,
    lang: str = "ko",
) -> str:
    """트랙 목록 + 태그 메타데이터로 자체 완결형 HTML 생성."""
    i18n = _I18N.get(lang, _I18N["ko"])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    page_title = f"{album_title}" + (f" – {album_artist}" if album_artist else "")
    folder_name = Path(source_path).name if source_path else ""

    # 커버아트 HTML
    cover_html = f'<img src="{cover_b64}" alt="cover" />' if cover_b64 else "💿"

    # 앨범 타입 자동 분류
    tc = len(tracks)
    if tc == 1:
        album_type = i18n["type_single"]
    elif tc <= 5:
        album_type = i18n["type_ep"]
    else:
        album_type = i18n["type_album"]

    # Hero 배경
    if cover_b64:
        hero_bg_html = (
            f'<div class="hero-bg" style="background-image: url({cover_b64});"></div>'
            f'<div class="hero-bg-vignette"></div>'
        )
    else:
        idx = (ord(album_title[0]) if album_title else 0) % len(_HERO_GRADIENTS)
        g = _HERO_GRADIENTS[idx]
        hero_bg_html = f'<div class="hero-bg-grad" style="background: linear-gradient(135deg, {g});"></div>'

    # 메타 라인
    meta_parts = []
    if year:
        meta_parts.append(_safe(str(year)))
    if genre:
        meta_parts.append(_safe(genre))
    if label:
        meta_parts.append(_safe(label))
    meta_html = ' <span class="sep">·</span> '.join(meta_parts)

    # 통계
    total_dur = _total_duration(tracks)
    stats_parts = [i18n["tracks"].format(n=len(tracks))]
    if total_dur:
        stats_parts.append(i18n["duration"].format(dur=total_dur))
    stats_html = " · ".join(stats_parts)

    # 앨범 소개
    desc_html_pc = ""
    desc_html_mobile = ""
    if description and description.strip():
        desc_escaped = _safe(description).replace("\n", "<br>")
        desc_html_pc = (
            f'  <div class="section-title">{i18n["album_intro"]}</div>\n'
            f'  <div class="desc-box desc-box-pc">{desc_escaped}</div>\n'
        )
        desc_html_mobile = (
            f'  <details class="desc-details">\n'
            f'    <summary>{i18n["album_intro"]}</summary>\n'
            f'    <div class="desc-box">{desc_escaped}</div>\n'
            f'  </details>\n'
        )

    # 옵션 컬럼 존재 여부
    has_youtube          = any(t.get("youtube_url") for t in tracks)
    has_multi_disc       = True  # 항상 표시
    has_album_artist_col = any(
        t.get("album_artist") and t.get("album_artist") != t.get("artist")
        for t in tracks
    )
    has_album_col  = any(t.get("album_title") for t in tracks)
    has_year_col   = any(t.get("year") for t in tracks)
    has_genre_col  = any(t.get("genre") for t in tracks)
    has_rel_date   = any(t.get("release_date") for t in tracks)
    has_isrc       = any(t.get("isrc") for t in tracks)
    has_comment    = any(t.get("comment") for t in tracks)
    has_bitrate    = any(t.get("bitrate") for t in tracks)
    has_samplerate = any(t.get("sample_rate") for t in tracks)
    has_filesize   = any(t.get("file_size") for t in tracks)

    # ── PC 테이블 헤더 ──
    th_parts = []
    if has_multi_disc:
        th_parts.append(f'<th class="col-disc">{i18n["col_disc"]}</th>')
    th_parts.append(f'<th class="num">{i18n["col_track"]}</th>')
    th_parts.append(f'<th>{i18n["col_title"]}</th>')
    th_parts.append(f'<th class="col-artist">{i18n["col_artist"]}</th>')
    if has_album_artist_col:
        th_parts.append(f'<th class="col-aa">{i18n["col_aa"]}</th>')
    if has_album_col:
        th_parts.append(f'<th class="col-album">{i18n["col_album"]}</th>')
    if has_year_col:
        th_parts.append(f'<th class="col-year">{i18n["col_year"]}</th>')
    if has_genre_col:
        th_parts.append(f'<th class="col-genre">{i18n["col_genre"]}</th>')
    if has_rel_date:
        th_parts.append(f'<th class="col-rd">{i18n["col_rel_date"]}</th>')
    if has_isrc:
        th_parts.append(f'<th class="col-isrc">{i18n["col_isrc"]}</th>')
    if has_comment:
        th_parts.append(f'<th class="col-comment">{i18n["col_comment"]}</th>')
    th_parts.append(f'<th class="dur">{i18n["col_dur"]}</th>')
    if has_youtube:
        th_parts.append('<th class="col-yt">MV</th>')
    if has_bitrate:
        th_parts.append(f'<th class="col-br">{i18n["col_br"]}</th>')
    if has_samplerate:
        th_parts.append(f'<th class="col-hz">{i18n["col_hz"]}</th>')
    if has_filesize:
        th_parts.append(f'<th class="col-size">{i18n["col_size"]}</th>')
    thead_html = "<tr>" + "".join(th_parts) + "</tr>"

    # ── 트랙 행 + 카드 ──
    track_rows = []
    card_items = []

    for t in tracks:
        disc    = t.get("disc_no") or 1
        num     = t.get("track_no")
        num_str = f"{num:02d}" if num else "—"
        disc_str = str(disc)
        dur_str  = _fmt_duration(t.get("duration"))
        file_attr = Path(t.get("file_path", "")).name if t.get("file_path") else ""

        lyrics_badge = (
            f'<span class="lyrics-badge" title="{i18n["has_lyrics"]}">LRC</span>'
            if t.get("has_lyrics") else ""
        )
        title_badge = (
            f'<span class="title-track-badge" title="{i18n["title_track"]}">'
            f'<svg viewBox="0 0 24 24" fill="currentColor" width="9" height="9">'
            f'<path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .55-.45 1-1 1H6c-.55 0-1-.45-1-1v-1h14v1z"/>'
            f'</svg></span>'
            if t.get("is_title_track") else ""
        )

        # YouTube 버튼
        yt_vid = _extract_youtube_id(t.get("youtube_url") or "")
        if yt_vid:
            yt_btn = (
                f'<button class="yt-play-btn" onclick="openYT(\'{yt_vid}\')" title="{i18n["play_mv"]}">'
                + _YT_SVG
                + '</button>'
            )
        else:
            yt_btn = ""

        # ── PC 테이블 행 ──
        td_parts = []
        if has_multi_disc:
            td_parts.append(f'<td class="col-disc">{disc_str}</td>')
        td_parts.append(
            f'<td class="num">'
            f'<span class="num-idx">{num_str}</span>'
            f'<span class="num-play">&#9654;</span>'
            f'</td>'
        )
        td_parts.append(
            f'<td><div class="title-cell">'
            f'<div class="title-row">'
            f'<span>{_safe(t.get("title") or "")}</span>'
            f'{title_badge}{lyrics_badge}'
            f'</div></div></td>'
        )
        td_parts.append(f'<td class="col-artist">{_safe(t.get("artist") or "")}</td>')
        if has_album_artist_col:
            td_parts.append(f'<td class="col-aa">{_safe(t.get("album_artist") or "")}</td>')
        if has_album_col:
            td_parts.append(f'<td class="col-album">{_safe(t.get("album_title") or "")}</td>')
        if has_year_col:
            td_parts.append(f'<td class="col-year">{_safe(str(t["year"]) if t.get("year") else "")}</td>')
        if has_genre_col:
            td_parts.append(f'<td class="col-genre">{_safe(t.get("genre") or "")}</td>')
        if has_rel_date:
            td_parts.append(f'<td class="col-rd">{_safe(t.get("release_date") or "")}</td>')
        if has_isrc:
            td_parts.append(f'<td class="col-isrc">{_safe(t.get("isrc") or "")}</td>')
        if has_comment:
            td_parts.append(f'<td class="col-comment">{_safe(t.get("comment") or "")}</td>')
        td_parts.append(f'<td class="dur">{dur_str}</td>')
        if has_youtube:
            td_parts.append(f'<td class="col-yt">{yt_btn}</td>')
        if has_bitrate:
            br = t.get("bitrate")
            td_parts.append(f'<td class="col-br">{f"{br}k" if br else "—"}</td>')
        if has_samplerate:
            sr = t.get("sample_rate")
            td_parts.append(f'<td class="col-hz">{f"{sr // 1000}kHz" if sr else "—"}</td>')
        if has_filesize:
            td_parts.append(f'<td class="col-size">{_fmt_size(t.get("file_size"))}</td>')

        track_rows.append(
            f'<tr data-file="{_safe(file_attr)}">' + "".join(td_parts) + "</tr>"
        )

        # ── 모바일 카드 기술정보 ──
        tech_rows = []
        codec = (t.get("file_format") or "").upper()
        if codec:
            badge_cls = (
                f'badge-{codec.lower()}'
                if codec.lower() in ("mp3", "flac", "m4a", "ogg")
                else "badge-other"
            )
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_codec"]}</span>'
                f'<span class="tc-tech-val"><span class="badge {badge_cls}">{_safe(codec)}</span></span>'
            )
        if t.get("bitrate"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_br"]}</span>'
                f'<span class="tc-tech-val">{t["bitrate"]}k</span>'
            )
        if t.get("sample_rate"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_hz"]}</span>'
                f'<span class="tc-tech-val">{t["sample_rate"] // 1000}kHz</span>'
            )
        if t.get("file_size"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_size"]}</span>'
                f'<span class="tc-tech-val">{_fmt_size(t["file_size"])}</span>'
            )
        if t.get("disc_no"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_disc"]}</span>'
                f'<span class="tc-tech-val">{t["disc_no"]}</span>'
            )
        if has_album_artist_col and t.get("album_artist"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_aa"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["album_artist"])}</span>'
            )
        if t.get("album_title"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_album"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["album_title"])}</span>'
            )
        if t.get("year"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_year"]}</span>'
                f'<span class="tc-tech-val">{t["year"]}</span>'
            )
        if t.get("genre"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_genre"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["genre"])}</span>'
            )
        if t.get("release_date"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_rel_date"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["release_date"])}</span>'
            )
        if t.get("isrc"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_isrc"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["isrc"])}</span>'
            )
        if t.get("comment"):
            tech_rows.append(
                f'<span class="tc-tech-label">{i18n["col_comment"]}</span>'
                f'<span class="tc-tech-val">{_safe(t["comment"])}</span>'
            )

        details_html = ""
        if tech_rows:
            details_html = (
                f'<details class="tc-details">'
                f'<summary>{i18n["more_info"]}</summary>'
                f'<div class="tc-tech">{"".join(tech_rows)}</div>'
                f'</details>'
            )

        card_items.append(
            f'<div class="track-card" data-file="{_safe(file_attr)}">'
            f'<div class="tc-main">'
            f'<span class="tc-num">{num_str}</span>'
            f'<div class="tc-info">'
            f'<div class="tc-title">'
            f'<span>{_safe(t.get("title") or "")}</span>'
            f'{title_badge}{lyrics_badge}'
            f'</div>'
            f'<div class="tc-artist">{_safe(t.get("artist") or "")}</div>'
            f'</div>'
            f'<div class="tc-right">'
            + (yt_btn if yt_btn else "")
            + f'<span class="tc-dur">{dur_str}</span>'
            f'</div>'
            f'</div>'
            + details_html
            + f'</div>'
        )

    source_note = (
        f'<span style="font-size:10px;color:var(--text3);">{_safe(folder_name)}</span>'
        if folder_name else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="{i18n["lang"]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="eztag">
<title>{_safe(page_title)}</title>
<style>{_CSS}</style>
</head>
<body>

<!-- Hero Banner -->
<div class="hero">
  {hero_bg_html}
  <div class="hero-overlay"></div>
  <div class="hero-inner">
    <div class="hero-cover">{cover_html}</div>
    <div class="hero-info">
      <span class="hero-type-badge">{_safe(album_type)}</span>
      <h1 class="hero-title">{_safe(album_title)}</h1>
      <span class="hero-artist">{_safe(album_artist or '')}</span>
      {f'<div class="hero-meta">{meta_html}</div>' if meta_html else ''}
      <div class="hero-stats">
        <span>{_safe(stats_html)}</span>
        <span class="hero-badge"><span class="eztag-badge">{_logo_svg(16)} eztag</span></span>
      </div>
    </div>
  </div>
</div>

<div class="page">
{desc_html_pc}{desc_html_mobile}
  <!-- 트랙 목록 -->
  <div class="section-title">{i18n["track_list"]}</div>

  <!-- PC 테이블 -->
  <div class="track-table-wrap">
    <table class="track-table">
      <thead>{thead_html}</thead>
      <tbody>
        {''.join(track_rows)}
      </tbody>
    </table>
  </div>

  <!-- 모바일 카드 -->
  <div class="track-card-list">
    {''.join(card_items)}
  </div>

  <!-- 푸터 -->
  <div class="footer">
    <span class="eztag-badge eztag-badge-lg">{_logo_svg(22)} eztag</span>
    <span>Generated · {now_str}{(' · ' + source_note) if source_note else ''}</span>
  </div>
</div>


<script>
function openYT(id) {{
  window.open('https://www.youtube.com/watch?v=' + id, '_blank', 'noopener,noreferrer');
}}
</script>
</body>
</html>"""

    return html


def track_model_to_dict(t) -> dict:
    """SQLAlchemy Track 모델 → dict."""
    return {
        "title": t.title,
        "artist": t.artist,
        "album_artist": t.album_artist,
        "album_title": t.album_title,
        "track_no": t.track_no,
        "disc_no": t.disc_no,
        "year": t.year,
        "genre": t.genre,
        "label": t.label,
        "isrc": t.isrc,
        "comment": t.comment,
        "release_date": t.release_date,
        "duration": t.duration,
        "bitrate": t.bitrate,
        "sample_rate": t.sample_rate,
        "file_format": t.file_format,
        "file_path": t.file_path,
        "file_size": t.file_size,
        "modified_time": t.modified_time,
        "tag_version": t.tag_version,
        "has_lyrics": t.has_lyrics,
        "has_cover": t.has_cover,
        "is_title_track": bool(t.is_title_track),
        "youtube_url": t.youtube_url,
    }


def parse_youtube_urls_from_html(html_path: str) -> dict:
    """eztag HTML 파일에서 파일명 → YouTube watch URL 매핑 추출.
    <tr data-file="filename.flac">..openYT('VIDEO_ID').. 패턴 파싱.
    """
    result = {}
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        pattern = r'<tr[^>]+data-file="([^"]+)"[^>]*>.*?openYT\(\'([A-Za-z0-9_-]{11})\'\)'
        for m in re.finditer(pattern, content, re.DOTALL):
            filename, yt_id = m.group(1), m.group(2)
            if filename:
                result[filename] = f"https://www.youtube.com/watch?v={yt_id}"
    except Exception:
        pass
    return result
