from __future__ import annotations

import importlib
import unittest

ReasoningEngine = importlib.import_module("ai.xai.reasoning").ReasoningEngine
canonical_reasons = importlib.import_module("ai.xai.purchase_core.reasons")


class ReasoningEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ReasoningEngine()

    def test_analyze_is_stable_and_deterministic_with_ties(self) -> None:
        feature_scores = {
            "shipping_fee": -0.7,
            "avg_price_30d": 0.7,
            "unknown_feature": 0.7,
            "current_price": 0.1,
        }

        first = self.engine.analyze(feature_scores, top_k=3)
        second = self.engine.analyze(feature_scores, top_k=3)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(first[0]["reason_code"], "PRICE_RELATIVE_TO_30D_AVG")
        self.assertEqual(
            first[1]["reason_code"], "SHIPPING_COST_REDUCES_ATTRACTIVENESS"
        )
        self.assertEqual(first[2]["reason_code"], "DECISION_FEATURE_SIGNAL")

    def test_known_feature_reuses_canonical_reason_catalog_with_output_shape(
        self,
    ) -> None:
        reasons = self.engine.analyze({"current_price": 0.25}, top_k=1)

        self.assertEqual(len(reasons), 1)
        reason = reasons[0]
        expected_code, expected_source_type = canonical_reasons.REASON_CODE_MAP[
            "current_price"
        ]
        self.assertEqual(reason["reason_code"], expected_code)
        self.assertEqual(
            reason["reason_text"], canonical_reasons.REASON_TEXT[expected_code]
        )
        self.assertEqual(reason["source_type"], expected_source_type)

        self.assertSetEqual(
            set(reason.keys()),
            {
                "reason_code",
                "reason_text",
                "feature",
                "score",
                "abs_score",
                "impact_direction",
                "shap_like_value",
                "source_type",
            },
        )

    def test_empty_input_returns_fallback_reason(self) -> None:
        reasons = self.engine.analyze({}, top_k=3)
        self.assertEqual(len(reasons), 1)
        self.assertEqual(reasons[0]["reason_code"], "NO_VALID_FEATURE_SCORES")

    def test_invalid_scores_do_not_crash_and_return_fallback(self) -> None:
        feature_scores = {
            "avg_price_30d": "not-a-number",
            "shipping_fee": None,
        }
        reasons = self.engine.analyze(feature_scores, top_k=2)

        self.assertEqual(len(reasons), 1)
        self.assertEqual(reasons[0]["reason_code"], "NO_VALID_FEATURE_SCORES")

    def test_top_k_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.analyze({"avg_price_30d": 1.0}, top_k=0)

    def test_reason_texts_are_localized_in_korean_for_known_features(self) -> None:
        reasons = self.engine.analyze(
            {"product_price_vs_monthly_spending": 1.0},
            top_k=1,
        )

        self.assertEqual(len(reasons), 1)
        self.assertRegex(str(reasons[0]["reason_text"]), r"[가-힣]")

    def test_fallback_reason_text_is_localized_in_korean(self) -> None:
        reasons = self.engine.analyze({}, top_k=1)

        self.assertEqual(len(reasons), 1)
        self.assertRegex(str(reasons[0]["reason_text"]), r"[가-힣]")


if __name__ == "__main__":
    unittest.main()
