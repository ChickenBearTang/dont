from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .schema_models import PriceFeatureSnapshotRow


@dataclass(frozen=True)
class TimeSplitResult:
    train: list[PriceFeatureSnapshotRow]
    test: list[PriceFeatureSnapshotRow]


def time_based_split(
    rows: list[PriceFeatureSnapshotRow],
    *,
    cutoff_date: datetime,
) -> TimeSplitResult:
    ordered = sorted(rows, key=lambda row: row.snapshot_date)
    train = [row for row in ordered if row.snapshot_date < cutoff_date]
    test = [row for row in ordered if row.snapshot_date >= cutoff_date]

    if (
        train
        and test
        and max(item.snapshot_date for item in train)
        >= min(item.snapshot_date for item in test)
    ):
        raise ValueError("time split leakage detected")

    return TimeSplitResult(train=train, test=test)
