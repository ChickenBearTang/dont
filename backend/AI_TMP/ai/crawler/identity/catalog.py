"""상품 카탈로그와 '버전을 구분하는' 매칭.

매칭 규칙
  1. 비교는 정확히 한다. 공백/하이픈/대소문자만 무시하고, 숫자가 들어간 토큰은 유사도로
     맞추지 않는다 (MX Master 3S 와 MX Master 4 는 다른 상품).
  2. 일치는 토큰 경계에서 시작하고 끝나야 한다.
  3. 더 긴 일치가 이긴다 (RTX 4070 SUPER 가 있으면 그 안의 RTX 4070 은 버린다).
  4. 같은 line 이 제목에 있는데 버전을 가리는 토큰이 없으면 추측하지 않고 후보를 돌려준다.
  5. 제목에 서로 다른 상품이 둘 이상이면 묶음으로 보고 고르지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from .text import compact, compact_code, find_on_boundaries, tokenize

_DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "catalog_seed.json"


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    brand: str
    line: str
    model: str
    category: str
    aliases: tuple[str, ...] = ()
    line_aliases: tuple[str, ...] = ()
    verified: bool = False
    # 제목에 이 브랜드가 있어도 이 상품으로 본다 (그래픽카드: 칩은 NVIDIA, 제목은 'MSI 벤투스').
    compatible_brands: tuple[str, ...] = ()
    # 이 상품의 모델명 뒤에 붙어도 상품을 바꾸지 않는 말 (그래픽카드 파트너 제품명 TUF/Ventus/OC ...).
    benign_suffixes: tuple[str, ...] = ()

    def sold_under(self, brands: list[str] | None) -> bool:
        """제목의 브랜드가 이 상품과 양립하는가. 브랜드를 모르면 True."""
        if not brands:
            return True
        return self.brand in brands or any(b in brands for b in self.compatible_brands)

    @property
    def codes(self) -> tuple[str, ...]:
        """이 상품을 가리키는 모든 표기 (compact_code 형태, 긴 것부터)."""
        found = {compact_code(self.model), *(compact_code(a) for a in self.aliases)}
        return tuple(sorted((c for c in found if c), key=lambda c: (-len(c), c)))

    @property
    def line_codes(self) -> tuple[str, ...]:
        return tuple(c for c in {compact_code(self.line), *(compact_code(a) for a in self.line_aliases)} if c)


@dataclass(frozen=True)
class CatalogMatch:
    status: str  # "match" | "ambiguous_variant" | "multiple_products" | "none"
    entry: CatalogEntry | None = None
    candidates: tuple[CatalogEntry, ...] = ()
    matched_code: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)
    following: tuple[str, ...] = ()  # 일치한 모델명 바로 뒤의 토큰들 (최대 4개)


class Catalog:
    def __init__(self, entries: list[CatalogEntry]) -> None:
        ids = [e.id for e in entries]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate catalog ids")
        owners: dict[str, str] = {}
        for entry in entries:
            for code in entry.codes:
                if code in owners and owners[code] != entry.id:
                    raise ValueError(f"code {code!r} is claimed by both {owners[code]} and {entry.id}")
                owners[code] = entry.id
        self._entries = entries
        self._by_id = {e.id: e for e in entries}

    @classmethod
    def load(cls, path: Path | None = None) -> "Catalog":
        data = json.loads((path or _DEFAULT_PATH).read_text(encoding="utf-8"))
        entries = [
            CatalogEntry(
                id=p["id"], brand=p["brand"], line=p.get("line", ""), model=p["model"], category=p.get("category", ""),
                aliases=tuple(p.get("aliases", ())), line_aliases=tuple(p.get("line_aliases", ())),
                verified=bool(p.get("verified", False)),
                compatible_brands=tuple(p.get("compatible_brands", ())),
                benign_suffixes=tuple(p.get("benign_suffixes", ())),
            )
            for p in data["products"]
        ]
        return cls(entries)

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, entry_id: str) -> CatalogEntry | None:
        return self._by_id.get(entry_id)

    def match(self, title: str, *, brands: list[str] | None = None) -> CatalogMatch:
        """brands: 제목에서 찾은 브랜드 ID. 주어지면 그 브랜드 상품만 후보로 한다."""
        tokens = tokenize(title)
        haystack = compact(tokens)
        pool = [e for e in self._entries if e.sold_under(brands)]

        hits: list[tuple[int, int, CatalogEntry, str]] = []  # (start, end, entry, code)
        for entry in pool:
            for code in entry.codes:
                for start, end in find_on_boundaries(haystack, code):
                    hits.append((start, end, entry, code))

        # 더 긴 일치 안에 완전히 들어가는 일치는 버린다.
        kept = [
            h for h in hits
            if not any((o[0] <= h[0] and h[1] <= o[1]) and (o[1] - o[0]) > (h[1] - h[0]) for o in hits)
        ]
        distinct = {h[2].id: h for h in kept}
        if len(distinct) == 1:
            _, end, entry, code = next(iter(distinct.values()))
            ordered = sorted(haystack[1])
            token_index = ordered.index(end)  # end 는 토큰 경계이므로 항상 있다
            following = tuple(tokens[token_index: token_index + 4])
            return CatalogMatch("match", entry, (entry,), code, (f"catalog code '{code}'",), following)
        if len(distinct) > 1:
            entries = tuple(h[2] for h in distinct.values())
            return CatalogMatch("multiple_products", None, entries, "", ("title mentions several catalog products",))

        # 완전한 모델 일치가 없다. 같은 line 만 있고 버전을 가리는 토큰이 없는 경우.
        line_candidates: dict[str, CatalogEntry] = {}
        for entry in pool:
            if any(find_on_boundaries(haystack, lc) for lc in entry.line_codes):
                line_candidates[entry.id] = entry
        if len(line_candidates) > 1:
            return CatalogMatch(
                "ambiguous_variant", None, tuple(line_candidates.values()), "",
                ("line matched but no version token distinguishes the model",),
            )
        return CatalogMatch("none")
