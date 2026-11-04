from __future__ import annotations

import unittest
from unittest.mock import patch

from ..finance_engine.allowlist import (
    SCHEMA_VERSION,
    TARGET_NAME,
    raw_input_names,
    training_feature_names,
)
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
    def test_build_inference_payload_는_원본_입력과_같다(self) -> None:
        payload = build_finance_inference_payload(
            current_price=200_000,
            finance_profile={
                "current_balance": 1_100_000,
                "emergency_fund_balance": 700_000,
                "expected_card_payment_amount": 120_000,
                "days_until_card_due": 9,
                "savebox_balance": 900_000,
                "monthly_spending_30d": 1_300_000,
            },
        )
        self.assertEqual(set(payload.keys()), set(raw_input_names()))
        self.assertEqual(payload["monthly_spending_30d"], 1_300_000.0)
        self.assertEqual(payload["product_price"], 200_000.0)

    def test_payload는_프로필에_없는_키를_기본값으로_메우지_않는다(self) -> None:
        """예전에는 `.get(키, 0.0)` 과 소득 1_000_000 이 조용히 들어갔다."""
        with self.assertRaises(ValueError) as ctx:
            build_finance_inference_payload(
                current_price=200_000,
                finance_profile={"current_balance": 1_100_000},
            )
        self.assertIn("monthly_spending_30d", str(ctx.exception))

    def test_payload에_파생_비율이_없다(self) -> None:
        payload = build_finance_inference_payload(
            current_price=200_000,
            finance_profile={
                "current_balance": 1, "emergency_fund_balance": 1,
                "expected_card_payment_amount": 1, "days_until_card_due": 1,
                "savebox_balance": 1, "monthly_spending_30d": 1,
            },
        )
        for derived in (
            "product_price_vs_monthly_spending",
            "projected_balance_after_purchase",
            "product_price_vs_emergency_fund",
            "available_fixed_income",
            "available_fixed_expense",
        ):
            self.assertNotIn(derived, payload)

    def test_predict_finance_signal_returns_disabled_when_flag_is_off(self) -> None:
        signal, state = predict_finance_signal(
            current_price=1000,
            finance_profile={},
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
                    "monthly_spending_30d": 900_000,
                },
                enabled=True,
                explicit_model_path="C:/tmp/fake-finance-model",
            )

        self.assertTrue(state["enabled"])
        self.assertEqual(state["backend"], "lightgbm_classifier")
        self.assertEqual(signal["finance_model_risk_bucket"], "high")
        self.assertIn("finance_model_risk_score", signal)


if __name__ == "__main__":
    unittest.main()
