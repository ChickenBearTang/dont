"""테이블 내용 검증. 오류가 있는 행은 빼고(쓰지 않고), 이유를 Issue 로 돌려준다.

한 행이 틀렸다고 전체 적재를 멈추지도, 틀린 행을 조용히 쓰지도 않는다.

별칭에서 특히 막는 것
  - 같은 이름을 서로 다른 상품이 '정확한 이름'으로 주장 -> 어느 쪽인지 알 수 없어 모두 뺀다.
    (정말 여러 상품에 걸친 이름이면 alias_kind='line' 으로 쓴다: 후보로만 쓰이고 하나를 고르지 않는다.)
  - 다른 상품의 모델 코드와 같은 이름.
  - 너무 짧거나 숫자뿐인 이름 ('3s', '4'): 브랜드가 제목에 있을 때만 인정(brand_required_yn=Y)하게 해야 한다.
"""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable, Mapping

from .models import (
    ALIAS_KINDS,
    ALIAS_SOURCES,
    ALIAS_STATUSES,
    ALIAS_TYPES,
    CATALOG_SOURCES,
    MATCH_TYPES,
    YN,
    YNU,
    AliasRow,
    CatalogRow,
    Issue,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
)

MIN_ALIAS_LEN = 2
SAFE_ALIAS_LEN = 4  # 이보다 짧거나 숫자뿐이면 브랜드가 제목에 있을 때만 인정해야 한다
MIN_PATTERN_LEN = 2
_HOSTNAME = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


def _err(table: str, key: str, code: str, message: str) -> Issue:
    return Issue("error", table, key, code, message)


def _warn(table: str, key: str, code: str, message: str) -> Issue:
    return Issue("warning", table, key, code, message)


def _one_of(value: str, allowed: Iterable[str]) -> bool:
    return value in tuple(allowed)


def clean_catalog(rows: Iterable[CatalogRow]) -> tuple[list[CatalogRow], list[Issue]]:
    kept: list[CatalogRow] = []
    issues: list[Issue] = []
    ids: set[str] = set()
    by_model: dict[tuple[str, str], str] = {}
    for row in rows:
        key = row.catalog_id or "(empty id)"
        if not row.catalog_id or not row.brand.strip() or not row.model_code_norm:
            issues.append(_err("product_catalog", key, "CATALOG_EMPTY_FIELD", "catalog_id, brand, model_code 는 비어 있으면 안 된다"))
            continue
        bad = [
            name for name, value, allowed in (
                ("kc_certified_yn", row.kc_certified_yn, YNU), ("verified_yn", row.verified_yn, YN),
                ("requires_brand_yn", row.requires_brand_yn, YN), ("source", row.source, CATALOG_SOURCES),
            ) if not _one_of(value, allowed)
        ]
        if bad:
            issues.append(_err("product_catalog", key, "CATALOG_BAD_VALUE", f"허용되지 않는 값: {', '.join(bad)}"))
            continue
        if row.catalog_id in ids:
            issues.append(_err("product_catalog", key, "CATALOG_DUPLICATE_ID", "같은 catalog_id 가 이미 있다 (뒤의 행을 쓰지 않음)"))
            continue
        model_key = (row.brand, row.model_code_norm)
        if model_key in by_model:
            issues.append(_err(
                "product_catalog", key, "CATALOG_DUPLICATE_MODEL",
                f"같은 브랜드의 같은 모델 코드가 {by_model[model_key]} 에도 있다 (뒤의 행을 쓰지 않음)",
            ))
            continue
        ids.add(row.catalog_id)
        by_model[model_key] = row.catalog_id
        kept.append(row)
    return kept, issues


def _alias_key(row: AliasRow) -> str:
    return f"{row.catalog_id} / {row.alias_text}"


def clean_aliases(
    rows: Iterable[AliasRow],
    *,
    known_ids: set[str],
    reserved_codes: Mapping[str, str],
    model_codes: Mapping[str, str] | None = None,
) -> tuple[list[AliasRow], list[Issue]]:
    """reserved_codes: 이미 어느 상품이 쓰는 표기(compact_code) -> 그 상품 ID. 모델 코드와 기존 별칭이 들어 있다.
    model_codes: 그중 모델 코드만 (표기 -> 상품 ID). 별칭이 자기 모델 코드와 같으면 쓸 필요가 없다는 경고를 낸다.
    별칭이 이미 같은 상품의 별칭으로 있는 것(다시 가져오기, 갱신)은 경고 대상이 아니다."""
    issues: list[Issue] = []
    syntactic: list[AliasRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = _alias_key(row)
        bad = [
            name for name, value, allowed in (
                ("alias_kind", row.alias_kind, ALIAS_KINDS), ("alias_type", row.alias_type, ALIAS_TYPES),
                ("brand_required_yn", row.brand_required_yn, YN), ("status", row.status, ALIAS_STATUSES),
                ("source", row.source, ALIAS_SOURCES),
            ) if not _one_of(value, allowed)
        ]
        if bad:
            issues.append(_err("product_aliases", key, "ALIAS_BAD_VALUE", f"허용되지 않는 값: {', '.join(bad)}"))
            continue
        norm = row.alias_norm
        if len(norm) < MIN_ALIAS_LEN:
            issues.append(_err("product_aliases", key, "ALIAS_EMPTY", "비교 가능한 글자(영숫자/한글)가 2자 미만이다"))
            continue
        if row.catalog_id not in known_ids:
            issues.append(_err("product_aliases", key, "ALIAS_ORPHAN", f"카탈로그에 없는 catalog_id: {row.catalog_id}"))
            continue
        if row.status != "rejected" and (len(norm) < SAFE_ALIAS_LEN or norm.isdigit()) and row.brand_required_yn != "Y":
            issues.append(_err(
                "product_aliases", key, "ALIAS_TOO_GENERIC",
                f"'{row.alias_text}' 는 너무 짧거나 숫자뿐이라 다른 글과 우연히 겹친다. brand_required_yn=Y 로 하거나 더 구체적인 이름을 쓴다",
            ))
            continue
        triple = (row.catalog_id, norm, row.alias_kind)
        if triple in seen:
            issues.append(_warn("product_aliases", key, "ALIAS_DUPLICATE", "같은 상품에 같은 이름이 이미 있다 (뒤의 행을 쓰지 않음)"))
            continue
        seen.add(triple)
        syntactic.append(row)

    # 정확한 이름(model)의 충돌: 승인된 이름만 서로 비교한다.
    claims: dict[str, set[str]] = defaultdict(set)
    for row in syntactic:
        if row.status == "approved" and row.alias_kind == "model":
            claims[row.alias_norm].add(row.catalog_id)

    kept: list[AliasRow] = []
    for row in syntactic:
        norm = row.alias_norm
        if row.alias_kind == "model" and row.status != "rejected":
            owner = reserved_codes.get(norm)
            if (model_codes or {}).get(norm) == row.catalog_id:
                issues.append(_warn("product_aliases", _alias_key(row), "ALIAS_SAME_AS_MODEL", "이 상품의 모델 코드와 같다 (별칭으로 쓰지 않아도 같다)"))
                continue
            clash = sorted((claims.get(norm, set()) | ({owner} if owner else set())) - {row.catalog_id})
            if clash:
                if row.status == "approved":
                    issues.append(_err(
                        "product_aliases", _alias_key(row), "ALIAS_CONFLICT",
                        f"같은 이름을 {', '.join(clash)} 도 정확한 이름으로 쓴다. 어느 쪽인지 알 수 없어 쓰지 않는다 (여러 상품에 걸친 이름이면 alias_kind=line)",
                    ))
                    continue
                issues.append(_warn(
                    "product_aliases", _alias_key(row), "PENDING_ALIAS_WOULD_CONFLICT",
                    f"승인하면 {', '.join(clash)} 와 충돌한다",
                ))
        kept.append(row)
    return kept, issues


def clean_sourcing(
    categories: Iterable[SourcingCategoryRow], signals: Iterable[SourcingSignalRow]
) -> tuple[list[SourcingCategoryRow], list[SourcingSignalRow], list[Issue]]:
    issues: list[Issue] = []
    kept_categories: list[SourcingCategoryRow] = []
    codes: set[str] = set()
    for row in categories:
        key = row.category_code or "(empty)"
        bad = [
            name for name, value, allowed in (
                ("kc_record_expected_yn", row.kc_record_expected_yn, YNU), ("price_pool_yn", row.price_pool_yn, YN),
                ("reviewed_yn", row.reviewed_yn, YN),
            ) if not _one_of(value, allowed)
        ]
        if not row.category_code or not row.label_ko.strip():
            issues.append(_err("sourcing_categories", key, "CATEGORY_EMPTY_FIELD", "category_code, label_ko 는 비어 있으면 안 된다"))
        elif bad:
            issues.append(_err("sourcing_categories", key, "CATEGORY_BAD_VALUE", f"허용되지 않는 값: {', '.join(bad)}"))
        elif row.category_code in codes:
            issues.append(_err("sourcing_categories", key, "CATEGORY_DUPLICATE", "같은 category_code 가 이미 있다 (뒤의 행을 쓰지 않음)"))
        else:
            codes.add(row.category_code)
            kept_categories.append(row)

    staged: list[SourcingSignalRow] = []
    for row in signals:
        key = f"{row.match_type}:{row.pattern}"
        norm = row.pattern_norm
        if not _one_of(row.match_type, MATCH_TYPES) or not _one_of(row.enabled_yn, YN):
            issues.append(_err("sourcing_signals", key, "SIGNAL_BAD_VALUE", "match_type 또는 enabled_yn 이 허용되지 않는 값이다"))
        elif row.category_code not in codes:
            issues.append(_err("sourcing_signals", key, "SIGNAL_UNKNOWN_CATEGORY", f"없는 category_code: {row.category_code}"))
        elif not norm:
            issues.append(_err("sourcing_signals", key, "SIGNAL_EMPTY_PATTERN", "비교 가능한 글자가 없다"))
        elif row.match_type == "domain" and not _HOSTNAME.match(norm):
            issues.append(_err("sourcing_signals", key, "SIGNAL_BAD_DOMAIN", "호스트 이름만 쓴다 (예: aliexpress.com). 주소 전체/경로는 안 된다"))
        elif row.match_type != "domain" and len(norm.replace(" ", "")) < MIN_PATTERN_LEN:
            issues.append(_err("sourcing_signals", key, "SIGNAL_PATTERN_TOO_SHORT", "한 글자 신호는 다른 말과 겹쳐 쓸 수 없다"))
        else:
            staged.append(row)

    by_pattern: dict[tuple[str, str], list[SourcingSignalRow]] = defaultdict(list)
    for row in staged:
        by_pattern[(row.match_type, row.pattern_norm)].append(row)
    kept_signals: list[SourcingSignalRow] = []
    for (match_type, norm), group in by_pattern.items():
        categories_of = {r.category_code for r in group}
        if len(categories_of) > 1:
            issues.append(_err(
                "sourcing_signals", f"{match_type}:{norm}", "SIGNAL_CONFLICT",
                f"같은 신호가 서로 다른 경로({', '.join(sorted(categories_of))})를 가리킨다. 모두 쓰지 않는다",
            ))
            continue
        if len(group) > 1:
            issues.append(_warn("sourcing_signals", f"{match_type}:{norm}", "SIGNAL_DUPLICATE", "같은 신호가 여러 줄이다 (첫 줄만 씀)"))
        kept_signals.append(group[0])
    return kept_categories, kept_signals, issues


def clean_tables(
    tables: ProductTables,
    *,
    known_ids: Iterable[str] = (),
    reserved_codes: Mapping[str, str] | None = None,
    model_codes: Mapping[str, str] | None = None,
) -> tuple[ProductTables, list[Issue]]:
    """known_ids/reserved_codes/model_codes: 이 테이블 밖(예: 파일 카탈로그, DB 에 이미 있는 행)의 상품과 그 표기."""
    catalog, issues = clean_catalog(tables.catalog)
    ids = set(known_ids) | {row.catalog_id for row in catalog}
    reserved = dict(reserved_codes or {})
    models = dict(model_codes or {})
    for row in catalog:
        reserved.setdefault(row.model_code_norm, row.catalog_id)
        models[row.model_code_norm] = row.catalog_id
    aliases, alias_issues = clean_aliases(tables.aliases, known_ids=ids, reserved_codes=reserved, model_codes=models)
    categories, signals, sourcing_issues = clean_sourcing(tables.categories, tables.signals)
    return ProductTables(catalog, aliases, categories, signals), [*issues, *alias_issues, *sourcing_issues]
