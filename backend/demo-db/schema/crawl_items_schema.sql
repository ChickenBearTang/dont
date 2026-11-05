-- ai-postgres 의 crawl_items (핫딜 크롤링 원본). demo DB 용.
--
-- 출처: backend/AI_TMP/ai/storage/postgres_store.py 의 PostgresCrawlStore._initialize() 가 만드는
-- 테이블과 같다 (CREATE + ALTER 를 합친 최종 모양). 스토어가 CREATE TABLE IF NOT EXISTS 를 쓰므로
-- 이 파일을 먼저 적용해도, 나중에 스토어가 떠도 충돌하지 않는다.
-- Spring 의 PrXaiAvailabilityService 가 같은 테이블을 JDBC 로 직접 조회한다
-- (is_outlier, url, title, price, last_seen_at 컬럼).

CREATE TABLE IF NOT EXISTS crawl_items (
    source            TEXT        NOT NULL,
    post_id           TEXT,
    url               TEXT PRIMARY KEY,
    title             TEXT        NOT NULL,
    price             TEXT,                       -- 숫자만 남긴 원 단위 문자열 ("99000")
    posted_at         TEXT,                       -- 사이트에 보이는 글자 그대로 ("2026.03.26", "03.26", "13:05" ...)
    fetched_at        TIMESTAMPTZ NOT NULL,
    first_seen_at     TIMESTAMPTZ NOT NULL,
    last_seen_at      TIMESTAMPTZ NOT NULL,
    is_outlier        BOOLEAN     NOT NULL DEFAULT FALSE,
    outlier_reason    TEXT,
    outlier_marked_at TIMESTAMPTZ,
    item_family       TEXT
);

CREATE INDEX IF NOT EXISTS idx_crawl_items_source_post_id ON crawl_items (source, post_id);
CREATE INDEX IF NOT EXISTS idx_crawl_items_outlier ON crawl_items (is_outlier);
CREATE INDEX IF NOT EXISTS idx_crawl_items_item_family ON crawl_items (item_family);
