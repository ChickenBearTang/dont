"""테이블(카탈로그 행 + 별칭 행)을 Catalog 에 얹는다.

  1. 테이블의 카탈로그 행을 항목으로 더한다. 파일 카탈로그에 같은 id 가 있으면 테이블이 대체한다: 테이블이
     맨 위 층이라서, DB 에서 고친 값(requires_brand_yn, 별칭 승인/거절 ...)이 시드 JSON 보다 우선해야 한다.
     대체하는 항목은 파일 항목의 인라인 별칭을 이어받지 않는다. 별칭은 테이블에서만 온다(가져오기가 인라인 별칭도
     별칭 행으로 옮겨 놓으므로 DB 에서 거절한 별칭이 파일 때문에 되살아나지 않는다).
  2. 승인된(approved) 별칭만 그 상품의 이름으로 붙인다.
       alias_kind=model -> 정확한 이름(aliases)   alias_kind=line -> 제품군 이름(line_aliases, 후보로만 쓰임)
       brand_required_yn=Y -> 제목에 브랜드가 있을 때만 이 이름을 인정(gated_codes)
  3. 충돌하는 별칭(다른 상품의 코드/이름과 같음, 여러 상품이 주장)은 붙이지 않고 Issue 로 알린다.
     Catalog 는 같은 표기를 두 상품이 갖는 것을 오류로 막으므로, 걸러서 넘기지 않으면 한 줄 때문에 전체가 안 읽힌다.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from ..catalog import Catalog, CatalogEntry
from ..text import compact_code
from .models import AliasRow, CatalogRow, Issue, ProductTables
from .validate import clean_aliases, clean_catalog


def entry_from_row(row: CatalogRow) -> CatalogEntry:
    return CatalogEntry(
        id=row.catalog_id, brand=row.brand, line=row.product_line, model=row.model_code, category=row.category,
        verified=row.verified_yn == "Y", compatible_brands=row.compatible_brands, benign_suffixes=row.benign_suffixes,
        requires_brand=row.requires_brand_yn == "Y", source=row.source, kc=row.kc_info or None,
        kc_certified=row.kc_certified_yn,
    )


def row_from_entry(entry: dict[str, Any]) -> CatalogRow:
    """카탈로그 JSON 항목(kc_import 출력, catalog_seed.json) -> 테이블 행."""
    source = str(entry.get("source", "seed"))
    kc = entry.get("kc")
    return CatalogRow(
        catalog_id=entry["id"], brand=entry["brand"], model_code=entry["model"], display_name=None,
        product_line=entry.get("line", ""), category=entry.get("category", ""),
        manufacturer=", ".join((kc or {}).get("manufacturers", [])) or None,
        kc_certified_yn="Y" if source == "kc" or kc else "U", kc_info=dict(kc) if kc else {},
        source=source if source in ("kc", "curated", "seed", "import_only") else "seed",
        verified_yn="Y" if entry.get("verified") else "N", requires_brand_yn="Y" if entry.get("requires_brand") else "N",
        compatible_brands=tuple(entry.get("compatible_brands", ())), benign_suffixes=tuple(entry.get("benign_suffixes", ())),
    )


def apply_tables(catalog: Catalog, tables: ProductTables) -> tuple[Catalog, list[Issue]]:
    """catalog 에 tables 를 얹은 새 Catalog 와 문제 목록을 돌려준다. catalog 자체는 바꾸지 않는다.

    순서가 중요하다: 카탈로그 행으로 항목을 먼저 더하거나 대체하고, 그 결과의 표기를 기준으로 별칭을 검사한다.
    대체되는 항목이 쓰던 옛 표기(모델 코드, 인라인 별칭)와 별칭을 비교하면 이미 사라진 것과 충돌한다고 오판한다.
    """
    issues: list[Issue] = []
    rows, catalog_issues = clean_catalog(tables.catalog)
    issues += catalog_issues

    entries: dict[str, CatalogEntry] = {e.id: e for e in catalog.entries}
    reserved: dict[str, str] = {}
    for entry in entries.values():
        for code in entry.codes:
            reserved.setdefault(code, entry.id)

    for row in rows:
        entry = entry_from_row(row)
        others = {code: owner for code, owner in reserved.items() if owner != row.catalog_id}
        clash = next((others[c] for c in entry.codes if c in others), None)
        if clash is not None:
            issues.append(Issue("error", "product_catalog", row.catalog_id, "CATALOG_CODE_CLASH", f"모델 코드가 {clash} 와 같아 쓰지 않는다"))
            continue
        for code in [c for c, owner in reserved.items() if owner == row.catalog_id]:
            del reserved[code]  # 대체되는 항목이 쓰던 표기는 비운다
        entries[row.catalog_id] = entry
        for code in entry.codes:
            reserved[code] = row.catalog_id

    # 별칭: 승인된 것만 붙인다. 충돌하는 것은 clean_aliases 가 걸러 낸다.
    models = {compact_code(e.model): e.id for e in entries.values() if compact_code(e.model)}
    aliases, alias_issues = clean_aliases(tables.aliases, known_ids=set(entries), reserved_codes=reserved, model_codes=models)
    issues += alias_issues
    additions: dict[str, dict[str, Any]] = {}
    for alias in aliases:
        if alias.status != "approved":
            continue
        norm = alias.alias_norm
        slot = additions.setdefault(alias.catalog_id, {"model": [], "line": [], "gated": set(), "types": {}})
        if alias.alias_kind == "line":
            slot["line"].append(alias.alias_text)
        else:
            slot["model"].append(alias.alias_text)
            slot["types"][norm] = alias.alias_type
        if alias.brand_required_yn == "Y":
            slot["gated"].add(norm)

    for catalog_id, slot in additions.items():
        entry = entries[catalog_id]
        entries[catalog_id] = dataclasses.replace(
            entry,
            aliases=tuple(dict.fromkeys([*entry.aliases, *slot["model"]])),
            line_aliases=tuple(dict.fromkeys([*entry.line_aliases, *slot["line"]])),
            gated_codes=entry.gated_codes | frozenset(slot["gated"]),
            code_types=tuple(sorted({**dict(entry.code_types), **slot["types"]}.items())),
        )

    merged = Catalog(list(entries.values()))
    merged.skipped = list(catalog.skipped)
    merged.issues = issues
    return merged, issues


def tables_from_catalog_entries(entries: list[dict[str, Any]], *, alias_status: str = "approved") -> ProductTables:
    """카탈로그 JSON 항목들(시드, KC 가져오기 결과)을 테이블 행으로 옮긴다: 항목 -> 카탈로그 행, 인라인 별칭 -> 별칭 행.

    DB 의 별칭 행은 외래키로 카탈로그 행을 가리키므로, JSON 에만 있는 상품에 별칭을 붙이려면 먼저 이렇게 옮겨야 한다.
    """
    return ProductTables(
        catalog=[row_from_entry(e) for e in entries], aliases=alias_rows_from_entries(entries, status=alias_status),
    )


def alias_rows_from_entries(entries: list[dict[str, Any]], *, status: str = "approved") -> list[AliasRow]:
    """카탈로그 JSON 항목의 인라인 별칭 -> 별칭 행. KC 가져오기의 파생모델은 kc_derived, 그 밖은 other."""
    rows: list[AliasRow] = []
    for entry in entries:
        kind = "kc_derived" if entry.get("source") == "kc" else "other"
        source = "kc" if entry.get("source") == "kc" else "curated"
        for alias in entry.get("aliases", ()):
            if compact_code(alias):
                rows.append(AliasRow(entry["id"], alias, "model", kind, "N", status, source))
        for alias in entry.get("line_aliases", ()):
            if compact_code(alias):
                rows.append(AliasRow(entry["id"], alias, "line", "other", "N", status, source))
    return rows

