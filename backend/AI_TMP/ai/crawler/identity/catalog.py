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
from typing import Any

from .text import compact, compact_code, tokenize

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
    # True 면 제목에 이 상품의 브랜드가 있을 때만 맞춘다. 짧거나 흔한 코드(K2, A1234)가 다른 글의
    # 숫자/문자와 우연히 일치하는 것을 막는다. KC 인증 DB 에서 가져온 항목은 대개 True 다.
    requires_brand: bool = False
    source: str = "seed"  # "seed"(손으로 쓴 예시) | "kc"(공공 인증 DB) | "curated"(검수)
    kc: Any = None  # KC 인증 정보 (인증/관리번호, 제조자, 기자재명칭 ...)
    # 인증 DB 에 기록이 있는가: "Y" | "N" | "U"(확인 안 함). 유통경로 규칙(kc_record_expected_yn)과 짝을 이룬다.
    kc_certified: str = "U"
    # 이 표기(compact_code)는 제목에 브랜드가 있을 때만 인정한다. 짧거나 통칭인 이름("마스터 3S")이
    # 다른 브랜드의 글에서 우연히 맞는 것을 막는다. 항목 전체를 막는 requires_brand 와 달리 이름 하나만 막는다.
    gated_codes: frozenset[str] = frozenset()
    # 별칭 표기 -> 별칭 종류(별칭 테이블의 alias_type). 어떤 이름으로 맞았는지 근거에 남기는 데 쓴다.
    code_types: tuple[tuple[str, str], ...] = ()

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

    def code_type(self, code: str) -> str | None:
        return dict(self.code_types).get(code)

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


def _token_spans(tokens: list[str], max_len: int):
    """토큰 경계에서 시작하고 끝나는 모든 구간 (시작, 끝, 이어 붙인 문자열). 길이는 max_len 까지."""
    offsets = [0]
    for token in tokens:
        offsets.append(offsets[-1] + len(token))
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens) + 1):
            if offsets[j] - offsets[i] > max_len:
                break
            yield offsets[i], offsets[j], "".join(tokens[i:j])


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
        self.skipped: list[tuple[str, str]] = []  # load_many 가 건너뛴 항목 (id, 이유)
        self.issues: list[Any] = []  # 테이블(별칭/카탈로그 행)을 얹을 때 걸러진 행과 이유 (tables.Issue)
        self._by_id = {e.id: e for e in entries}
        # 색인: 표기(compact_code) -> 항목들. 제목은 토큰 구간을 이어 붙인 문자열로 조회한다.
        # 전수 탐색(항목 수 x 표기 수)을 제목 길이에 비례하는 조회로 바꿔 수십만 건에서도 빠르다.
        self._code_index: dict[str, list[CatalogEntry]] = {}
        self._line_index: dict[str, list[CatalogEntry]] = {}
        for entry in entries:
            for code in entry.codes:
                self._code_index.setdefault(code, []).append(entry)
            for line_code in entry.line_codes:
                self._line_index.setdefault(line_code, []).append(entry)
        self._max_code_len = max((len(c) for c in self._code_index), default=0)
        self._max_line_len = max((len(c) for c in self._line_index), default=0)

    @classmethod
    def load(cls, path: Path | None = None) -> "Catalog":
        return cls(cls._read_entries(path or _DEFAULT_PATH))

    @classmethod
    def load_many(cls, paths: list[Path]) -> "Catalog":
        """여러 카탈로그 파일을 읽는다. 앞선 파일이 우선한다(검수본 -> KC 순으로 준다).

        뒤 파일의 항목이 이미 있는 id 이거나 앞 항목과 같은 표기(코드)를 쓰면 그 항목만 건너뛰고
        catalog.skipped 에 이유와 함께 남긴다. 충돌을 조용히 덮어쓰지도, 전체를 멈추지도 않는다.
        """
        merged: list[CatalogEntry] = []
        seen_ids: set[str] = set()
        code_owner: dict[str, str] = {}
        skipped: list[tuple[str, str]] = []
        for path in paths:
            for entry in cls._read_entries(Path(path)):
                if entry.id in seen_ids:
                    skipped.append((entry.id, f"duplicate id (already loaded before {Path(path).name})"))
                    continue
                clash = next((c for c in entry.codes if c in code_owner and code_owner[c] != entry.id), None)
                if clash is not None:
                    skipped.append((entry.id, f"same code {clash!r} as {code_owner[clash]}"))
                    continue
                seen_ids.add(entry.id)
                for code in entry.codes:
                    code_owner[code] = entry.id
                merged.append(entry)
        catalog = cls(merged)
        catalog.skipped = skipped
        return catalog

    @classmethod
    def load_default(cls, tables: Any = None) -> "Catalog":
        """시드 카탈로그 + AI_PRODUCT_CATALOG_PATHS(os.pathsep 로 구분)의 추가 파일들, 그 위에 별칭/카탈로그 테이블.

        추가 파일은 시드보다 뒤에 읽으므로 시드(검수한 항목)가 우선한다. 테이블(tables.loader 가 환경변수로
        정한 곳: DB, CSV 디렉터리, 패키지 초기 파일)은 맨 위에 얹는다: 승인된 별칭이 항목에 붙고, 아직 없는
        상품이 더해진다. tables 를 주면 그것을 쓴다(이미 읽은 것을 재사용할 때).
        """
        import os

        from .tables.loader import load_default_tables
        from .tables.overlay import apply_tables

        extra = [Path(p) for p in os.getenv("AI_PRODUCT_CATALOG_PATHS", "").split(os.pathsep) if p.strip()]
        base = cls.load_many([_DEFAULT_PATH, *extra]) if extra else cls.load()
        if tables is None:
            tables, _, _ = load_default_tables()
        merged, _ = apply_tables(base, tables)
        return merged

    @staticmethod
    def _read_entries(path: Path) -> list["CatalogEntry"]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = [
            CatalogEntry(
                id=p["id"], brand=p["brand"], line=p.get("line", ""), model=p["model"], category=p.get("category", ""),
                aliases=tuple(p.get("aliases", ())), line_aliases=tuple(p.get("line_aliases", ())),
                verified=bool(p.get("verified", False)),
                compatible_brands=tuple(p.get("compatible_brands", ())),
                benign_suffixes=tuple(p.get("benign_suffixes", ())),
                requires_brand=bool(p.get("requires_brand", False)),
                source=str(p.get("source", "seed")),
                kc=p.get("kc"),
            )
            for p in data["products"]
        ]
        return entries

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> tuple[CatalogEntry, ...]:
        return tuple(self._entries)

    def get(self, entry_id: str) -> CatalogEntry | None:
        return self._by_id.get(entry_id)

    def match(self, title: str, *, brands: list[str] | None = None) -> CatalogMatch:
        """brands: 제목에서 찾은 브랜드 ID. 주어지면 그 브랜드 상품만 후보로 한다."""
        tokens = tokenize(title)
        haystack = compact(tokens)
        brand_known = bool(brands)

        def eligible(entry: CatalogEntry, code: str) -> bool:
            if (entry.requires_brand or code in entry.gated_codes) and not brand_known:
                return False
            return entry.sold_under(brands)

        spans = list(_token_spans(tokens, self._max_code_len))
        hits: list[tuple[int, int, CatalogEntry, str]] = []  # (start, end, entry, code)
        for start, end, text in spans:
            for entry in self._code_index.get(text, ()):
                if eligible(entry, text):
                    hits.append((start, end, entry, text))

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
            kind = entry.code_type(code)
            note = f"catalog code '{code}'" + (f" (alias: {kind})" if kind else "")
            return CatalogMatch("match", entry, (entry,), code, (note,), following)
        if len(distinct) > 1:
            entries = tuple(h[2] for h in distinct.values())
            return CatalogMatch("multiple_products", None, entries, "", ("title mentions several catalog products",))

        # 완전한 모델 일치가 없다. 같은 line 만 있고 버전을 가리는 토큰이 없는 경우.
        line_candidates: dict[str, CatalogEntry] = {}
        for _, _, text in _token_spans(tokens, self._max_line_len):
            for entry in self._line_index.get(text, ()):
                if eligible(entry, text):
                    line_candidates[entry.id] = entry
        if len(line_candidates) > 1:
            return CatalogMatch(
                "ambiguous_variant", None, tuple(line_candidates.values()), "",
                ("line matched but no version token distinguishes the model",),
            )
        return CatalogMatch("none")
