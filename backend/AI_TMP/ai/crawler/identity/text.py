"""제목 문자열 정규화와 '토큰 경계가 있는' 부분 문자열 찾기.

모델명 비교의 핵심 규칙: 숫자가 들어간 토큰은 유사도로 맞추지 않는다. "MX Master 3S" 와
"MX Master 4", "G304" 와 "G305" 는 한 글자 차이라서 편집 거리로는 같은 상품처럼 보인다.
여기서는 공백/하이픈/대소문자만 무시하고 글자를 그대로 비교하며, 일치는 반드시 토큰 경계에서
시작하고 끝나야 한다 ('3s' 가 '3sfoo' 의 앞부분과 일치하는 것을 막는다).
"""

from __future__ import annotations

import re
import unicodedata

_TOKEN = re.compile(r"[a-z0-9]+|[가-힣]+")


def tokenize(text: str) -> list[str]:
    """소문자 영숫자 덩어리와 한글 덩어리로 나눈다. '3S무선' -> ['3s', '무선']."""
    return _TOKEN.findall(unicodedata.normalize("NFKC", str(text)).lower())


def compact(tokens: list[str]) -> tuple[str, set[int]]:
    """토큰을 이어 붙인 문자열과, 토큰 경계가 되는 위치(0 포함) 집합."""
    boundaries = {0}
    total = 0
    parts: list[str] = []
    for token in tokens:
        parts.append(token)
        total += len(token)
        boundaries.add(total)
    return "".join(parts), boundaries


def compact_code(text: str) -> str:
    """모델 코드 비교용: 'MX Master 3S' / 'mx-master-3s' -> 'mxmaster3s'."""
    return "".join(tokenize(text))


def find_on_boundaries(haystack: tuple[str, set[int]], needle: str) -> list[tuple[int, int]]:
    """needle(compact_code 형태)이 토큰 경계에서 시작하고 끝나는 모든 위치 (start, end)."""
    text, boundaries = haystack
    if not needle:
        return []
    spans: list[tuple[int, int]] = []
    start = text.find(needle)
    while start != -1:
        end = start + len(needle)
        if start in boundaries and end in boundaries:
            spans.append((start, end))
        start = text.find(needle, start + 1)
    return spans
