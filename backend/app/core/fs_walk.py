"""심볼릭 링크를 따라가는 안전한 디렉터리 순회."""
import os
from typing import Iterator, Set, Tuple


def walk_dirs(root: str, excluded: Set[str]) -> Iterator[Tuple[str, list, list]]:
    """`os.walk` 와 같은 (경로, 하위폴더, 파일) 튜플을 내보내되 심볼릭 링크를 따라간다.

    `os.walk` 의 `followlinks` 기본값은 False 다. 그래서 README 가 권장하는
    NAS 구성(`ln -s /volume1/music ./data/library/MyAlbums`)에서 재귀 보기가
    링크 안으로 들어가지 못하고 빈 결과를 냈다.

    `followlinks=True` 만 켜면 링크가 자기 조상을 가리킬 때 무한히 순회한다.
    방문한 디렉터리의 (st_dev, st_ino) 를 기억해 두 번째 방문에서 가지를 잘라
    순환과 중복 순회를 함께 막는다.

    숨김 폴더(`.`)와 제외 목록(`excluded_folders` 설정)은 여기서 걸러낸다.
    호출부는 `dirs[:]` 를 다시 손볼 필요가 없다.
    """
    seen: Set[Tuple[int, int]] = set()

    for cur, dirs, files in os.walk(root, followlinks=True):
        try:
            st = os.stat(cur)
            key = (st.st_dev, st.st_ino)
        except OSError:
            dirs[:] = []
            continue

        if key in seen:
            # 이미 지나온 디렉터리 — 링크가 만든 순환이거나 중복 경로다
            dirs[:] = []
            continue
        seen.add(key)

        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in excluded)
        yield cur, dirs, files
