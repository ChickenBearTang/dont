"""브랜드 별칭 사전."""

from __future__ import annotations

import json
from pathlib import Path

from .text import compact, find_on_boundaries, tokenize

_DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "brands.json"


class BrandLexicon:
    def __init__(self, aliases: dict[str, list[str]]) -> None:
        self._aliases: dict[str, list[str]] = {}
        for brand, names in aliases.items():
            self._aliases[brand] = sorted({"".join(tokenize(n)) for n in [brand, *names] if tokenize(n)})
        self._owner: dict[str, str] = {}
        for brand, names in self._aliases.items():
            for name in names:
                if name in self._owner and self._owner[name] != brand:
                    raise ValueError(f"brand alias {name!r} belongs to both {self._owner[name]!r} and {brand!r}")
                self._owner[name] = brand

    @classmethod
    def load(cls, path: Path | None = None) -> "BrandLexicon":
        data = json.loads((path or _DEFAULT_PATH).read_text(encoding="utf-8"))
        return cls({k: v for k, v in data.items() if not k.startswith("_")})

    def brands(self) -> list[str]:
        return sorted(self._aliases)

    def aliases_of(self, brand: str) -> list[str]:
        return list(self._aliases.get(brand, []))

    def detect(self, title: str) -> list[str]:
        """제목에 나온 브랜드 ID 들 (등장 순서, 중복 제거). 토큰 경계에서만 일치한다 —
        'ms' 가 'msi' 의 앞부분으로, 'lg' 가 'logitech' 안에서 잡히지 않게."""
        haystack = compact(tokenize(title))
        hits: list[tuple[int, str]] = []
        for alias, brand in self._owner.items():
            for start, _ in find_on_boundaries(haystack, alias):
                hits.append((start, brand))
        ordered: list[str] = []
        for _, brand in sorted(hits):
            if brand not in ordered:
                ordered.append(brand)
        return ordered
