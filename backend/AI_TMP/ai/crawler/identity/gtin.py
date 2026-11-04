"""GTIN(바코드) 검증.

GTIN-8/12/13/14 는 마지막 자리가 체크 숫자다 (GS1 mod-10). 체크 숫자가 맞지 않는 숫자열은
바코드가 아니라 가격, 전화번호, 글 번호일 가능성이 높으므로 상품 식별자로 쓰지 않는다.
"""

from __future__ import annotations

import re

_VALID_LENGTHS = (8, 12, 13, 14)
_DIGIT_RUN = re.compile(r"(?<!\d)\d{8,14}(?!\d)")


def is_valid_gtin(value: object) -> bool:
    if not isinstance(value, str):
        return False
    digits = value.strip()
    if not digits.isdigit() or len(digits) not in _VALID_LENGTHS or digits == "0" * len(digits):
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def normalize_gtin(value: object) -> str | None:
    """하이픈/공백을 지우고 14자리로 맞춘다. 체크 숫자가 틀리면 None."""
    if not isinstance(value, str):
        return None
    digits = re.sub(r"[\s-]", "", value)
    return digits.zfill(14) if is_valid_gtin(digits) else None


def find_gtins(text: str) -> list[str]:
    """글 속에서 체크 숫자가 맞는 GTIN 만 찾는다 (정규화된 14자리)."""
    found: list[str] = []
    for match in _DIGIT_RUN.finditer(text or ""):
        normalized = normalize_gtin(match.group(0))
        if normalized and normalized not in found:
            found.append(normalized)
    return found
