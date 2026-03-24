from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from ..price_engine.features_rolling import compute_rolling_features


class PriceEngineRollingTest(unittest.TestCase):
    def test_no_future_leakage_for_rolling_features(self) -> None:
        base = datetime(2026, 1, 10, tzinfo=timezone.utc)
        history = [
            {
                "observed_at": base - timedelta(days=2),
                "effective_price_candidate": 1000,
                "shipping_fee": 0,
                "seller_id_candidate": "s1",
            },
            {
                "observed_at": base - timedelta(days=1),
                "effective_price_candidate": 1100,
                "shipping_fee": 0,
                "seller_id_candidate": "s2",
            },
            {
                "observed_at": base + timedelta(days=1),
                "effective_price_candidate": 10,
                "shipping_fee": 0,
                "seller_id_candidate": "s3",
            },
        ]

        rolling = compute_rolling_features(
            history=history,
            now=base,
            current_seller_id="s1",
            first_observed_at=base - timedelta(days=2),
        )
        self.assertEqual(rolling.avg_price_7d, 1050.0)
        self.assertEqual(rolling.min_price_30d, 1000.0)
        self.assertEqual(rolling.max_price_30d, 1100.0)


if __name__ == "__main__":
    unittest.main()
