"""PostgreSQL 에서 테이블을 읽고 쓴다 (sql/product_tables_v1.sql).

쓰기는 이 모듈의 고정된 INSERT 문뿐이다. 기본은 '없는 행만 넣는다'(ON CONFLICT DO NOTHING)라서,
사람이 DB 에서 고친 별칭/규칙을 다시 가져오기가 덮어쓰지 않는다. 덮어쓰려면 update=True 를 명시한다.
가져오기 전에 validate.clean_tables 로 걸러서, 틀린 행은 DB 에 들어가지 않는다. 한 번의 가져오기는
한 트랜잭션이라 도중에 실패하면 아무것도 바뀌지 않는다.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable

from .models import (
    AliasRow,
    CatalogRow,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
)
from .validate import clean_tables

Connector = Callable[[str], Any]
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "product_tables_v1.sql"


def _connect(dsn: str, connector: Connector | None) -> Any:
    if connector is not None:
        return connector(dsn)
    try:
        return importlib.import_module("psycopg").connect(dsn)
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg package is required to use the product tables in PostgreSQL") from exc


def apply_schema(dsn: str, *, connector: Connector | None = None) -> None:
    """테이블/인덱스/뷰를 만든다. 이미 있으면 그대로 둔다."""
    connection = _connect(dsn, connector)
    try:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    return dict(value) if isinstance(value, dict) else {}


def _as_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = json.loads(value)
    return tuple(str(v) for v in (value or ()))


def _read(cursor: Any, sql: str) -> list[tuple[Any, ...]]:
    cursor.execute(sql)
    return list(cursor.fetchall())


def load_tables(dsn: str, *, connector: Connector | None = None) -> ProductTables:
    connection = _connect(dsn, connector)
    try:
        with connection.cursor() as cursor:
            catalog = [
                CatalogRow(
                    catalog_id=r[0], brand=r[1], model_code=r[2], display_name=r[3], product_line=r[4], category=r[5],
                    manufacturer=r[6], kc_certified_yn=r[7], kc_info=_as_dict(r[8]), source=r[9], verified_yn=r[10],
                    requires_brand_yn=r[11], compatible_brands=_as_tuple(r[12]), benign_suffixes=_as_tuple(r[13]),
                )
                for r in _read(cursor, """
                    SELECT catalog_id, brand, model_code, display_name, product_line, category, manufacturer, kc_certified_yn,
                           kc_info, source, verified_yn, requires_brand_yn, compatible_brands, benign_suffixes
                    FROM product_catalog ORDER BY catalog_id""")
            ]
            aliases = [
                AliasRow(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8])
                for r in _read(cursor, """
                    SELECT catalog_id, alias_text, alias_kind, alias_type, brand_required_yn, status, source, note, reviewed_by
                    FROM product_aliases ORDER BY catalog_id, alias_norm, alias_kind""")
            ]
            categories = [
                SourcingCategoryRow(r[0], r[1], r[2], r[3], r[4], int(r[5]), r[6])
                for r in _read(cursor, """
                    SELECT category_code, label_ko, kc_record_expected_yn, price_pool_yn, reviewed_yn, sort_order, note
                    FROM sourcing_categories ORDER BY sort_order, category_code""")
            ]
            signals = [
                SourcingSignalRow(r[0], r[1], r[2], int(r[3]), r[4], r[5])
                for r in _read(cursor, """
                    SELECT category_code, match_type, pattern, priority, enabled_yn, note
                    FROM sourcing_signals ORDER BY priority, match_type, pattern_norm""")
            ]
        return ProductTables(catalog, aliases, categories, signals)
    finally:
        connection.close()


def _reserved_from(existing: ProductTables) -> dict[str, str]:
    """이미 DB 에 있는 상품 표기(모델 코드 + 승인된 정확한 이름) -> 상품 ID."""
    reserved: dict[str, str] = {}
    for row in existing.catalog:
        reserved.setdefault(row.model_code_norm, row.catalog_id)
    for alias in existing.aliases:
        if alias.status == "approved" and alias.alias_kind == "model":
            reserved.setdefault(alias.alias_norm, alias.catalog_id)
    return reserved


_CATALOG_COLS = (
    "catalog_id, brand, model_code, model_code_norm, display_name, product_line, category, manufacturer, kc_certified_yn, "
    "kc_info, source, verified_yn, requires_brand_yn, compatible_brands, benign_suffixes"
)
_CATALOG_VALUES = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s::jsonb"


def plan_write(existing: ProductTables, tables: ProductTables) -> tuple[ProductTables, list[Issue], dict[str, int], dict[str, int]]:
    """DB 에 이미 있는 내용(existing)을 기준으로 가져올 행을 검증하고, 새 행/이미 있는 행의 수를 센다.

    반환: (검증을 통과한 행, 문제 목록, {표: 새 행 수}, {표: 이미 있는 행 수})
    """
    clean, issues = clean_tables(
        tables, known_ids={r.catalog_id for r in existing.catalog}, reserved_codes=_reserved_from(existing),
        model_codes={r.model_code_norm: r.catalog_id for r in existing.catalog},
    )
    have = {
        "product_catalog": {r.catalog_id for r in existing.catalog},
        "product_aliases": {(a.catalog_id, a.alias_norm, a.alias_kind) for a in existing.aliases},
        "sourcing_categories": {c.category_code for c in existing.categories},
        "sourcing_signals": {(g.match_type, g.pattern_norm) for g in existing.signals},
    }
    keys = {
        "product_catalog": [r.catalog_id for r in clean.catalog],
        "product_aliases": [(a.catalog_id, a.alias_norm, a.alias_kind) for a in clean.aliases],
        "sourcing_categories": [c.category_code for c in clean.categories],
        "sourcing_signals": [(g.match_type, g.pattern_norm) for g in clean.signals],
    }
    new = {name: sum(1 for k in ks if k not in have[name]) for name, ks in keys.items()}
    present = {name: len(ks) - new[name] for name, ks in keys.items()}
    return clean, issues, new, present


def write_tables(
    dsn: str,
    tables: ProductTables,
    *,
    update: bool = False,
    dry_run: bool = False,
    connector: Connector | None = None,
) -> dict[str, Any]:
    """검증을 통과한 행만 넣는다. update=False 면 이미 있는 행은 건드리지 않는다.

    dry_run=True 면 DB 를 읽기만 하고 쓰지 않는다 (검증 결과와 새 행/이미 있는 행의 수만 돌려준다).
    반환: {"written": {표: 쓴 행 수}, "skipped_existing": {표: 이미 있어 건드리지 않은 행 수}, "issues": [Issue...]}
    (update=True 면 written 은 새로 넣은 행과 고쳐 쓴 행을 합친 수. dry_run 이면 written 은 쓸 행 수, "dry_run": True)
    """
    existing = load_tables(dsn, connector=connector)
    clean, issues, new, present = plan_write(existing, tables)
    if dry_run:
        return {
            "written": {name: (new[name] + present[name] if update else new[name]) for name in new},
            "skipped_existing": {name: 0 if update else present[name] for name in present},
            "issues": issues, "dry_run": True,
        }
    changed = {"product_catalog": 0, "product_aliases": 0, "sourcing_categories": 0, "sourcing_signals": 0}
    offered = {
        "product_catalog": len(clean.catalog), "product_aliases": len(clean.aliases),
        "sourcing_categories": len(clean.categories), "sourcing_signals": len(clean.signals),
    }

    connection = _connect(dsn, connector)
    try:
        with connection.cursor() as cursor:
            for row in clean.catalog:
                tail = (
                    "ON CONFLICT (catalog_id) DO UPDATE SET brand = EXCLUDED.brand, model_code = EXCLUDED.model_code, "
                    "model_code_norm = EXCLUDED.model_code_norm, display_name = EXCLUDED.display_name, "
                    "product_line = EXCLUDED.product_line, category = EXCLUDED.category, manufacturer = EXCLUDED.manufacturer, "
                    "kc_certified_yn = EXCLUDED.kc_certified_yn, kc_info = EXCLUDED.kc_info, source = EXCLUDED.source, "
                    "verified_yn = EXCLUDED.verified_yn, requires_brand_yn = EXCLUDED.requires_brand_yn, "
                    "compatible_brands = EXCLUDED.compatible_brands, benign_suffixes = EXCLUDED.benign_suffixes, updated_at = NOW()"
                    if update else "ON CONFLICT DO NOTHING"
                )
                cursor.execute(
                    f"INSERT INTO product_catalog ({_CATALOG_COLS}) VALUES ({_CATALOG_VALUES}) {tail}",
                    (
                        row.catalog_id, row.brand, row.model_code, row.model_code_norm, row.display_name, row.product_line,
                        row.category, row.manufacturer, row.kc_certified_yn, json.dumps(row.kc_info, ensure_ascii=False),
                        row.source, row.verified_yn, row.requires_brand_yn,
                        json.dumps(list(row.compatible_brands), ensure_ascii=False),
                        json.dumps(list(row.benign_suffixes), ensure_ascii=False),
                    ),
                )
                changed["product_catalog"] += max(cursor.rowcount, 0)
            for row in clean.aliases:
                tail = (
                    "ON CONFLICT (catalog_id, alias_norm, alias_kind) DO UPDATE SET alias_text = EXCLUDED.alias_text, "
                    "alias_type = EXCLUDED.alias_type, brand_required_yn = EXCLUDED.brand_required_yn, "
                    "status = EXCLUDED.status, source = EXCLUDED.source, note = EXCLUDED.note, "
                    "reviewed_by = EXCLUDED.reviewed_by, updated_at = NOW()"
                    if update else "ON CONFLICT DO NOTHING"
                )
                cursor.execute(
                    "INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, alias_kind, alias_type, brand_required_yn, "
                    f"status, source, note, reviewed_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) {tail}",
                    (row.catalog_id, row.alias_text, row.alias_norm, row.alias_kind, row.alias_type, row.brand_required_yn,
                     row.status, row.source, row.note, row.reviewed_by),
                )
                changed["product_aliases"] += max(cursor.rowcount, 0)
            for row in clean.categories:
                tail = (
                    "ON CONFLICT (category_code) DO UPDATE SET label_ko = EXCLUDED.label_ko, "
                    "kc_record_expected_yn = EXCLUDED.kc_record_expected_yn, price_pool_yn = EXCLUDED.price_pool_yn, "
                    "reviewed_yn = EXCLUDED.reviewed_yn, sort_order = EXCLUDED.sort_order, note = EXCLUDED.note, updated_at = NOW()"
                    if update else "ON CONFLICT DO NOTHING"
                )
                cursor.execute(
                    "INSERT INTO sourcing_categories (category_code, label_ko, kc_record_expected_yn, price_pool_yn, reviewed_yn, "
                    f"sort_order, note) VALUES (%s, %s, %s, %s, %s, %s, %s) {tail}",
                    (row.category_code, row.label_ko, row.kc_record_expected_yn, row.price_pool_yn, row.reviewed_yn,
                     row.sort_order, row.note),
                )
                changed["sourcing_categories"] += max(cursor.rowcount, 0)
            for row in clean.signals:
                tail = (
                    "ON CONFLICT (match_type, pattern_norm) DO UPDATE SET category_code = EXCLUDED.category_code, "
                    "pattern = EXCLUDED.pattern, priority = EXCLUDED.priority, enabled_yn = EXCLUDED.enabled_yn, note = EXCLUDED.note"
                    if update else "ON CONFLICT DO NOTHING"
                )
                cursor.execute(
                    "INSERT INTO sourcing_signals (category_code, match_type, pattern, pattern_norm, priority, enabled_yn, note) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s) {tail}",
                    (row.category_code, row.match_type, row.pattern, row.pattern_norm, row.priority, row.enabled_yn, row.note),
                )
                changed["sourcing_signals"] += max(cursor.rowcount, 0)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "written": changed,
        "skipped_existing": {name: offered[name] - changed[name] for name in changed},
        "issues": issues,
    }
