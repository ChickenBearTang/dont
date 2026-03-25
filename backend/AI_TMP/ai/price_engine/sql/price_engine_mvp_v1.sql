CREATE TABLE IF NOT EXISTS raw_listing (
    id BIGSERIAL PRIMARY KEY,
    source_site TEXT NOT NULL,
    post_url TEXT NOT NULL,
    post_id_raw TEXT NOT NULL,
    title_raw TEXT NOT NULL,
    merchant_raw_hint TEXT,
    category_raw TEXT,
    price_raw TEXT,
    shipping_raw TEXT,
    created_at_raw TEXT,
    crawled_at TIMESTAMPTZ NOT NULL,
    html_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_post_detail (
    id BIGSERIAL PRIMARY KEY,
    post_url TEXT NOT NULL,
    title_raw TEXT NOT NULL,
    body_raw TEXT NOT NULL,
    external_links JSONB NOT NULL,
    posted_at_exact TIMESTAMPTZ,
    promo_text_raw TEXT,
    option_text_raw TEXT,
    soldout_text_raw TEXT,
    crawled_at TIMESTAMPTZ NOT NULL,
    html_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_merchant_offer (
    id BIGSERIAL PRIMARY KEY,
    merchant_url TEXT NOT NULL,
    merchant_domain TEXT NOT NULL,
    seller_name_raw TEXT,
    product_name_raw TEXT,
    brand_raw TEXT,
    gtin_raw TEXT,
    mpn_raw TEXT,
    model_code_raw TEXT,
    listed_price_raw TEXT,
    original_price_raw TEXT,
    sale_price_raw TEXT,
    shipping_fee_raw TEXT,
    availability_raw TEXT,
    stock_raw TEXT,
    raw_jsonld JSONB,
    crawled_at TIMESTAMPTZ NOT NULL,
    html_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS price_observation (
    id BIGSERIAL PRIMARY KEY,
    canonical_product_id_candidate TEXT NOT NULL,
    variant_id_candidate TEXT,
    seller_id_candidate TEXT,
    observed_at TIMESTAMPTZ NOT NULL,
    listed_price BIGINT,
    shipping_fee BIGINT,
    effective_price_candidate BIGINT,
    availability_status TEXT,
    stock_status TEXT,
    source_site TEXT NOT NULL,
    source_priority TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    evidence_refs JSONB NOT NULL,
    normalization_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    coupon_text_raw TEXT,
    coupon_discount_amount BIGINT,
    card_benefit_text_raw TEXT,
    card_discount_amount BIGINT,
    membership_text_raw TEXT,
    membership_discount_amount BIGINT
);

CREATE INDEX IF NOT EXISTS idx_price_obs_product_time
ON price_observation (canonical_product_id_candidate, observed_at);
