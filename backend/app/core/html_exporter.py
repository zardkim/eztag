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


# ── HTML 템플릿 ───────────────────────────────────────────────
_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f8f9fb;
  --surface: #ffffff;
  --border: #e5e7eb;
  --text: #111827;
  --text2: #6b7280;
  --text3: #9ca3af;
  --accent: #3b82f6;
  --row-hover: #f3f4f6;
  --header-from: #e5e7eb;
  --header-to: #f8f9fb;
  --badge-mp3: #fff7ed; --badge-mp3-t: #c2410c;
  --badge-flac: #eff6ff; --badge-flac-t: #1d4ed8;
  --badge-m4a: #faf5ff; --badge-m4a-t: #7c3aed;
  --badge-ogg: #f0fdf4; --badge-ogg-t: #15803d;
  --badge-other: #f3f4f6; --badge-other-t: #374151;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f172a;
    --surface: #1e293b;
    --border: #334155;
    --text: #f1f5f9;
    --text2: #94a3b8;
    --text3: #64748b;
    --accent: #60a5fa;
    --row-hover: #1e293b;
    --header-from: #1e293b;
    --header-to: #0f172a;
    --badge-mp3: #431407; --badge-mp3-t: #fed7aa;
    --badge-flac: #1e3a5f; --badge-flac-t: #bfdbfe;
    --badge-m4a: #3b0764; --badge-m4a-t: #e9d5ff;
    --badge-ogg: #052e16; --badge-ogg-t: #bbf7d0;
    --badge-other: #1f2937; --badge-other-t: #d1d5db;
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}

.page { max-width: 1280px; margin: 0 auto; padding: 24px 16px 60px; }

/* ── 앨범 헤더 ── */
.album-header {
  background: linear-gradient(to bottom, var(--header-from), var(--header-to));
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 28px;
  display: flex;
  gap: 28px;
  align-items: flex-end;
  margin-bottom: 24px;
}
.album-cover {
  width: 160px;
  height: 160px;
  min-width: 160px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  background: var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
}
.album-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.album-info { flex: 1; min-width: 0; }
.album-type { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--text3); margin-bottom: 4px; }
.album-title { font-size: 28px; font-weight: 800; line-height: 1.2; margin-bottom: 6px; word-break: break-word; }
.album-artist { font-size: 15px; color: var(--text2); margin-bottom: 8px; }
.album-meta { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; color: var(--text2); }
.album-meta span::before { content: "· "; }
.album-meta span:first-child::before { content: ""; }
.album-stats { margin-top: 10px; font-size: 12px; color: var(--text3); display: flex; flex-wrap: wrap; gap: 12px; }

/* ── 트랙 테이블 ── */
.section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text3); margin-bottom: 8px; padding-left: 2px; }
.track-table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-bottom: 24px; }
.track-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.track-table thead th { background: var(--bg); padding: 10px 12px; text-align: left; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text3); border-bottom: 1px solid var(--border); white-space: nowrap; }
.track-table thead th.num { text-align: center; width: 40px; }
.track-table thead th.dur { text-align: right; width: 60px; }
.track-table thead th.codec { text-align: center; width: 56px; }
.track-table thead th.br { text-align: center; width: 72px; }
.track-table tbody tr { border-bottom: 1px solid var(--border); transition: background 0.1s; }
.track-table tbody tr:last-child { border-bottom: none; }
.track-table tbody tr:hover { background: var(--row-hover); }
.track-table td { padding: 10px 12px; vertical-align: middle; color: var(--text); }
.track-table td.num { text-align: center; color: var(--text3); font-variant-numeric: tabular-nums; }
.track-table td.dur { text-align: right; color: var(--text3); font-variant-numeric: tabular-nums; font-family: ui-monospace, monospace; font-size: 12px; }
.track-table td.codec { text-align: center; }
.track-table td.br { text-align: center; color: var(--text3); font-size: 12px; }
.track-table .title-cell { font-weight: 600; }
.track-table .artist-cell { color: var(--text2); font-size: 12px; }
.lyrics-badge { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #a855f7; margin-left: 6px; vertical-align: middle; }

/* ── 코덱 뱃지 ── */
.badge { display: inline-block; padding: 2px 6px; border-radius: 5px; font-size: 10px; font-weight: 700; font-family: ui-monospace, monospace; text-transform: uppercase; }
.badge-mp3  { background: var(--badge-mp3);  color: var(--badge-mp3-t); }
.badge-flac { background: var(--badge-flac); color: var(--badge-flac-t); }
.badge-m4a  { background: var(--badge-m4a);  color: var(--badge-m4a-t); }
.badge-ogg  { background: var(--badge-ogg);  color: var(--badge-ogg-t); }
.badge-other{ background: var(--badge-other); color: var(--badge-other-t); }

/* ── 기술 정보 (접기/펼치기) ── */
details { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; margin-bottom: 24px; }
details summary { padding: 12px 16px; cursor: pointer; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text3); user-select: none; }
details summary:hover { background: var(--row-hover); }
.tech-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tech-table tr { border-top: 1px solid var(--border); }
.tech-table td { padding: 8px 16px; vertical-align: top; }
.tech-table td:first-child { color: var(--text3); width: 120px; font-weight: 500; white-space: nowrap; }
.tech-table td:last-child { color: var(--text2); font-family: ui-monospace, monospace; word-break: break-all; font-size: 11px; }

/* ── 타이틀곡 뱃지 ── */
.title-track-badge {
  display: inline-flex; align-items: center;
  background: linear-gradient(135deg, #f97316, #ef4444);
  color: white; font-size: 9px; font-weight: 800;
  letter-spacing: 0.5px; text-transform: uppercase;
  padding: 2px 6px; border-radius: 4px;
  margin-left: 6px; vertical-align: middle; flex-shrink: 0;
}

/* ── YouTube 섹션 ── */
.yt-section { margin-bottom: 24px; }
.yt-embed-wrap {
  position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;
  border-radius: 12px; background: #000;
  box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}
.yt-embed-wrap iframe {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;
}
.yt-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: var(--text3); margin-bottom: 8px;
}
.yt-label svg { color: #ff0000; }

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

/* ── 푸터 ── */
.footer { text-align: center; font-size: 11px; color: var(--text3); padding-top: 20px; border-top: 1px solid var(--border); display: flex; flex-direction: column; align-items: center; gap: 8px; }
.footer a { color: var(--accent); text-decoration: none; }

/* ── 반응형 ── */
@media (max-width: 600px) {
  .album-header { flex-direction: column; align-items: center; text-align: center; padding: 20px; }
  .album-cover { width: 130px; height: 130px; min-width: 130px; }
  .album-title { font-size: 22px; }
  .album-meta { justify-content: center; }
  .album-stats { justify-content: center; }
  .col-artist { display: none; }
  .col-br { display: none; }
}

/* ── 인쇄 최적화 ── */
@media print {
  body { background: white; color: black; }
  .album-header { background: white; border: 1px solid #ddd; }
  .track-table-wrap { break-inside: avoid; }
  details { display: block; }
  details summary::marker { display: none; }
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
    # youtu.be/XXXX or youtube.com/watch?v=XXXX or youtube.com/embed/XXXX
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
) -> str:
    """트랙 목록 + 태그 메타데이터로 자체 완결형 HTML 생성."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    page_title = f"{album_title}" + (f" – {album_artist}" if album_artist else "")
    folder_name = Path(source_path).name if source_path else ""

    # 커버아트
    cover_html = f'<img src="{cover_b64}" alt="cover" />' if cover_b64 else "💿"

    # 앨범 메타 라인
    meta_items = []
    if album_artist:
        meta_items.append(_safe(album_artist))
    if year:
        meta_items.append(_safe(str(year)))
    if genre:
        meta_items.append(_safe(genre))
    if label:
        meta_items.append(_safe(label))
    meta_html = "".join(f"<span>{m}</span>" for m in meta_items)

    # 통계
    total_dur = _total_duration(tracks)
    stats_parts = [f"{len(tracks)}곡"]
    if total_dur:
        stats_parts.append(f"재생시간 {total_dur}")
    stats_html = " · ".join(stats_parts)

    # YouTube 임베드
    yt_html = ""
    yt_id = _extract_youtube_id(youtube_url)
    if yt_id:
        yt_html = f"""
  <!-- 뮤직비디오 -->
  <div class="yt-section">
    <div class="yt-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783 3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088 31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/></svg>
      뮤직비디오
    </div>
    <div class="yt-embed-wrap">
      <iframe src="https://www.youtube.com/embed/{yt_id}" title="뮤직비디오" allowfullscreen loading="lazy"></iframe>
    </div>
  </div>
"""

    # 앨범 소개 섹션
    desc_html = ""
    if description and description.strip():
        desc_escaped = _safe(description).replace("\n", "<br>")
        desc_html = f"""
  <!-- 앨범 소개 -->
  <div class="section-title">앨범 소개</div>
  <div class="desc-box">{desc_escaped}</div>
"""

    # 옵션 컬럼 존재 여부
    has_multi_disc    = True  # 디스크번호 항상 표시
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

    # 테이블 헤더
    th_parts = []
    if has_multi_disc:
        th_parts.append('<th class="col-disc">디스크</th>')
    th_parts.append('<th class="num">트랙</th>')
    th_parts.append('<th>제목</th>')
    th_parts.append('<th class="col-artist">아티스트</th>')
    if has_album_artist_col:
        th_parts.append('<th class="col-aa">앨범아티스트</th>')
    if has_album_col:
        th_parts.append('<th class="col-album">앨범</th>')
    if has_year_col:
        th_parts.append('<th class="col-year">연도</th>')
    if has_genre_col:
        th_parts.append('<th class="col-genre">장르</th>')
    if has_rel_date:
        th_parts.append('<th class="col-rd">발매일</th>')
    if has_isrc:
        th_parts.append('<th class="col-isrc">ISRC</th>')
    if has_comment:
        th_parts.append('<th class="col-comment">설명</th>')
    th_parts.append('<th class="dur">길이</th>')
    if has_bitrate:
        th_parts.append('<th class="col-br">비트레이트</th>')
    if has_samplerate:
        th_parts.append('<th class="col-hz">주파수</th>')
    if has_filesize:
        th_parts.append('<th class="col-size">용량</th>')
    thead_html = "<tr>" + "".join(th_parts) + "</tr>"

    # 트랙 행
    track_rows = []
    for t in tracks:
        disc = t.get("disc_no") or 1
        num  = t.get("track_no")
        num_str  = f"{num:02d}" if num else "—"
        disc_str = str(disc) if has_multi_disc else ""
        lyrics_dot = '<span class="lyrics-badge" title="가사 있음"></span>' if t.get("has_lyrics") else ""
        title_badge = '<span class="title-track-badge">타이틀</span>' if t.get("is_title_track") else ""

        td_parts = []
        if has_multi_disc:
            td_parts.append(f'<td class="col-disc">{disc_str}</td>')
        td_parts += [
            f'<td class="num">{num_str}</td>',
            f'<td><div class="title-cell">{_safe(t.get("title") or "")}{title_badge}{lyrics_dot}</div></td>',
            f'<td class="col-artist">{_safe(t.get("artist") or "")}</td>',
        ]
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
        td_parts.append(f'<td class="dur">{_fmt_duration(t.get("duration"))}</td>')
        if has_bitrate:
            br = t.get("bitrate")
            td_parts.append(f'<td class="col-br">{f"{br}k" if br else "—"}</td>')
        if has_samplerate:
            sr = t.get("sample_rate")
            td_parts.append(f'<td class="col-hz">{f"{sr // 1000}kHz" if sr else "—"}</td>')
        if has_filesize:
            td_parts.append(f'<td class="col-size">{_fmt_size(t.get("file_size"))}</td>')
        track_rows.append("<tr>" + "".join(td_parts) + "</tr>")

    source_note = f'<span style="font-size:10px;color:var(--text3);">{_safe(folder_name)}</span>' if folder_name else ""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="eztag">
<title>{_safe(page_title)}</title>
<style>{_CSS}
.col-disc    {{ text-align: center; width: 52px; color: var(--text3); font-size: 12px; }}
.col-aa      {{ min-width: 100px; color: var(--text2); }}
.col-album   {{ min-width: 120px; color: var(--text2); }}
.col-year    {{ text-align: center; width: 56px; color: var(--text2); font-size: 12px; }}
.col-genre   {{ min-width: 80px; color: var(--text2); font-size: 12px; }}
.col-rd      {{ white-space: nowrap; text-align: center; width: 90px; color: var(--text2); font-size: 12px; }}
.col-isrc    {{ font-family: ui-monospace, monospace; font-size: 11px; color: var(--text2); white-space: nowrap; }}
.col-comment {{ color: var(--text2); font-size: 12px; max-width: 200px; }}
.col-br      {{ text-align: center; width: 80px; color: var(--text3); font-size: 12px; }}
.col-hz      {{ text-align: center; width: 72px; color: var(--text3); font-size: 12px; }}
.col-size    {{ text-align: right; width: 72px; color: var(--text3); font-size: 12px; font-family: ui-monospace, monospace; }}
.desc-box    {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; font-size: 13px; color: var(--text2); line-height: 1.8; white-space: pre-wrap; word-break: break-word; }}
</style>
</head>
<body>
<div class="page">

  <!-- 앨범 헤더 -->
  <div class="album-header">
    <div class="album-cover">{cover_html}</div>
    <div class="album-info">
      <div class="album-type">Album</div>
      <div class="album-title">{_safe(album_title)}</div>
      <div class="album-artist">{_safe(album_artist or '')}</div>
      <div class="album-meta">{meta_html}</div>
      <div class="album-stats">
        {_safe(stats_html)}
        <span style="margin-left:auto;"><span class="eztag-badge">{_logo_svg(16)} eztag</span></span>
      </div>
    </div>
  </div>
{yt_html}{desc_html}
  <!-- 트랙 목록 -->
  <div class="section-title">트랙 목록</div>
  <div class="track-table-wrap">
    <table class="track-table">
      <thead>{thead_html}</thead>
      <tbody>
        {''.join(track_rows)}
      </tbody>
    </table>
  </div>

  <!-- 푸터 -->
  <div class="footer">
    <span class="eztag-badge eztag-badge-lg">{_logo_svg(22)} eztag</span>
    <span>Generated · {now_str}{(' · ' + source_note) if source_note else ''}</span>
  </div>

</div>
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
