from __future__ import annotations

import unittest

from ..price_engine.allowlist import training_feature_names
from ..price_engine.schema_validator import (
    SchemaValidationError,
    validate_inference_payload,
)


class PriceEngineInferenceValidatorTest(unittest.TestCase):
    def test_validate_inference_payload_accepts_exact_allowlist(self) -> None:
        payload: dict[str, object] = {name: 0.0 for name in training_feature_names()}
        for categorical_name in (
            "brand",
            "category",
            "seller_type",
            "availability_status",
        ):
            payload[categorical_name] = "unknown"

        validate_inference_payload(payload)

    def test_validate_inference_payload_rejects_unknown_or_missing_fields(self) -> None:
        payload: dict[str, object] = {name: 0.0 for name in training_feature_names()}
        for categorical_name in (
            "brand",
            "category",
            "seller_type",
            "availability_status",
        ):
            payload[categorical_name] = "unknown"

        payload["post_url"] = "https://example.com/raw"
        with self.assertRaises(SchemaValidationError):
            validate_inference_payload(payload)

        payload.pop("post_url")
        payload.pop("current_effective_price")
        with self.assertRaises(SchemaValidationError):
            validate_inference_payload(payload)


if __name__ == "__main__":
    unittest.main()
