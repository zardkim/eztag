"""사용자 입력 경로 검증 유틸리티.

README가 권장하는 NAS 설치 방식(`ln -s /volume1/music ./data/library/MyAlbums`)처럼
등록된 루트 **안에 놓인 심볼릭 링크**를 허용하면서도, `..` 를 이용한 디렉터리 탈출은 막는다.

기존 코드는 `Path(path).resolve()` 로 링크를 끝까지 따라간 뒤 루트와 비교했다.
그 결과 링크 대상(`/volume1/music/...`)이 등록된 어떤 루트 아래에도 없어 403이 났다.
"""
import os
from pathlib import Path
from typing import Optional, Union


def safe_path(raw: Union[str, os.PathLike, None]) -> Optional[Path]:
    """사용자가 보낸 경로를 정규화한다. 허용 불가면 None.

    - 절대경로가 아니면 거부
    - `..` 가 하나라도 있으면 거부

      이 조건이 아래 `is_within` 의 어휘적 비교를 안전하게 만드는 핵심이다.
      `..` 를 허용한 채 어휘적으로만 비교하면
      `/music/link/../passwd` 가 `/music/passwd` 로 정규화되어 통과하지만,
      커널은 `link` 를 따라간 뒤 `..` 를 적용하므로 실제로는 루트 밖 파일이 열린다.

    - 심볼릭 링크는 따라가지 않는다. `//` 와 `./` 만 정리한다.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    p = Path(text)
    if not p.is_absolute():
        return None
    if ".." in p.parts:
        return None
    return Path(os.path.normpath(str(p)))


def is_within(p: Path, root: Path) -> bool:
    """`p` 가 `root` 하위이거나 `root` 자신인지 검사.

    1. 어휘적 비교 — 루트 **안에 있는** 심볼릭 링크를 허용한다.
    2. 실패 시 양쪽을 resolve 해서 재비교 — 루트 **자체가** 심볼릭 링크인 경우를 살린다.
    """
    try:
        p.relative_to(root)
        return True
    except ValueError:
        pass
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def same_path(a: Path, b: Path) -> bool:
    """두 경로가 같은 위치를 가리키는지. 어휘적으로 같거나 resolve 결과가 같으면 True."""
    if a == b:
        return True
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def first_root_containing(p: Path, roots) -> Optional[Path]:
    """`p` 를 담고 있는 첫 번째 루트를 반환. 없으면 None."""
    for root in roots:
        if root and is_within(p, root):
            return root
    return None
