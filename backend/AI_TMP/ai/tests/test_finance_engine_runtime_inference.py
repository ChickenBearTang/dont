from __future__ import annotations

import unittest
from unittest.mock import patch

from ..finance_engine.allowlist import SCHEMA_VERSION, TARGET_NAME, training_feature_names
from ..finance_engine.inference import (
    build_finance_inference_payload,
    predict_finance_signal,
)


class _FakeFinanceModel:
    classes_ = ["low", "medium", "high"]

    def predict_proba(self, frame):
        _ = frame
        return [[0.2, 0.3, 0.5]]


class _FakeFinanceArtifact:
    def __init__(self) -> None:
        self.model = _FakeFinanceModel()
        self.metadata = {
            "schema_version": SCHEMA_VERSION,
            "model_family": "lightgbm_classifier",
            "target_name": TARGET_NAME,
            "feature_names": list(training_feature_names()),
        }


class FinanceEngineRuntimeInferenceTest(unittest.TestCase):
    def test_build_inference_payload_matches_allowlist(self) -> None:
        payload = build_finance_inference_payload(
            current_price=200_000,
            finance_profile={
                "current_balance": 1_100_000,
                "emergency_fund_balance": 700_000,
                "expected_card_payment_amount": 120_000,
                "days_until_card_due": 9,
                "savebox_balance": 900_000,
                "available_fixed_expense": 450_000,
                "available_fixed_income": 520_000,
            },
            window_stats={"30d": {"avg_price": 70_000, "count": 18}},
        )
        self.assertEqual(set(payload.keys()), set(training_feature_names()))
        self.assertGreater(payload["monthly_spending_30d_estimate"], 0)

    def test_predict_finance_signal_returns_disabled_when_flag_is_off(self) -> None:
        signal, state = predict_finance_signal(
            current_price=1000,
            finance_profile={},
            window_stats=None,
            enabled=False,
        )
        self.assertEqual(signal, {})
        self.assertFalse(state["enabled"])
        self.assertEqual(state["reason"], "finance_model_disabled")

    def test_predict_finance_signal_uses_loaded_artifact(self) -> None:
        with patch(
            "ai.finance_engine.inference._load_cached_artifact",
            return_value=_FakeFinanceArtifact(),
        ):
            signal, state = predict_finance_signal(
                current_price=120_000,
                finance_profile={
                    "current_balance": 1_500_000,
                    "emergency_fund_balance": 500_000,
                    "expected_card_payment_amount": 200_000,
                    "days_until_card_due": 7,
                    "savebox_balance": 700_000,
                    "available_fixed_expense": 400_000,
                    "available_fixed_income": 450_000,
                },
                window_stats={"30d": {"avg_price": 60_000, "count": 20}},
                enabled=True,
                explicit_model_path="C:/tmp/fake-finance-model",
            )

        self.assertTrue(state["enabled"])
        self.assertEqual(state["backend"], "lightgbm_classifier")
        self.assertEqual(signal["finance_model_risk_bucket"], "high")
        self.assertIn("finance_model_risk_score", signal)


if __name__ == "__main__":
    unittest.main()
