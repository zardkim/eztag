"""파싱된 파일명과 메타데이터 검색 결과의 매칭 점수 계산."""
import re
import unicodedata
from difflib import SequenceMatcher

_FEAT_RE = re.compile(r'\s*(feat\.?|ft\.?|featuring)\s+[^)\]]*', re.IGNORECASE)
_PARENS_RE = re.compile(r'[\(\[\{][^\)\]\}]*[\)\]\}]')
_SPECIAL_RE = re.compile(r'[^\w\s가-힣]')
_SPACES_RE = re.compile(r'\s+')


def normalize(text: str) -> str:
    """비교용 텍스트 정규화 (소문자, feat 제거, 특수문자 제거)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = _FEAT_RE.sub("", text)
    text = _PARENS_RE.sub("", text)
    text = text.lower()
    text = _SPECIAL_RE.sub(" ", text)
    text = _SPACES_RE.sub(" ", text).strip()
    return text


def string_similarity(a: str, b: str) -> float:
    """두 문자열 유사도 0.0~1.0."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def score_match(parsed: dict, candidate: dict, local_duration: float = None) -> float:
    """
    파싱 결과와 후보의 매칭 점수 계산 (0.0 ~ 110.0).
    - 제목 유사도: 최대 60점
    - 아티스트 유사도: 최대 30점 (parsed에 artist가 있을 때)
    - 재생시간 근접도: 최대 20점, 최대 -10점 패널티
    """
    score = 0.0

    title_sim = string_similarity(
        normalize(parsed.get("title", "")),
        normalize(candidate.get("title", ""))
    )
    score += title_sim * 60

    if parsed.get("artist"):
        artist_sim = string_similarity(
            normalize(parsed["artist"]),
            normalize(candidate.get("artist", ""))
        )
        score += artist_sim * 30

    cand_dur = candidate.get("duration")  # seconds
    if local_duration and cand_dur:
        diff = abs(local_duration - float(cand_dur))
        if diff <= 2:
            score += 20
        elif diff <= 5:
            score += 10
        elif diff > 15:
            score -= 10

    return score


def find_best_match(parsed: dict, candidates: list, local_duration: float = None, threshold: float = 70.0):
    """
    후보 목록에서 최적 매칭 선택.
    Returns: (best_candidate | None, score)
    """
    if not candidates:
        return None, 0.0

    scored = [(c, score_match(parsed, c, local_duration)) for c in candidates]
    best_candidate, best_score = max(scored, key=lambda x: x[1])

    if best_score < threshold:
        return None, best_score

    return best_candidate, best_score
