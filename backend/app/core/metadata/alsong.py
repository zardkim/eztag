"""
알송(AlSong) LRC 가사 가져오기.

흐름:
  1. lyrics.alsong.co.kr SOAP API 호출 (제목 + 아티스트 기반)
  2. XML 파싱 → <strLyric> 추출 (이미 표준 LRC 포맷)
  3. 오디오 파일과 같은 폴더에 {stem}.lrc 저장

알송 API:
  POST http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx
  비공식 SOAP API (인증 불필요, 언제든 차단 가능)

주의: 비공식 API이므로 fallback 용도로만 사용할 것.
"""
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_ALSONG_URL = "http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx"

_HEADERS = {
    "Content-Type": "application/soap+xml; charset=utf-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

_SOAP_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:ns1="ALSongWebServer">
  <SOAP-ENV:Body>
    <ns1:GetResembleLyric2>
      <ns1:stQuery>
        <ns1:strTitle>{title}</ns1:strTitle>
        <ns1:strArtistName>{artist}</ns1:strArtistName>
        <ns1:nCurPage>0</ns1:nCurPage>
      </ns1:stQuery>
    </ns1:GetResembleLyric2>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""


def _escape_xml(text: str) -> str:
    """XML 특수문자 이스케이프."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _fetch_lyric(artist: str, title: str) -> Optional[str]:
    """알송 SOAP API 호출 → LRC 문자열 반환. 실패 시 None."""
    body = _SOAP_TEMPLATE.format(
        title=_escape_xml(title),
        artist=_escape_xml(artist),
    )
    try:
        resp = requests.post(
            _ALSONG_URL,
            data=body.encode("utf-8"),
            headers=_HEADERS,
            timeout=5,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"[alsong] request error: {e}")
        return None

    # XML 파싱 — namespace wildcard로 strLyric 탐색
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.warning(f"[alsong] XML parse error: {e}")
        return None

    lyric_el = root.find(".//{*}strLyric")
    if lyric_el is None or not lyric_el.text:
        logger.debug("[alsong] strLyric not found or empty")
        return None

    lrc = lyric_el.text.strip()

    # <br> 태그 제거 (일부 응답에 포함됨)
    lrc = re.sub(r"<br\s*/?>", "", lrc, flags=re.IGNORECASE)

    # 타임스탬프 없는 경우 (싱크 가사 없음) 제외
    if "[" not in lrc:
        logger.debug("[alsong] no time-sync lyrics")
        return None

    return lrc


def fetch_lrc_for_file(file_path: str, artist: str, title: str) -> dict:
    """단일 오디오 파일에 대한 LRC를 알송에서 가져와 같은 폴더에 저장.

    Returns:
        {
            "status": "ok" | "no_sync" | "not_found" | "error",
            "lrc_path": str | None,
            "message": str | None,
        }
    """
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")

    lrc = _fetch_lyric(artist, title)
    if lrc is None:
        return {"status": "not_found", "lrc_path": None, "message": "트랙을 찾을 수 없습니다"}

    try:
        lrc_path.write_text(lrc, encoding="utf-8")
        logger.info(f"[alsong] saved: {lrc_path}")
        return {"status": "ok", "lrc_path": str(lrc_path), "message": None}
    except Exception as e:
        logger.error(f"[alsong] save error ({lrc_path}): {e}")
        return {"status": "error", "lrc_path": None, "message": str(e)}
