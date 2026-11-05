"""crawl_items(핫딜 가격) demo 시드.

!! 전부 가짜다 !!
    실제 퀘이사존 글·실제 시세가 아니다. 제품 3개(F87, MX Master 3S, VXE R1 — Spring
    PrXaiAvailabilityService 가 지원하는 품목)의 가격 흐름을 '그럴듯한 모양'으로 만든 것이다.
    기준가·변동 폭은 임의로 정한 값이다. 그래서 이 데이터로 가격 모델을 학습해 점수를 내면 그것은
    '이 생성기가 만든 모양을 얼마나 따라 하나'일 뿐 실제 가격 예측력이 아니다. 목적은 (1) 가격 학습
    파이프라인이 8개 이상의 서로 다른 값을 가진 feature 로 끝까지 도는지, (2) Spring·AI 가
    crawl_items 를 읽는 경로를 돌려 보는 것이다.

가짜임을 알아보게 하고 지우기 쉽게 하려고 source·url 을 예약 도메인(demo.invalid)으로 만든다.
  지우기:  DELETE FROM crawl_items WHERE source LIKE 'https://demo.invalid/%';

가격 과정 (제품마다 독립):
    로그 가격 = AR(1) 평균 회귀(phi=0.96) + 세일 구간(제품당 3번, 4~7일, 추가 8~15% 할인)
    글마다 0~10% 의 개별 할인. 100원 단위로 반올림.
이상치: 제품당 2건, 입력 실수(x10 또는 x0.1)를 흉내 낸다. 그 위에 mark_price_outliers 배치와 같은 규칙
  (제품별 IQR x1.5 울타리)을 적용해 is_outlier 를 채운다 — 배치가 돈 뒤의 상태다. 큰 세일 구간의 낮은 가격도
  울타리 밖이면 같이 표시된다 (배치가 실제로 그렇게 동작한다). 이 표시가 스토어의 실제 배치 결과와
  정확히 같은지는 tests/test_demo_db.py 가 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
import math
import random

from .sqlfmt import insert_rows

KST = timezone(timedelta(hours=9))
DEMO_SOURCE_PREFIX = "https://demo.invalid/"
HISTORY_DAYS = 120
POSTS_PER_DAY = 1.2
FIRST_POST_ID = 9_000_001
OUTLIER_CHANNEL = "quasarzone"  # mark_price_outliers(channels=[...]) 에 넘기는 값과 같다


@dataclass(frozen=True)
class Product:
    family: str  # 스토어 classify_item_family() 가 돌려줘야 하는 값
    keyword: str  # source 의 검색어 (퀘이사존 검색 URL 모양)
    title: str  # {price} 자리에 "99,000" 같은 표기가 들어간다
    base_price: int
    malls: tuple[str, ...]


PRODUCTS: tuple[Product, ...] = (
    Product("f87", "F87", "{mall} 독거미 F87 PRO 유무선 기계식 키보드 ({price}원/무료)", 99_000, ("쿠팡", "11번가", "G마켓")),
    Product("mx_master", "MX Master 3S", "{mall} 로지텍 MX Master 3S 무선 마우스 ({price}원/무료)", 119_000, ("쿠팡", "네이버", "옥션")),
    Product("vxe_r1", "VXE R1", "{mall} VXE R1 PRO 무선 게이밍 마우스 ({price}원/무료)", 49_000, ("알리익스프레스", "쿠팡", "네이버")),
)


@dataclass(frozen=True)
class CrawlRow:
    source: str
    post_id: str
    url: str
    title: str
    price: str
    posted_at: str
    fetched_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime
    is_outlier: bool
    outlier_reason: str | None
    outlier_marked_at: datetime | None
    item_family: str
    kind: str  # "normal" | "anomaly"  (SQL 에는 들어가지 않는다, 테스트용)


def source_for(product: Product) -> str:
    return f"{DEMO_SOURCE_PREFIX}quasarzone/bbs/qb_saleinfo?kind=subject&keyword={product.keyword.replace(' ', '+')}"


def _percentile(sorted_values: list[float], ratio: float) -> float:
    """선형 보간 분위수 (스토어의 _percentile 과 같은 정의)."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * ratio
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def iqr_bounds(prices: list[float], multiplier: float = 1.5) -> tuple[float, float]:
    ordered = sorted(prices)
    q1, q3 = _percentile(ordered, 0.25), _percentile(ordered, 0.75)
    spread = q3 - q1
    return max(q1 - spread * multiplier, 0.0), q3 + spread * multiplier


def _poisson(rng: random.Random, lam: float) -> int:
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def _sale_windows(rng: random.Random) -> list[tuple[int, int, float]]:
    """(시작 일 offset, 길이, 추가 할인율). offset 은 과거 방향이 아니라 0=가장 오래된 날."""
    windows: list[tuple[int, int, float]] = []
    for slot in range(3):
        lo = slot * (HISTORY_DAYS // 3) + 2
        hi = (slot + 1) * (HISTORY_DAYS // 3) - 9
        windows.append((rng.randrange(lo, hi), rng.randrange(4, 8), rng.uniform(0.08, 0.15)))
    return windows


def make_rows(as_of: date, seed: int, next_post_id: int = FIRST_POST_ID) -> list[CrawlRow]:
    rows: list[CrawlRow] = []
    post_id = next_post_id
    now_cap = datetime.combine(as_of, datetime.max.time().replace(microsecond=0), tzinfo=KST)
    for product in PRODUCTS:
        rng = random.Random(f"{seed}:{product.family}")
        windows = _sale_windows(rng)
        x = 0.0  # 로그 편차
        posts: list[tuple[datetime, int]] = []
        for day_index in range(HISTORY_DAYS):
            day = as_of - timedelta(days=HISTORY_DAYS - 1 - day_index)
            x = 0.96 * x + rng.gauss(0, 0.008)
            event = max(
                (extra for start, length, extra in windows if start <= day_index < start + length),
                default=0.0,
            )
            for _ in range(_poisson(rng, POSTS_PER_DAY)):
                seconds = rng.randrange(8 * 3600, 23 * 3600)
                posted = datetime.combine(day, datetime.min.time(), tzinfo=KST) + timedelta(seconds=seconds)
                level = product.base_price * math.exp(x) * (1.0 - event) * (1.0 - rng.uniform(0.0, 0.10))
                posts.append((posted, max(1_000, int(round(level / 100.0)) * 100)))

        first_slot, second_slot = sorted(rng.sample(range(5, len(posts) - 5), 2))
        anomaly_factor = {first_slot: 10.0, second_slot: 0.1}  # 입력 실수: 0 하나 더, 0 하나 덜
        product_rows: list[CrawlRow] = []
        for index, (posted, price) in enumerate(posts):
            anomaly = index in anomaly_factor
            if anomaly:
                price = max(1_000, int(round(price * anomaly_factor[index] / 100.0)) * 100)
            fetched = posted + timedelta(minutes=rng.randrange(5, 90))
            last_seen = min(fetched + timedelta(hours=rng.randrange(0, 48)), now_cap)
            fetched = min(fetched, now_cap)
            mall = rng.choice(product.malls)
            title = product.title.format(mall=f"[{mall}]", price=f"{price:,}")
            product_rows.append(
                CrawlRow(
                    source=source_for(product),
                    post_id=str(post_id),
                    url=f"{DEMO_SOURCE_PREFIX}quasarzone/bbs/qb_saleinfo/views/{post_id}",
                    title=title,
                    price=str(price),
                    posted_at=posted.strftime("%Y.%m.%d"),
                    fetched_at=fetched,
                    first_seen_at=fetched,
                    last_seen_at=max(last_seen, fetched),
                    is_outlier=False,
                    outlier_reason=None,
                    outlier_marked_at=None,
                    item_family=product.family,
                    kind="anomaly" if anomaly else "normal",
                )
            )
            post_id += 1
        rows.extend(_mark_outliers(product_rows, product, now_cap))
    return rows


def _mark_outliers(product_rows: list[CrawlRow], product: Product, marked_at: datetime) -> list[CrawlRow]:
    lower, upper = iqr_bounds([float(r.price) for r in product_rows])
    reason = f"IQR_OUTLIER(channel={OUTLIER_CHANNEL},keyword={product.keyword.lower()},lower={int(lower)},upper={int(upper)})"
    marked = []
    for row in product_rows:
        price = float(row.price)
        if price < lower or price > upper:
            row = replace(row, is_outlier=True, outlier_reason=reason, outlier_marked_at=marked_at)
        marked.append(row)
    return marked


COLUMNS = (
    "source", "post_id", "url", "title", "price", "posted_at", "fetched_at", "first_seen_at", "last_seen_at",
    "is_outlier", "outlier_reason", "outlier_marked_at", "item_family",
)


def cleanup_sql() -> str:
    return f"DELETE FROM crawl_items WHERE source LIKE '{DEMO_SOURCE_PREFIX}%';"


def seed_sql(as_of: date, seed: int) -> str:
    rows = make_rows(as_of, seed)
    values = [
        [
            r.source, r.post_id, r.url, r.title, r.price, r.posted_at, r.fetched_at, r.first_seen_at, r.last_seen_at,
            r.is_outlier, r.outlier_reason, r.outlier_marked_at, r.item_family,
        ]
        for r in rows
    ]
    return "\n".join(
        [
            "-- 자동 생성 파일 (demo.py generate). 직접 고치지 말고 생성기를 고친다.",
            f"-- as_of={as_of.isoformat()} seed={seed}  — 전부 가짜 데이터다. 운영 DB 에 넣지 않는다.",
            "BEGIN;",
            cleanup_sql(),
            insert_rows("crawl_items", COLUMNS, values),
            "COMMIT;",
            "",
        ]
    )
