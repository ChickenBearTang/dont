from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from ..price_engine.allowlist import training_feature_names
from ..price_engine.dataset_builder import build_price_feature_snapshot_v1
from ..price_engine.normalizer import merge_to_price_observation
from ..price_engine.schema_models import RawListing, RawMerchantOffer
from ..price_engine.schema_validator import validate_training_columns


class PriceEngineDatasetTest(unittest.TestCase):
    def test_source_priority_prefers_merchant(self) -> None:
        now = datetime.now(timezone.utc)
        listing = RawListing(
            source_site="qz",
            post_url="https://example.com/post/1",
            post_id_raw="1",
            title_raw="GPU 할인",
            merchant_raw_hint="shop-a",
            category_raw="gpu",
            price_raw="500,000",
            shipping_raw="3,000",
            created_at_raw=None,
            crawled_at=now,
            html_hash="h1",
        )
        merchant = RawMerchantOffer(
            merchant_url="https://merchant.example.com/item/1",
            merchant_domain="merchant.example.com",
            seller_name_raw="shop-a",
            product_name_raw="gpu-1",
            brand_raw="brand-a",
            gtin_raw="123",
            mpn_raw="mpn-1",
            model_code_raw="m1",
            listed_price_raw="490,000",
            original_price_raw=None,
            sale_price_raw="470,000",
            shipping_fee_raw="0",
            availability_raw="in_stock",
            stock_raw="ok",
            raw_jsonld=None,
            crawled_at=now,
            html_hash="h2",
        )

        observation = merge_to_price_observation(
            listing,
            None,
            merchant,
            observed_at=now,
        )
        self.assertEqual(observation.source_priority, "merchant")
        self.assertEqual(observation.listed_price, 470000)
        self.assertEqual(observation.shipping_fee, 0)
        self.assertEqual(observation.effective_price_candidate, 470000)

    def test_allowlist_only_training_columns(self) -> None:
        validate_training_columns(list(training_feature_names()))
        with self.assertRaises(Exception):
            validate_training_columns(["current_effective_price", "post_url"])

    def test_dataset_builder_excludes_null_effective_price_from_training(self) -> None:
        now = datetime.now(timezone.utc)
        listing_ok = RawListing(
            source_site="qz",
            post_url="https://example.com/post/ok",
            post_id_raw="ok",
            title_raw="SSD 특가",
            merchant_raw_hint=None,
            category_raw="storage",
            price_raw="120,000",
            shipping_raw="0",
            created_at_raw=None,
            crawled_at=now,
            html_hash="h-ok",
        )
        listing_missing = RawListing(
            source_site="qz",
            post_url="https://example.com/post/missing",
            post_id_raw="missing",
            title_raw="SSD 특가",
            merchant_raw_hint=None,
            category_raw="storage",
            price_raw="120,000",
            shipping_raw=None,
            created_at_raw=None,
            crawled_at=now,
            html_hash="h-missing",
        )

        rows = [
            merge_to_price_observation(
                listing_ok, None, None, observed_at=now - timedelta(days=1)
            ),
            merge_to_price_observation(listing_missing, None, None, observed_at=now),
        ]

        built = build_price_feature_snapshot_v1(rows)
        self.assertEqual(len(built.raw_records), 2)
        self.assertEqual(len(built.training_rows), 1)


if __name__ == "__main__":
    unittest.main()
