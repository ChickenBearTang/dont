from __future__ import annotations

import unittest
from unittest.mock import patch

from ..price_engine.allowlist import SCHEMA_VERSION, training_feature_names
from ..price_engine.inference import (
    build_price_inference_payload,
    predict_price_signal,
)


class _FakeModel:
    def predict(self, frame):
        _ = frame
        return [900.0]


class _FakeArtifact:
    def __init__(self) -> None:
        self.model = _FakeModel()
        self.metadata = {
            "schema_version": SCHEMA_VERSION,
            "model_family": "lightgbm_regressor",
            "target_name": "current_effective_price",
            "feature_names": list(training_feature_names()),
        }


class PriceEngineRuntimeInferenceTest(unittest.TestCase):
    def test_build_inference_payload_matches_allowlist(self) -> None:
        payload = build_price_inference_payload(
            current_price=1000,
            window_stats={"30d": {"avg_price": 1100, "min_price": 900, "max_price": 1300}},
            category="IT",
        )
        self.assertEqual(set(payload.keys()), set(training_feature_names()))
        self.assertEqual(payload["category"], "IT")
        self.assertGreater(payload["avg_price_30d"], 0)

    def test_predict_price_signal_returns_disabled_when_flag_is_off(self) -> None:
        signal, state = predict_price_signal(
            current_price=1000,
            window_stats=None,
            category="IT",
            enabled=False,
        )
        self.assertEqual(signal, {})
        self.assertFalse(state["enabled"])
        self.assertEqual(state["reason"], "price_model_disabled")

    def test_predict_price_signal_returns_path_missing_when_enabled_without_path(self) -> None:
        signal, state = predict_price_signal(
            current_price=1000,
            window_stats=None,
            category="IT",
            enabled=True,
            explicit_model_path=None,
        )
        self.assertEqual(signal, {})
        self.assertFalse(state["enabled"])
        self.assertEqual(state["reason"], "model_path_missing")

    def test_predict_price_signal_uses_loaded_artifact(self) -> None:
        with patch("ai.price_engine.inference._load_cached_artifact", return_value=_FakeArtifact()):
            signal, state = predict_price_signal(
                current_price=1000,
                window_stats={"30d": {"avg_price": 1200, "min_price": 900, "max_price": 1300}},
                category="IT",
                enabled=True,
                explicit_model_path="C:/tmp/fake-model",
            )

        self.assertTrue(state["enabled"])
        self.assertEqual(state["backend"], "lightgbm_regressor")
        self.assertIn("price_model_gap_score", signal)
        self.assertIn("predicted_price", state)


if __name__ == "__main__":
    unittest.main()
