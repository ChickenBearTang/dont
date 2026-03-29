from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..price_engine.schema_models import PriceFeatureSnapshotRow
from ..price_engine.split import time_based_split


class PriceEngineSplitTest(unittest.TestCase):
    def test_time_based_split_only(self) -> None:
        a = datetime(2026, 1, 1, tzinfo=timezone.utc)
        b = datetime(2026, 1, 5, tzinfo=timezone.utc)
        c = datetime(2026, 1, 10, tzinfo=timezone.utc)

        rows = [
            PriceFeatureSnapshotRow(
                canonical_product_id="p",
                variant_id=None,
                seller_id="s",
                snapshot_date=a,
                current_effective_price=1000,
                avg_price_7d=None,
                avg_price_30d=None,
                min_price_30d=None,
                max_price_30d=None,
                price_volatility_30d=None,
                seller_count_same_product=1,
                release_age_days=0,
                shipping_fee_mode_30d=None,
                price_vs_avg_7d=None,
                price_vs_avg_30d=None,
                price_to_min_30d_gap=None,
                price_to_max_30d_gap=None,
                brand="b",
                category="c",
                seller_type="merchant",
                availability_status="in_stock",
            ),
            PriceFeatureSnapshotRow(
                canonical_product_id="p",
                variant_id=None,
                seller_id="s",
                snapshot_date=b,
                current_effective_price=1100,
                avg_price_7d=1000,
                avg_price_30d=1000,
                min_price_30d=1000,
                max_price_30d=1000,
                price_volatility_30d=0,
                seller_count_same_product=1,
                release_age_days=4,
                shipping_fee_mode_30d=0,
                price_vs_avg_7d=1.1,
                price_vs_avg_30d=1.1,
                price_to_min_30d_gap=100,
                price_to_max_30d_gap=-100,
                brand="b",
                category="c",
                seller_type="merchant",
                availability_status="in_stock",
            ),
        ]

        split = time_based_split(rows, cutoff_date=c)
        self.assertEqual(len(split.train), 2)
        self.assertEqual(len(split.test), 0)


if __name__ == "__main__":
    unittest.main()
