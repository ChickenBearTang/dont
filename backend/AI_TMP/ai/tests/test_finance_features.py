"""파생 비율을 모델 안쪽(features.py 한 곳)에서 계산하는지 확인한다.

핵심 약속: 호출하는 쪽은 원본 7개만 준다. 파생 3개는 학습과 추론이 같은 함수로
계산하므로 정의가 갈라질 수 없다.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ..finance_engine.allowlist import (
    DERIVED_FEATURE_NAMES,
    raw_input_names,
    training_feature_names,
)
from ..finance_engine.features import build_feature_frame, derive_model_features
from ..finance_engine.synthetic import generate_rows

RAW = {
    "current_balance": 1_000_000.0,
    "emergency_fund_balance": 500_000.0,
    "savebox_balance": 400_000.0,
    "expected_card_payment_amount": 100_000.0,
    "days_until_card_due": 10.0,
    "monthly_spending_30d": 1_000_000.0,
    "product_price": 250_000.0,
}


class DeriveModelFeaturesTest(unittest.TestCase):
    def test_파생_값이_정의대로_계산된다(self) -> None:
        out = derive_model_features(RAW)

        self.assertAlmostEqual(out["product_price_vs_monthly_spending"], 0.25)
        self.assertAlmostEqual(out["projected_balance_after_purchase"], 150_000.0)
        self.assertAlmostEqual(out["product_price_vs_emergency_fund"], 0.5)

    def test_열_순서가_모델_열과_같다(self) -> None:
        self.assertEqual(tuple(derive_model_features(RAW)), training_feature_names())

    def test_0으로_나누지_않는다(self) -> None:
        out = derive_model_features({**RAW, "monthly_spending_30d": 0.0, "emergency_fund_balance": 0.0})

        self.assertAlmostEqual(out["product_price_vs_monthly_spending"], 250_000.0)
        self.assertAlmostEqual(out["product_price_vs_emergency_fund"], 250_000.0)

    def test_원본이_빠지면_어떤_키인지_밝히며_실패한다(self) -> None:
        broken = {k: v for k, v in RAW.items() if k != "savebox_balance"}

        with self.assertRaises(ValueError) as ctx:
            derive_model_features(broken)
        self.assertIn("savebox_balance", str(ctx.exception))

    def test_행에_낡은_파생_값이_있어도_다시_계산한다(self) -> None:
        """예전 열이 남은 데이터가 몰래 학습에 쓰이면 안 된다."""
        stale = {**RAW, "product_price_vs_monthly_spending": 999.0}

        self.assertAlmostEqual(
            derive_model_features(stale)["product_price_vs_monthly_spending"], 0.25
        )


class BuildFeatureFrameTest(unittest.TestCase):
    def test_프레임은_모델_열_순서이고_행_수가_같다(self) -> None:
        frame = build_feature_frame([RAW, {**RAW, "product_price": 10_000.0}])

        self.assertEqual(list(frame.columns), list(training_feature_names()))
        self.assertEqual(len(frame), 2)


class TrainServeConsistencyTest(unittest.TestCase):
    def test_합성_데이터의_파생_열이_모델과_같은_함수로_계산된다(self) -> None:
        for row in generate_rows(row_count=20, seed=3):
            expected = derive_model_features(row)
            for name in DERIVED_FEATURE_NAMES:
                self.assertAlmostEqual(row[name], expected[name], msg=name)

    def test_추론이_모델에_넘기는_프레임이_학습과_같은_변환을_거친다(self) -> None:
        """호출하는 쪽 입력(7개)만으로 모델 열 10개가 만들어져 모델에 들어간다."""
        from ..finance_engine.allowlist import SCHEMA_VERSION, TARGET_NAME
        from ..finance_engine.inference import predict_finance_signal

        seen = {}

        class _Spy:
            classes_ = ["low", "medium", "high"]

            def predict_proba(self, frame):
                seen["frame"] = frame
                return [[0.6, 0.3, 0.1]]

        class _Artifact:
            model = _Spy()
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "model_family": "lightgbm_classifier",
                "target_name": TARGET_NAME,
                "feature_names": list(training_feature_names()),
            }

        profile = {k: v for k, v in RAW.items() if k != "product_price"}
        with patch("ai.finance_engine.inference._load_cached_artifact", return_value=_Artifact()):
            predict_finance_signal(
                current_price=250_000,
                finance_profile=profile,
                enabled=True,
                explicit_model_path="x",
            )

        frame = seen["frame"]
        self.assertEqual(list(frame.columns), list(training_feature_names()))
        self.assertAlmostEqual(float(frame["product_price_vs_monthly_spending"][0]), 0.25)
        self.assertAlmostEqual(float(frame["projected_balance_after_purchase"][0]), 150_000.0)

    def test_호출하는_쪽_입력은_7개다(self) -> None:
        self.assertEqual(len(raw_input_names()), 7)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
