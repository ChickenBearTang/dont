from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .features_rolling import compute_rolling_features
from .schema_models import (
    DatasetBuildResult,
    PriceFeatureSnapshotRow,
    PriceObservation,
)
from .schema_validator import (
    validate_price_observation,
    validate_training_row,
)


def _dedupe_key(
    observation: PriceObservation,
) -> tuple[str, str | None, datetime, int | None]:
    return (
        observation.canonical_product_id_candidate,
        observation.seller_id_candidate,
        observation.observed_at,
        observation.effective_price_candidate,
    )


def _ratio(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


def build_price_feature_snapshot_v1(
    observations: list[PriceObservation],
) -> DatasetBuildResult:
    cleaned: list[PriceObservation] = []
    seen_keys: set[tuple[str, str | None, datetime, int | None]] = set()

    for observation in sorted(observations, key=lambda item: item.observed_at):
        validate_price_observation(observation)
        dedupe = _dedupe_key(observation)
        if dedupe in seen_keys:
            continue
        seen_keys.add(dedupe)
        cleaned.append(observation)

    grouped: dict[str, list[PriceObservation]] = defaultdict(list)
    for row in cleaned:
        grouped[row.canonical_product_id_candidate].append(row)

    training_rows: list[PriceFeatureSnapshotRow] = []

    for canonical_id, rows in grouped.items():
        rows_sorted = sorted(rows, key=lambda item: item.observed_at)
        if not rows_sorted:
            continue
        first_observed_at = rows_sorted[0].observed_at
        history_records: list[dict[str, object]] = []

        for row in rows_sorted:
            if row.listed_price is None or row.listed_price <= 0:
                history_records.append(row.__dict__)
                continue
            if row.shipping_fee is not None and row.shipping_fee < 0:
                history_records.append(row.__dict__)
                continue
            if row.effective_price_candidate is None:
                history_records.append(row.__dict__)
                continue

            rolling = compute_rolling_features(
                history=history_records,
                now=row.observed_at,
                current_seller_id=row.seller_id_candidate,
                first_observed_at=first_observed_at,
            )
            current_price = float(row.effective_price_candidate)

            training_row = PriceFeatureSnapshotRow(
                canonical_product_id=canonical_id,
                variant_id=row.variant_id_candidate,
                seller_id=row.seller_id_candidate,
                snapshot_date=row.observed_at,
                current_effective_price=current_price,
                avg_price_7d=rolling.avg_price_7d,
                avg_price_30d=rolling.avg_price_30d,
                min_price_30d=rolling.min_price_30d,
                max_price_30d=rolling.max_price_30d,
                price_volatility_30d=rolling.price_volatility_30d,
                seller_count_same_product=rolling.seller_count_same_product,
                release_age_days=rolling.release_age_days,
                shipping_fee_mode_30d=rolling.shipping_fee_mode_30d,
                price_vs_avg_7d=_ratio(current_price, rolling.avg_price_7d),
                price_vs_avg_30d=_ratio(current_price, rolling.avg_price_30d),
                price_to_min_30d_gap=(
                    current_price - rolling.min_price_30d
                    if rolling.min_price_30d is not None
                    else None
                ),
                price_to_max_30d_gap=(
                    rolling.max_price_30d - current_price
                    if rolling.max_price_30d is not None
                    else None
                ),
                brand=row.brand or "unknown",
                category=row.category or "unknown",
                seller_type=row.seller_type or "unknown",
                availability_status=row.availability_status or "unknown",
            )
            validate_training_row(training_row)
            training_rows.append(training_row)
            history_records.append(row.__dict__)

    return DatasetBuildResult(raw_records=cleaned, training_rows=training_rows)
