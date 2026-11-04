from __future__ import annotations

import unittest
from unittest.mock import patch

from ..price_engine.allowlist import SCHEMA_VERSION, training_feature_names
from ..price_engine.inference import (
    build_price_inference_payload,
    predict_price_signal,
)
from ..validation import TrustVerdict


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
        # 이 테스트는 추론 경로 자체를 본다. 신뢰 관문은 아래 별도 테스트에서 검증한다.
        with patch("ai.price_engine.inference._load_cached_artifact", return_value=_FakeArtifact()), patch(
            "ai.price_engine.inference.assess_price_artifact", return_value=TrustVerdict(True, [])
        ):
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


class PriceModelTrustGateTest(unittest.TestCase):
    """신뢰할 수 없는 가격 모델의 숫자는 구매 판단에 섞지 않는다."""

    def _predict(self):
        return predict_price_signal(
            current_price=89_000,
            window_stats=None,
            category="keyboard",
            enabled=True,
            explicit_model_path="C:/tmp/fake-model",
        )

    def test_정답이_피처에_있는_아티팩트는_신호를_내지_않는다(self) -> None:
        with patch("ai.price_engine.inference._load_cached_artifact", return_value=_FakeArtifact()):
            signal, state = self._predict()

        self.assertEqual(signal, {})
        self.assertFalse(state["enabled"])
        self.assertEqual(state["reason"], "price_model_untrusted")
        self.assertIn("TARGET_IN_FEATURES", state["untrusted_reasons"])

    def test_저장소의_운영_가격_모델이_실제로_막힌다(self) -> None:
        """어떤 가격을 넣어도 36,707원을 답하던 모델이다 (정답 누수 + 상품 1개 67행)."""
        signal, state = predict_price_signal(
            current_price=89_000, window_stats=None, category="keyboard", enabled=True,
            explicit_model_path=str(__import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "artifacts" / "price_retrain_model"),
        )

        self.assertEqual(signal, {})
        self.assertEqual(state["reason"], "price_model_untrusted")

    def test_환경변수로_명시하면_실험용으로_우회할_수_있다(self) -> None:
        with patch("ai.price_engine.inference._load_cached_artifact", return_value=_FakeArtifact()), patch.dict(
            "os.environ", {"AI_PRICE_MODEL_ALLOW_UNTRUSTED": "1"}
        ):
            signal, state = self._predict()

        self.assertTrue(state["enabled"])
        self.assertIn("price_model_gap_score", signal)

    def test_신뢰하면_통과한다(self) -> None:
        with patch("ai.price_engine.inference._load_cached_artifact", return_value=_FakeArtifact()), patch(
            "ai.price_engine.inference.assess_price_artifact", return_value=TrustVerdict(True, [])
        ):
            _, state = self._predict()

        self.assertTrue(state["enabled"])


if __name__ == "__main__":
    unittest.main()
