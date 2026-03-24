from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..price_engine.allowlist import SCHEMA_VERSION
from ..price_engine.schema_models import PriceObservation
from ..price_engine.schema_validator import (
    SchemaValidationError,
    enforce_null_reserved_fields,
    validate_schema_version,
)


class PriceEngineSchemaTest(unittest.TestCase):
    def test_schema_version_mismatch_fails_fast(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_schema_version("v0")

    def test_reserved_fields_keep_null_not_zero(self) -> None:
        with self.assertRaises(SchemaValidationError):
            enforce_null_reserved_fields({"coupon_discount_amount": 0})

        enforce_null_reserved_fields({"coupon_discount_amount": None})

    def test_price_observation_schema_version_defaults_to_expected(self) -> None:
        row = PriceObservation(
            canonical_product_id_candidate="p-1",
            variant_id_candidate=None,
            seller_id_candidate="s-1",
            observed_at=datetime.now(timezone.utc),
            listed_price=1000,
            shipping_fee=0,
            effective_price_candidate=1000,
            availability_status="in_stock",
            stock_status="normal",
            source_site="site-a",
            source_priority="merchant",
            confidence=0.9,
            evidence_refs=[],
            normalization_version="v1",
        )
        self.assertEqual(row.schema_version, SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
