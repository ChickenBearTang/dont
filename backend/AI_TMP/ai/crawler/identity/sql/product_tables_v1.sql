-- 상품 카탈로그 · 별칭 · 유통경로(직구/병행수입) 규칙 테이블 (PostgreSQL)
--
--   product_catalog      한국 인증 기관(KC/전파 적합성평가) 기준 카탈로그. 인증 기록의 기본모델 하나가 한 줄.
--   product_aliases      그 상품을 가리키는 마케팅 이름/한글 표기/줄임말/통칭. 이름은 사람마다 다르고 비슷한
--                        모델도 있으므로 '승인된 이름만' 정확히 일치할 때 쓴다 (유사도로 맞추지 않는다).
--   sourcing_categories  유통경로 분류(정식수입/병행수입/직구/구매대행)와 그 경로의 규칙(Y/N 열).
--   sourcing_signals     제목/주소에서 유통경로를 알아내는 신호(키워드, 도메인).
--
-- 여러 번 실행해도 안전하다 (IF NOT EXISTS). 값의 뜻과 검수 방법은 docs/product_tables.md.

CREATE TABLE IF NOT EXISTS product_catalog (
    catalog_id         TEXT PRIMARY KEY,
    brand              TEXT NOT NULL,
    model_code         TEXT NOT NULL,   -- 인증 기본모델 코드 (예: SM-R510). 인증 전 항목은 대표 모델명
    model_code_norm    TEXT NOT NULL,   -- 소문자 영숫자/한글만 이어 붙인 비교용 값
    display_name       TEXT,            -- 사람이 읽는 대표 이름 (화면 표시용, 매칭에는 쓰지 않는다)
    product_line       TEXT NOT NULL DEFAULT '',   -- 같은 제품군 (MX Master). 버전 없이 제품군만 말한 제목은 후보로만 본다
    category           TEXT NOT NULL DEFAULT '',   -- 우리 분류(mouse ...) 또는 인증 기록의 기자재명칭
    manufacturer       TEXT,
    kc_certified_yn    CHAR(1) NOT NULL DEFAULT 'U' CHECK (kc_certified_yn IN ('Y', 'N', 'U')),  -- Y: 인증 DB 기록 있음, N: 없음(직구 전용 등), U: 아직 확인 안 함
    kc_info            JSONB NOT NULL DEFAULT '{}'::jsonb,       -- 관리번호, 제조자, 제조국, 최초 인증일
    source             TEXT NOT NULL DEFAULT 'curated' CHECK (source IN ('kc', 'curated', 'seed', 'import_only')),
    verified_yn        CHAR(1) NOT NULL DEFAULT 'N' CHECK (verified_yn IN ('Y', 'N')),
    requires_brand_yn  CHAR(1) NOT NULL DEFAULT 'N' CHECK (requires_brand_yn IN ('Y', 'N')),  -- Y: 제목에 브랜드가 있을 때만 맞춘다
    compatible_brands  JSONB NOT NULL DEFAULT '[]'::jsonb,       -- 제목에 이 브랜드가 있어도 같은 상품으로 본다 (그래픽카드 파트너사)
    benign_suffixes    JSONB NOT NULL DEFAULT '[]'::jsonb,       -- 모델명 뒤에 붙어도 상품을 바꾸지 않는 말
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (brand, model_code_norm)
);

CREATE INDEX IF NOT EXISTS idx_product_catalog_brand ON product_catalog (brand);

CREATE TABLE IF NOT EXISTS product_aliases (
    alias_id           BIGSERIAL PRIMARY KEY,
    catalog_id         TEXT NOT NULL REFERENCES product_catalog (catalog_id) ON UPDATE CASCADE ON DELETE CASCADE,
    alias_text         TEXT NOT NULL,   -- 사람이 쓴 그대로 (MX Master S3)
    alias_norm         TEXT NOT NULL,   -- 비교용 (mxmasters3). 매칭은 이 값이 제목의 토큰 경계와 정확히 같을 때만 성립
    alias_kind         TEXT NOT NULL DEFAULT 'model' CHECK (alias_kind IN ('model', 'line')),
                       -- model: 이 상품 하나를 가리킴.  line: 제품군 이름이라 여러 상품에 걸침 (후보로만 쓰고 고르지 않는다)
    alias_type         TEXT NOT NULL DEFAULT 'other' CHECK (alias_type IN
                       ('marketing', 'korean', 'english', 'abbreviation', 'colloquial', 'misspelling', 'kc_derived', 'part_number', 'other')),
    brand_required_yn  CHAR(1) NOT NULL DEFAULT 'N' CHECK (brand_required_yn IN ('Y', 'N')),  -- Y: 제목에 브랜드가 있을 때만 이 이름을 인정
    status             TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('approved', 'pending', 'rejected')),  -- approved 만 매칭에 쓴다
    source             TEXT NOT NULL DEFAULT 'curated' CHECK (source IN ('curated', 'kc', 'crawl_suggested', 'llm_suggested', 'user_report')),
    note               TEXT,
    reviewed_by        TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (catalog_id, alias_norm, alias_kind)
);

CREATE INDEX IF NOT EXISTS idx_product_aliases_norm ON product_aliases (alias_norm);

-- 같은 이름을 서로 다른 상품이 '정확한 이름'으로 주장하는 경우. 이런 이름은 어느 쪽인지 알 수 없어 쓰지 않는다.
CREATE OR REPLACE VIEW v_product_alias_conflicts AS
SELECT alias_norm,
       COUNT(DISTINCT catalog_id) AS products,
       ARRAY_AGG(DISTINCT catalog_id ORDER BY catalog_id) AS catalog_ids
FROM product_aliases
WHERE status = 'approved' AND alias_kind = 'model'
GROUP BY alias_norm
HAVING COUNT(DISTINCT catalog_id) > 1;

CREATE TABLE IF NOT EXISTS sourcing_categories (
    category_code          TEXT PRIMARY KEY,   -- OFFICIAL_IMPORT / PARALLEL_IMPORT / DIRECT_PURCHASE / PURCHASING_AGENCY
    label_ko               TEXT NOT NULL,
    kc_record_expected_yn  CHAR(1) NOT NULL CHECK (kc_record_expected_yn IN ('Y', 'N', 'U')),
                           -- 이 경로의 상품은 인증 DB에 기록이 있을 것으로 기대하는가. Y 인데 카탈로그에 없으면 '카탈로그 공백'으로 알린다.
    price_pool_yn          CHAR(1) NOT NULL CHECK (price_pool_yn IN ('Y', 'N')),
                           -- 가격 이력을 같은 상품의 다른 경로 가격과 합쳐도 되는가. N 이면 경로별로 따로 쌓는다 (관부가세/배송/보증이 달라 가격 수준이 다르다).
    reviewed_yn            CHAR(1) NOT NULL DEFAULT 'N' CHECK (reviewed_yn IN ('Y', 'N')),  -- 사람이 확인한 값인가. N 이면 초기 가정이다
    sort_order             INTEGER NOT NULL DEFAULT 100,
    note                   TEXT,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sourcing_signals (
    signal_id      BIGSERIAL PRIMARY KEY,
    category_code  TEXT NOT NULL REFERENCES sourcing_categories (category_code) ON UPDATE CASCADE,
    match_type     TEXT NOT NULL CHECK (match_type IN ('keyword', 'token', 'domain')),
                   -- keyword: 제목(공백/기호 무시)에 포함되면 일치 (직구 -> 해외직구, 직구템).  token: 제목의 토큰이 정확히 같을 때 (짧은 영문 ebay 등).  domain: 주소의 호스트
    pattern        TEXT NOT NULL,
    pattern_norm   TEXT NOT NULL,
    priority       INTEGER NOT NULL DEFAULT 100,   -- 작을수록 먼저. 일치한 신호 중 가장 작은 값끼리만 판정하고, 서로 다른 경로면 '충돌'로 알린다
    enabled_yn     CHAR(1) NOT NULL DEFAULT 'Y' CHECK (enabled_yn IN ('Y', 'N')),
    note           TEXT,
    UNIQUE (match_type, pattern_norm)
);
