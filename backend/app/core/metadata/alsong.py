"""
알송(AlSong) LRC 가사 가져오기.

흐름:
  1. [1순위] GetLyric8: 파일 MD5 해시 기반 정확 매칭 (2019 프로토콜)
  2. [2순위] GetResembleLyric2: 제목+아티스트 텍스트 검색 (다단계)
       - 1단계: 정규화 제목 + 아티스트
       - 2단계: 정규화 제목만
       - 3단계: 괄호/특수문자 제거 제목만
  3. XML 파싱 → <strLyric> 추출 (이미 표준 LRC 포맷)
  4. 오디오 파일과 같은 폴더에 {stem}.lrc 저장

알송 API:
  POST http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx
  비공식 SOAP API — 2019년 이후 encData 인증 토큰 필요

주의: 비공식 API이므로 fallback 용도로만 사용할 것.
"""
import hashlib
import logging
import re
import socket
import struct
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_ALSONG_URL = "http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx"

# 2019년 프로토콜 변경으로 모든 요청에 필요한 인증 토큰 (foobar2000 플러그인에서 추출)
_ENC_DATA = (
    "8582df6473c019a3186a2974aa1e034ae1b2bbb2e7c99575aadc475fcddd997d7"
    "4bbc1ce3d50b9900282903ee9eb60ae8c5bbf27484441bacb41ecf912840269664"
    "1655ff38c2cbbf3c81396034a883af2d82e0545ec32170bddc7c141208e7255e36"
    "7e5b5ebd81750226856f5405ec3ad7b6f8600c32c2718c4c525bfe34666"
)

# SOAP 1.2 방식 (application/soap+xml)
_HEADERS_HASH = {
    "Content-Type": "application/soap+xml; charset=utf-8",
    "SOAPAction": '"ALSongWebServer/GetLyric8"',
    "User-Agent": "gSOAP/2.7",
}

_HEADERS_SEARCH = {
    "Content-Type": "application/soap+xml; charset=utf-8",
    "SOAPAction": '"ALSongWebServer/GetResembleLyric2"',
    "User-Agent": "gSOAP/2.7",
}

# 해시 기반 정확 매칭 (GetLyric8 — 2019 프로토콜)
_SOAP_HASH_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
  xmlns:ns2="ALSongWebServer/Service1Soap"
  xmlns:ns1="ALSongWebServer"
  xmlns:ns3="ALSongWebServer/Service1Soap12">
  <SOAP-ENV:Body>
    <ns1:GetLyric8>
      <ns1:encData>{enc_data}</ns1:encData>
      <ns1:stQuery>
        <ns1:strChecksum>{checksum}</ns1:strChecksum>
        <ns1:strVersion>2.11</ns1:strVersion>
        <ns1:strMACAddress>{mac}</ns1:strMACAddress>
        <ns1:strIPAddress>{ip}</ns1:strIPAddress>
      </ns1:stQuery>
    </ns1:GetLyric8>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

# 텍스트 검색 (GetResembleLyric2 — encData 추가)
_SOAP_SEARCH_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
  xmlns:ns2="ALSongWebServer/Service1Soap"
  xmlns:ns1="ALSongWebServer"
  xmlns:ns3="ALSongWebServer/Service1Soap12">
  <SOAP-ENV:Body>
    <ns1:GetResembleLyric2>
      <ns1:encData>{enc_data}</ns1:encData>
      <ns1:stQuery>
        <ns1:strTitle>{title}</ns1:strTitle>
        <ns1:strArtistName>{artist}</ns1:strArtistName>
        <ns1:nCurPage>0</ns1:nCurPage>
      </ns1:stQuery>
    </ns1:GetResembleLyric2>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

# 제목에서 제거할 패턴
_TITLE_NOISE_RE = re.compile(
    r"""
    \s*[\(\[\{]                  # 여는 괄호
    [^\)\]\}]{0,40}              # 괄호 안 내용 (최대 40자)
    [\)\]\}]                     # 닫는 괄호
    """,
    re.VERBOSE,
)
_FEAT_RE = re.compile(r"\s+(?:feat\.?|ft\.?|with)\s+.+$", re.IGNORECASE)


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


def _normalize_title(title: str) -> str:
    """검색용 제목 정규화: feat/with 제거, 앞뒤 공백 정리."""
    t = _FEAT_RE.sub("", title)
    return t.strip()


def _strip_brackets(title: str) -> str:
    """괄호 내용 제거 후 정규화."""
    t = _TITLE_NOISE_RE.sub("", title)
    return t.strip()


def _get_mac_address() -> str:
    """MAC 주소 반환 (대문자, 콜론 없음). 예: A1B2C3D4E5F6"""
    mac_int = uuid.getnode()
    return f"{mac_int:012X}"


def _get_local_ip() -> str:
    """로컬 IP 주소 반환. 실패 시 127.0.0.1."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# ──────────────────────────────────────────────
# 해시 계산
# ──────────────────────────────────────────────

def _compute_alsong_hash(file_path: str) -> Optional[str]:
    """오디오 파일의 알송 체크섬(MD5) 계산.

    MP3: ID3v2 태그 건너뛰고 오디오 데이터 163840바이트 해시
    기타: 파일 시작부터 163840바이트 해시
    """
    try:
        ext = Path(file_path).suffix.lower()
        with open(file_path, "rb") as f:
            raw = f.read(1024 * 1024 * 10)  # 최대 10MB 읽기

        offset = 0

        if ext == ".mp3":
            # ID3v2 태그 건너뛰기
            if raw[:3] == b"ID3":
                flags = raw[5] if len(raw) > 5 else 0
                if len(raw) >= 10:
                    sb = raw[6:10]
                    size = 0
                    for b in sb:
                        size = (size << 7) | (b & 0x7F)
                    offset = 10 + size
                    # Extended header?
                    if flags & 0x40 and len(raw) > offset + 4:
                        ext_size = struct.unpack(">I", raw[offset:offset + 4])[0]
                        offset += ext_size + 4

        audio_chunk = raw[offset:offset + 163840]
        if len(audio_chunk) < 1024:
            return None

        return hashlib.md5(audio_chunk).hexdigest()

    except Exception as e:
        logger.debug(f"[alsong] hash compute error: {e}")
        return None


# ──────────────────────────────────────────────
# API 호출
# ──────────────────────────────────────────────

def _post_soap(body: str, headers: dict) -> Optional[bytes]:
    """알송 SOAP 요청 → 응답 bytes 반환. 네트워크 오류 시 None.

    HTTP 500도 Fault 본문을 반환할 수 있으므로 raise_for_status() 하지 않음.
    각 호출자가 Fault 여부를 직접 판단한다.
    """
    try:
        resp = requests.post(
            _ALSONG_URL,
            data=body.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        return resp.content
    except Exception as e:
        logger.warning(f"[alsong] request error: {e}")
        return None


def _extract_lyric_from_xml(content: bytes) -> Optional[str]:
    """XML 응답에서 첫 번째 유효한 싱크 가사 추출."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning(f"[alsong] XML parse error: {e}")
        return None

    lyric_el = root.find(".//{*}strLyric")
    if lyric_el is None or not lyric_el.text:
        return None

    lrc = lyric_el.text.strip()
    lrc = re.sub(r"<br\s*/?>", "", lrc, flags=re.IGNORECASE)

    if "[" not in lrc:
        logger.debug("[alsong] no time-sync lyrics")
        return None

    return lrc


def _fetch_lyric_by_hash(checksum: str) -> Optional[str]:
    """파일 해시로 알송 LRC 조회 (GetLyric8 — 2019 프로토콜)."""
    mac = _get_mac_address()
    ip = _get_local_ip()
    body = _SOAP_HASH_TEMPLATE.format(
        enc_data=_ENC_DATA,
        checksum=checksum,
        mac=mac,
        ip=ip,
    )
    content = _post_soap(body, _HEADERS_HASH)
    if content is None:
        return None

    # 해시 미매칭시 Fault 반환
    if b"Fault" in content:
        return None

    return _extract_lyric_from_xml(content)


def _fetch_lyric_by_text(title: str, artist: str) -> Optional[str]:
    """제목+아티스트 텍스트 검색 (GetResembleLyric2) — 다단계 시도."""
    candidates = []

    norm_title = _normalize_title(title)
    stripped_title = _strip_brackets(norm_title)

    # 1단계: 정규화 제목 + 아티스트
    if artist:
        candidates.append((norm_title, artist))
    # 2단계: 정규화 제목만
    candidates.append((norm_title, ""))
    # 3단계: 괄호 제거 제목 (원본과 다를 때만)
    if stripped_title and stripped_title != norm_title:
        candidates.append((stripped_title, ""))

    for t, a in candidates:
        if not t:
            continue
        body = _SOAP_SEARCH_TEMPLATE.format(
            enc_data=_ENC_DATA,
            title=_escape_xml(t),
            artist=_escape_xml(a),
        )
        content = _post_soap(body, _HEADERS_SEARCH)
        if content is None:
            continue

        lrc = _extract_lyric_from_xml(content)
        if lrc:
            logger.debug(f"[alsong] text search hit: title={t!r} artist={a!r}")
            return lrc

    return None


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def fetch_lrc_for_file(file_path: str, artist: str, title: str) -> dict:
    """단일 오디오 파일에 대한 LRC를 알송에서 가져와 같은 폴더에 저장.

    검색 순서:
      1. 파일 해시 기반 GetLyric8 (정확 매칭 — 2019 프로토콜)
      2. 텍스트 검색 GetResembleLyric2 (다단계: 정규화 제목+아티스트 → 제목만 → 괄호제거)

    Returns:
        {
            "status": "ok" | "no_sync" | "not_found" | "error",
            "lrc_path": str | None,
            "message": str | None,
        }
    """
    p = Path(file_path)
    lrc_path = p.with_suffix(".lrc")

    lrc = None

    # 1순위: 해시 기반 정확 매칭
    checksum = _compute_alsong_hash(file_path)
    if checksum:
        logger.debug(f"[alsong] hash={checksum}, trying GetLyric8")
        lrc = _fetch_lyric_by_hash(checksum)
        if lrc:
            logger.info(f"[alsong] hash match: {p.name}")

    # 2순위: 텍스트 검색 (해시 미매칭 또는 해시 계산 실패 시)
    if lrc is None and title:
        logger.debug(f"[alsong] hash miss, trying text search: title={title!r} artist={artist!r}")
        lrc = _fetch_lyric_by_text(title, artist)

    if lrc is None:
        return {"status": "not_found", "lrc_path": None, "message": "트랙을 찾을 수 없습니다"}

    try:
        lrc_path.write_text(lrc, encoding="utf-8")
        logger.info(f"[alsong] saved: {lrc_path}")
        return {"status": "ok", "lrc_path": str(lrc_path), "message": None}
    except Exception as e:
        logger.error(f"[alsong] save error ({lrc_path}): {e}")
        return {"status": "error", "lrc_path": None, "message": str(e)}
