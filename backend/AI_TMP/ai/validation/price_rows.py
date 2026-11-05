"""가격 모델 학습 행 검증.

한 행씩 보는 규칙(값 범위, 계산식 일치, 브랜드/판매자 오염)과 데이터셋 전체를 보는
규칙(상품 수, 이력 피처 채움률, 수집 시점, 중복, 상품 내 이상치)으로 나뉜다.
임계값(MIN_ROWS 등)은 판단값이다. 실제 데이터가 쌓이면 근거를 보고 조정한다.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import math
from statistics import median
from typing import Any, Iterable

from .core import Severity, ValidationReport

SCHEMA_VERSION = "price-engine-mvp-v1"
MIN_ROWS = 200
MIN_PRODUCTS = 20
MIN_HISTORY_COVERAGE = 0.5
MAX_PRICE = 100_000_000.0
LOW_PRICE = 1_000.0
OUTLIER_FACTOR = 5.0  # 같은 상품 중앙값의 5배 초과 또는 1/5 미만

REQUIRED = ("canonical_product_id", "snapshot_date", "current_effective_price", "category", "brand")
HISTORY_FIELDS = (
    "avg_price_7d", "avg_price_30d", "min_price_30d", "max_price_30d", "price_volatility_30d",
    "price_vs_avg_7d", "price_vs_avg_30d", "price_to_min_30d_gap", "price_to_max_30d_gap",
)
NON_NEGATIVE = ("price_volatility_30d", "release_age_days", "shipping_fee_mode_30d",
                "avg_price_7d", "avg_price_30d", "min_price_30d", "max_price_30d")
_REL_TOL = 1e-6


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= _REL_TOL * max(abs(a), abs(b), 1.0)


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def validate_price_training_rows(
    rows: Iterable[Any], *, now: datetime | None = None
) -> ValidationReport:
    rows = list(rows)
    now = now or datetime.now(timezone.utc)
    report = ValidationReport("price_training_rows", rows_checked=len(rows))
    err = Severity.ERROR

    valid_rows: list[tuple[int, dict[str, Any]]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            report.add("ROW_NOT_OBJECT", err, "행이 객체가 아니다", row_index=i)
            continue
        valid_rows.append((i, row))
        _check_row(report, i, row, now)

    _check_dataset(report, valid_rows)
    return report


def _check_row(report: ValidationReport, i: int, row: dict[str, Any], now: datetime) -> None:
    err, warn = Severity.ERROR, Severity.WARNING

    for name in REQUIRED:
        if row.get(name) in (None, ""):
            report.add("MISSING_FIELD", err, f"필수 필드가 없다: {name}", row_index=i, field_name=name)

    if str(row.get("schema_version", SCHEMA_VERSION)) != SCHEMA_VERSION:
        report.add("SCHEMA_VERSION_MISMATCH", err, "스키마 버전이 다르다", row_index=i, field_name="schema_version")

    price_raw = row.get("current_effective_price")
    price = _num(price_raw)
    if price_raw is not None and price is None:
        report.add("PRICE_NOT_NUMERIC", err, "가격이 숫자가 아니다", row_index=i, field_name="current_effective_price")
    elif price is not None:
        if price <= 0:
            report.add("PRICE_NOT_POSITIVE", err, "가격이 0 이하다", row_index=i, field_name="current_effective_price")
        elif price > MAX_PRICE:
            report.add("PRICE_OUT_OF_RANGE", err, f"가격이 상한({MAX_PRICE:,.0f})을 넘는다", row_index=i, field_name="current_effective_price")
        elif price < LOW_PRICE:
            report.add("PRICE_SUSPICIOUSLY_LOW", warn, f"가격이 {LOW_PRICE:,.0f}원 미만이라 파싱 오류일 수 있다", row_index=i, field_name="current_effective_price")

    for name in NON_NEGATIVE:
        value = _num(row.get(name))
        if value is not None and value < 0:
            report.add("NEGATIVE_VALUE", err, f"{name} 이 음수다", row_index=i, field_name=name)

    lo, hi = _num(row.get("min_price_30d")), _num(row.get("max_price_30d"))
    avg30 = _num(row.get("avg_price_30d"))
    if lo is not None and hi is not None and lo > hi:
        report.add("MIN_GT_MAX", err, "30일 최소가가 최대가보다 크다", row_index=i)
    if avg30 is not None and lo is not None and hi is not None and lo <= hi and not (lo - 1e-9 <= avg30 <= hi + 1e-9):
        report.add("AVG_OUT_OF_BOUNDS", err, "30일 평균이 최소~최대 밖이다", row_index=i, field_name="avg_price_30d")

    if price is not None and price > 0:
        for ratio_name, avg_name in (("price_vs_avg_7d", "avg_price_7d"), ("price_vs_avg_30d", "avg_price_30d")):
            ratio, avg = _num(row.get(ratio_name)), _num(row.get(avg_name))
            if ratio is not None and avg is not None and avg > 0 and not _close(ratio, price / avg):
                report.add("DERIVED_MISMATCH", err, f"{ratio_name} 이 가격/평균과 다르다", row_index=i, field_name=ratio_name)
        gap_lo, gap_hi = _num(row.get("price_to_min_30d_gap")), _num(row.get("price_to_max_30d_gap"))
        if gap_lo is not None and lo is not None and not _close(gap_lo, price - lo):
            report.add("DERIVED_MISMATCH", err, "price_to_min_30d_gap 이 가격-최소가와 다르다", row_index=i, field_name="price_to_min_30d_gap")
        if gap_hi is not None and hi is not None and not _close(gap_hi, hi - price):
            report.add("DERIVED_MISMATCH", err, "price_to_max_30d_gap 이 최대가-가격과 다르다", row_index=i, field_name="price_to_max_30d_gap")

    sellers = _num(row.get("seller_count_same_product"))
    if sellers is not None and sellers < 1:
        report.add("SELLER_COUNT_INVALID", err, "같은 상품 판매처 수가 1 미만이다", row_index=i, field_name="seller_count_same_product")

    brand = str(row.get("brand") or "")
    product = str(row.get("canonical_product_id") or "")
    if brand and brand == product:
        report.add("BRAND_IS_PRODUCT_ID", err, "brand 가 상품 ID 와 같다 (검색어를 브랜드로 쓴 것으로 보인다)", row_index=i, field_name="brand")
    elif brand.strip().lower() in ("", "unknown", "none", "null"):
        report.add("BRAND_UNKNOWN", warn, "브랜드를 알 수 없다", row_index=i, field_name="brand")

    seller = row.get("seller_id")
    if isinstance(seller, str) and seller.lower().startswith(("http://", "https://")):
        report.add("SELLER_ID_IS_URL", warn, "seller_id 가 URL 이다 (크롤러가 쓴 검색 주소이지 판매자가 아니다)", row_index=i, field_name="seller_id")

    parsed = _parse_date(row.get("snapshot_date"))
    if row.get("snapshot_date") not in (None, ""):
        if parsed is None:
            report.add("SNAPSHOT_DATE_INVALID", err, "snapshot_date 를 읽을 수 없다", row_index=i, field_name="snapshot_date")
        elif parsed > now:
            report.add("SNAPSHOT_IN_FUTURE", err, "snapshot_date 가 미래다", row_index=i, field_name="snapshot_date")

    if all(row.get(name) is None for name in HISTORY_FIELDS):
        report.add("NO_HISTORY_FEATURES", warn, "가격 이력 피처가 전부 비어 있다", row_index=i)


def _check_dataset(report: ValidationReport, valid_rows: list[tuple[int, dict[str, Any]]]) -> None:
    err, warn = Severity.ERROR, Severity.WARNING
    n = len(valid_rows)
    if n == 0:
        return
    rows = [r for _, r in valid_rows]

    if n < MIN_ROWS:
        report.add("TOO_FEW_ROWS", err, f"학습 행이 {n}개뿐이다 (최소 {MIN_ROWS}개 필요)")

    products = {str(r.get("canonical_product_id")) for r in rows if r.get("canonical_product_id") not in (None, "")}
    if len(products) < MIN_PRODUCTS:
        report.add("TOO_FEW_PRODUCTS", err, f"서로 다른 상품이 {len(products)}개뿐이다 (최소 {MIN_PRODUCTS}개 필요)")

    filled = sum(1 for r in rows if any(r.get(name) is not None for name in HISTORY_FIELDS))
    coverage = filled / n
    if coverage < MIN_HISTORY_COVERAGE:
        report.add("HISTORY_FEATURES_MOSTLY_NULL", err, f"가격 이력 피처가 있는 행이 {coverage:.0%}뿐이다 (최소 {MIN_HISTORY_COVERAGE:.0%})")

    days = {str(r.get("snapshot_date"))[:10] for r in rows if r.get("snapshot_date")}
    if n >= 2 and len(days) == 1:
        report.add("SINGLE_SNAPSHOT_DATE", warn, "모든 행이 같은 날짜에 수집됐다 (시간에 따른 변화를 배울 수 없다)")

    seen: dict[tuple[Any, ...], int] = {}
    for i, r in valid_rows:
        key = (r.get("canonical_product_id"), r.get("variant_id"), r.get("seller_id"), r.get("snapshot_date"))
        if key in seen:
            report.add("DUPLICATE_KEY", err, "같은 (상품, 변형, 판매자, 시점) 행이 중복된다", row_index=i)
        else:
            seen[key] = i

    by_product: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for i, r in valid_rows:
        price = _num(r.get("current_effective_price"))
        if price is not None and price > 0:
            by_product[str(r.get("canonical_product_id"))].append((i, price))
    for items in by_product.values():
        if len(items) < 5:
            continue
        mid = median(p for _, p in items)
        for i, p in items:
            if p > mid * OUTLIER_FACTOR or p < mid / OUTLIER_FACTOR:
                report.add("PRICE_OUTLIER", warn, f"같은 상품 중앙값({mid:,.0f}원) 대비 {OUTLIER_FACTOR:g}배 이상 벗어난 가격", row_index=i, field_name="current_effective_price")
