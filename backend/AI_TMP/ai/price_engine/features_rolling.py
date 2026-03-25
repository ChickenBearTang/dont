from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, pstdev


@dataclass(frozen=True)
class RollingPriceFeatures:
    avg_price_7d: float | None
    avg_price_30d: float | None
    min_price_30d: float | None
    max_price_30d: float | None
    price_volatility_30d: float | None
    shipping_fee_mode_30d: float | None
    seller_count_same_product: float
    release_age_days: float


def _window_values(
    history: list[dict[str, object]],
    *,
    now: datetime,
    days: int,
    key: str,
) -> list[float]:
    start = now - timedelta(days=days)
    values: list[float] = []
    for row in history:
        observed_at = row["observed_at"]
        if not isinstance(observed_at, datetime):
            continue
        if observed_at < start or observed_at >= now:
            continue
        value = row.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def compute_rolling_features(
    *,
    history: list[dict[str, object]],
    now: datetime,
    current_seller_id: str | None,
    first_observed_at: datetime,
) -> RollingPriceFeatures:
    prices_7d = _window_values(
        history, now=now, days=7, key="effective_price_candidate"
    )
    prices_30d = _window_values(
        history, now=now, days=30, key="effective_price_candidate"
    )
    shipping_30d = _window_values(history, now=now, days=30, key="shipping_fee")

    avg_price_7d = mean(prices_7d) if prices_7d else None
    avg_price_30d = mean(prices_30d) if prices_30d else None
    min_price_30d = min(prices_30d) if prices_30d else None
    max_price_30d = max(prices_30d) if prices_30d else None
    volatility_30d = pstdev(prices_30d) if len(prices_30d) >= 2 else None

    shipping_mode: float | None = None
    if shipping_30d:
        counts: dict[float, int] = {}
        for fee in shipping_30d:
            counts[fee] = counts.get(fee, 0) + 1
        shipping_mode = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[0][
            0
        ]

    seller_ids = {
        row.get("seller_id_candidate")
        for row in history
        if isinstance(row.get("seller_id_candidate"), str)
    }
    if current_seller_id:
        seller_ids.add(current_seller_id)

    release_age_days = max((now - first_observed_at).days, 0)
    return RollingPriceFeatures(
        avg_price_7d=avg_price_7d,
        avg_price_30d=avg_price_30d,
        min_price_30d=min_price_30d,
        max_price_30d=max_price_30d,
        price_volatility_30d=volatility_30d,
        shipping_fee_mode_30d=shipping_mode,
        seller_count_same_product=float(max(len(seller_ids), 1)),
        release_age_days=float(release_age_days),
    )
