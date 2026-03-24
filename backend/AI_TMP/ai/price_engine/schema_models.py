from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .allowlist import SCHEMA_VERSION


@dataclass(frozen=True)
class RawListing:
    source_site: str
    post_url: str
    post_id_raw: str
    title_raw: str
    merchant_raw_hint: str | None
    category_raw: str | None
    price_raw: str | None
    shipping_raw: str | None
    created_at_raw: str | None
    crawled_at: datetime
    html_hash: str


@dataclass(frozen=True)
class RawPostDetail:
    post_url: str
    title_raw: str
    body_raw: str
    external_links: list[str]
    posted_at_exact: datetime | None
    promo_text_raw: str | None
    option_text_raw: str | None
    soldout_text_raw: str | None
    crawled_at: datetime
    html_hash: str


@dataclass(frozen=True)
class RawMerchantOffer:
    merchant_url: str
    merchant_domain: str
    seller_name_raw: str | None
    product_name_raw: str | None
    brand_raw: str | None
    gtin_raw: str | None
    mpn_raw: str | None
    model_code_raw: str | None
    listed_price_raw: str | None
    original_price_raw: str | None
    sale_price_raw: str | None
    shipping_fee_raw: str | None
    availability_raw: str | None
    stock_raw: str | None
    raw_jsonld: dict[str, Any] | None
    crawled_at: datetime
    html_hash: str


@dataclass(frozen=True)
class PriceObservation:
    canonical_product_id_candidate: str
    variant_id_candidate: str | None
    seller_id_candidate: str | None
    observed_at: datetime
    listed_price: int | None
    shipping_fee: int | None
    effective_price_candidate: int | None
    availability_status: str | None
    stock_status: str | None
    source_site: str
    source_priority: str
    confidence: float
    evidence_refs: list[dict[str, Any]]
    normalization_version: str
    schema_version: str = SCHEMA_VERSION
    brand: str | None = None
    category: str | None = None
    seller_type: str | None = None

    coupon_text_raw: str | None = None
    coupon_discount_amount: int | None = None
    card_benefit_text_raw: str | None = None
    card_discount_amount: int | None = None
    membership_text_raw: str | None = None
    membership_discount_amount: int | None = None

    post_url: str | None = None
    post_id_raw: str | None = None
    merchant_url: str | None = None
    merchant_domain: str | None = None
    title_raw: str | None = None
    body_raw: str | None = None
    price_raw: str | None = None
    shipping_raw: str | None = None
    html_hash: str | None = None
    raw_jsonld: dict[str, Any] | None = None


@dataclass(frozen=True)
class PriceFeatureSnapshotRow:
    canonical_product_id: str
    variant_id: str | None
    seller_id: str | None
    snapshot_date: datetime
    current_effective_price: float
    avg_price_7d: float | None
    avg_price_30d: float | None
    min_price_30d: float | None
    max_price_30d: float | None
    price_volatility_30d: float | None
    seller_count_same_product: float
    release_age_days: float
    shipping_fee_mode_30d: float | None
    price_vs_avg_7d: float | None
    price_vs_avg_30d: float | None
    price_to_min_30d_gap: float | None
    price_to_max_30d_gap: float | None
    brand: str
    category: str
    seller_type: str
    availability_status: str
    schema_version: str = SCHEMA_VERSION
    market_gap: float | None = None
    history_gap: float | None = None
    price_bucket: str | None = None


@dataclass(frozen=True)
class DatasetBuildResult:
    raw_records: list[PriceObservation] = field(default_factory=list)
    training_rows: list[PriceFeatureSnapshotRow] = field(default_factory=list)
