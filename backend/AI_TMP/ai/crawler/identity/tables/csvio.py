"""CSV <-> 테이블 행. DB 없이도(온프레미스 개발, 검수 파일 주고받기) 같은 데이터를 다룬다.

파일 이름과 열 이름은 DB 테이블과 같다. 여러 값을 담는 열은 '|' 로 이어 쓰고, kc_info 는 JSON 문자열이다.
인코딩은 UTF-8(BOM 허용)으로 읽고, 엑셀에서 열기 쉽게 쓸 때는 BOM 을 붙인다.
형식이 깨진 행(숫자가 아닌 priority, 깨진 JSON)은 건너뛰고 Issue 로 알린다.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from .models import (
    AliasRow,
    CatalogRow,
    Issue,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
)

FILES = {
    "catalog": "product_catalog.csv",
    "aliases": "product_aliases.csv",
    "categories": "sourcing_categories.csv",
    "signals": "sourcing_signals.csv",
}
COLUMNS = {
    "catalog": [
        "catalog_id", "brand", "model_code", "display_name", "product_line", "category", "manufacturer", "kc_certified_yn",
        "kc_info", "source", "verified_yn", "requires_brand_yn", "compatible_brands", "benign_suffixes",
    ],
    "aliases": [
        "catalog_id", "alias_text", "alias_kind", "alias_type", "brand_required_yn", "status", "source", "note", "reviewed_by",
    ],
    "categories": ["category_code", "label_ko", "kc_record_expected_yn", "price_pool_yn", "reviewed_yn", "sort_order", "note"],
    "signals": ["category_code", "match_type", "pattern", "priority", "enabled_yn", "note"],
}
_LIST_SEP = "|"


def _cell(row: dict[str, str | None], name: str, default: str = "") -> str:
    value = row.get(name)
    return default if value is None else str(value).strip() or default


def _yn(row: dict[str, str | None], name: str, default: str) -> str:
    return _cell(row, name, default).upper()


def _list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(_LIST_SEP) if part.strip())


def _read_rows(path: Path) -> list[dict[str, str | None]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _catalog(row: dict[str, str | None]) -> CatalogRow:
    raw_info = _cell(row, "kc_info")
    info = json.loads(raw_info) if raw_info else {}
    if not isinstance(info, dict):
        raise ValueError("kc_info 는 JSON 객체여야 한다")
    return CatalogRow(
        catalog_id=_cell(row, "catalog_id"), brand=_cell(row, "brand").lower(), model_code=_cell(row, "model_code"),
        display_name=_cell(row, "display_name") or None, product_line=_cell(row, "product_line"),
        category=_cell(row, "category"), manufacturer=_cell(row, "manufacturer") or None,
        kc_certified_yn=_yn(row, "kc_certified_yn", "U"), kc_info=info, source=_cell(row, "source", "curated"),
        verified_yn=_yn(row, "verified_yn", "N"), requires_brand_yn=_yn(row, "requires_brand_yn", "N"),
        compatible_brands=_list(_cell(row, "compatible_brands")), benign_suffixes=_list(_cell(row, "benign_suffixes")),
    )


def _alias(row: dict[str, str | None]) -> AliasRow:
    return AliasRow(
        catalog_id=_cell(row, "catalog_id"), alias_text=_cell(row, "alias_text"), alias_kind=_cell(row, "alias_kind", "model"),
        alias_type=_cell(row, "alias_type", "other"), brand_required_yn=_yn(row, "brand_required_yn", "N"),
        status=_cell(row, "status", "pending"), source=_cell(row, "source", "curated"), note=_cell(row, "note") or None,
        reviewed_by=_cell(row, "reviewed_by") or None,
    )


def _category(row: dict[str, str | None]) -> SourcingCategoryRow:
    return SourcingCategoryRow(
        category_code=_cell(row, "category_code"), label_ko=_cell(row, "label_ko"),
        kc_record_expected_yn=_yn(row, "kc_record_expected_yn", "U"), price_pool_yn=_yn(row, "price_pool_yn", "N"),
        reviewed_yn=_yn(row, "reviewed_yn", "N"), sort_order=int(_cell(row, "sort_order", "100")), note=_cell(row, "note") or None,
    )


def _signal(row: dict[str, str | None]) -> SourcingSignalRow:
    return SourcingSignalRow(
        category_code=_cell(row, "category_code"), match_type=_cell(row, "match_type"), pattern=_cell(row, "pattern"),
        priority=int(_cell(row, "priority", "100")), enabled_yn=_yn(row, "enabled_yn", "Y"), note=_cell(row, "note") or None,
    )


_PARSERS: dict[str, Callable[[dict[str, str | None]], Any]] = {
    "catalog": _catalog, "aliases": _alias, "categories": _category, "signals": _signal,
}
_TABLE_NAMES = {
    "catalog": "product_catalog", "aliases": "product_aliases", "categories": "sourcing_categories", "signals": "sourcing_signals",
}


def read_tables(directory: Path) -> tuple[ProductTables, list[Issue]]:
    """디렉터리에서 있는 파일만 읽는다 (없는 파일은 빈 표). 파일 이름은 FILES 를 따른다."""
    directory = Path(directory)
    tables = ProductTables()
    issues: list[Issue] = []
    for kind, filename in FILES.items():
        path = directory / filename
        if not path.exists():
            continue
        target: list[Any] = getattr(tables, kind)
        rows = _read_rows(path)
        if rows:
            missing = [c for c in COLUMNS[kind][:1] if c not in rows[0]]
            if missing:
                issues.append(Issue("error", _TABLE_NAMES[kind], filename, "CSV_MISSING_COLUMN", f"필수 열이 없다: {', '.join(missing)}"))
                continue
        for line_no, row in enumerate(rows, start=2):  # 1행은 머리글
            try:
                target.append(_PARSERS[kind](row))
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                issues.append(Issue("error", _TABLE_NAMES[kind], f"{filename}:{line_no}", "CSV_BAD_ROW", str(exc)))
    return tables, issues


def _format(kind: str, row: Any) -> list[str]:
    if kind == "catalog":
        return [
            row.catalog_id, row.brand, row.model_code, row.display_name or "", row.product_line, row.category,
            row.manufacturer or "", row.kc_certified_yn, json.dumps(row.kc_info, ensure_ascii=False) if row.kc_info else "",
            row.source, row.verified_yn, row.requires_brand_yn, _LIST_SEP.join(row.compatible_brands),
            _LIST_SEP.join(row.benign_suffixes),
        ]
    if kind == "aliases":
        return [row.catalog_id, row.alias_text, row.alias_kind, row.alias_type, row.brand_required_yn, row.status, row.source,
                row.note or "", row.reviewed_by or ""]
    if kind == "categories":
        return [row.category_code, row.label_ko, row.kc_record_expected_yn, row.price_pool_yn, row.reviewed_yn,
                str(row.sort_order), row.note or ""]
    return [row.category_code, row.match_type, row.pattern, str(row.priority), row.enabled_yn, row.note or ""]


def write_tables(directory: Path, tables: ProductTables, *, only: Iterable[str] | None = None) -> list[Path]:
    """표마다 CSV 파일 하나. 비어 있는 표도 머리글만 있는 파일로 쓴다."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind, filename in FILES.items():
        if only is not None and kind not in set(only):
            continue
        path = directory / filename
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(COLUMNS[kind])
            for row in getattr(tables, kind):
                writer.writerow(_format(kind, row))
        written.append(path)
    return written
