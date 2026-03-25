from __future__ import annotations

SCHEMA_VERSION = "price-engine-mvp-v1"

PHASE2_RESERVED_FIELDS: tuple[str, ...] = (
    "coupon_text_raw",
    "coupon_discount_amount",
    "card_benefit_text_raw",
    "card_discount_amount",
    "membership_text_raw",
    "membership_discount_amount",
)

FORBIDDEN_TRAIN_FIELDS: tuple[str, ...] = (
    "post_url",
    "post_id_raw",
    "merchant_url",
    "merchant_domain",
    "title_raw",
    "body_raw",
    "price_raw",
    "shipping_raw",
    "source_site",
    "html_hash",
    "raw_jsonld",
    "coupon_text_raw",
    "coupon_discount_amount",
    "card_benefit_text_raw",
    "card_discount_amount",
    "membership_text_raw",
    "membership_discount_amount",
)

FEATURE_ALLOWLIST_PHASE1: dict[str, tuple[str, ...]] = {
    "numeric": (
        "current_effective_price",
        "avg_price_7d",
        "avg_price_30d",
        "min_price_30d",
        "max_price_30d",
        "price_volatility_30d",
        "seller_count_same_product",
        "release_age_days",
        "shipping_fee_mode_30d",
        "price_vs_avg_7d",
        "price_vs_avg_30d",
        "price_to_min_30d_gap",
        "price_to_max_30d_gap",
    ),
    "categorical": (
        "brand",
        "category",
        "seller_type",
        "availability_status",
    ),
}


def training_feature_names() -> tuple[str, ...]:
    return FEATURE_ALLOWLIST_PHASE1["numeric"] + FEATURE_ALLOWLIST_PHASE1["categorical"]
