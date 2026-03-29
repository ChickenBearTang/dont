from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from ..price_engine.schema_models import PriceFeatureSnapshotRow
from ..price_engine.train_lgbm import train_mvp_v1_5


class PriceEngineTrainLgbmTest(unittest.TestCase):
    def test_train_accepts_categorical_columns(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows: list[PriceFeatureSnapshotRow] = []
        for index in range(120):
            current_price = 150000.0 + float(index * 500)
            rows.append(
                PriceFeatureSnapshotRow(
                    canonical_product_id="product-1",
                    variant_id="variant-a",
                    seller_id=f"seller-{index % 4}",
                    snapshot_date=start + timedelta(days=index),
                    current_effective_price=current_price,
                    avg_price_7d=current_price * 1.01,
                    avg_price_30d=current_price * 1.02,
                    min_price_30d=current_price * 0.95,
                    max_price_30d=current_price * 1.08,
                    price_volatility_30d=1200.0 + float(index % 7),
                    seller_count_same_product=float((index % 4) + 1),
                    release_age_days=200.0 + float(index),
                    shipping_fee_mode_30d=float((index % 3) * 2500),
                    price_vs_avg_7d=0.99,
                    price_vs_avg_30d=0.98,
                    price_to_min_30d_gap=current_price * 0.05,
                    price_to_max_30d_gap=current_price * 0.08,
                    brand="brand-a" if index % 2 == 0 else "brand-b",
                    category="earbuds",
                    seller_type="official" if index % 2 == 0 else "reseller",
                    availability_status="in_stock" if index % 3 != 0 else "low_stock",
                )
            )

        model = train_mvp_v1_5(rows, params={"n_jobs": 1})
        self.assertEqual(model.__class__.__name__, "LGBMRegressor")


if __name__ == "__main__":
    unittest.main()
