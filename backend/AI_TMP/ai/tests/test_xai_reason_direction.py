"""설명 문구가 값의 방향(부호)과 일치하는지 확인한다.

예전 문제: 점수의 부호와 상관없이 문구가 고정이었다. 형편이 좋은 사용자에게도
"비상자금 수준이 낮아 재무 안정성이 부족합니다"가 나왔다.

규칙: signed=True 일 때 score 는 '구매에 유리한 정도'다.
      양수 = 유리, 음수 = 불리, 0 근처 = 영향 미미.
signed=False(기본)는 부호의 뜻이 정해지지 않은 예전 점수용이라 문구를 바꾸지 않는다.
"""

from __future__ import annotations

import importlib
import unittest

reasons = importlib.import_module("ai.xai.purchase_core.reasons")
ReasoningEngine = importlib.import_module("ai.xai.reasoning").ReasoningEngine

DIRECTIONAL_FEATURES = (
    "avg_price_30d",
    "price_model_gap_score",
    "emergency_fund_balance",
    "projected_balance_after_purchase",
    "product_price_vs_monthly_spending",
    "days_until_card_due",
)


class SignedReasonTextTest(unittest.TestCase):
    def test_양수는_유리한_문구_음수는_불리한_문구_0근처는_중립_문구다(self) -> None:
        for feature in DIRECTIONAL_FEATURES:
            with self.subTest(feature=feature):
                good = reasons.build_reason_item(feature, 1.0, signed=True)
                bad = reasons.build_reason_item(feature, -1.0, signed=True)
                flat = reasons.build_reason_item(feature, 0.0, signed=True)

                self.assertEqual(len({good.reason_text, bad.reason_text, flat.reason_text}), 3)

    def test_비상자금이_충분하면_부족하다고_말하지_않는다(self) -> None:
        good = reasons.build_reason_item("emergency_fund_balance", 1.2, signed=True)
        bad = reasons.build_reason_item("emergency_fund_balance", -1.2, signed=True)

        self.assertNotIn("부족", good.reason_text)
        self.assertIn("충분", good.reason_text)
        self.assertIn("낮아", bad.reason_text)

    def test_평균가보다_싸면_높다고_말하지_않는다(self) -> None:
        good = reasons.build_reason_item("avg_price_30d", 0.4, signed=True)
        bad = reasons.build_reason_item("avg_price_30d", -0.4, signed=True)

        self.assertIn("낮", good.reason_text)
        self.assertNotIn("높게", good.reason_text)
        self.assertIn("높게", bad.reason_text)

    def test_가격모델_신호도_방향을_말한다(self) -> None:
        good = reasons.build_reason_item("price_model_gap_score", 0.5, signed=True)
        bad = reasons.build_reason_item("price_model_gap_score", -0.5, signed=True)

        self.assertIn("낮", good.reason_text)
        self.assertIn("높", bad.reason_text)

    def test_불리한_문구는_예전_문구와_같다(self) -> None:
        """예전 문구는 사실 '불리한 경우'를 말하고 있었다. 그 문구는 보존한다."""
        for feature in ("emergency_fund_balance", "projected_balance_after_purchase",
                        "product_price_vs_monthly_spending", "days_until_card_due",
                        "avg_price_30d"):
            with self.subTest(feature=feature):
                item = reasons.build_reason_item(feature, -1.0, signed=True)
                self.assertEqual(item.reason_text, reasons.REASON_TEXT[item.reason_code])

    def test_중립_구간은_경계_안쪽이다(self) -> None:
        band = reasons.SIGNED_NEUTRAL_BAND
        inside = reasons.build_reason_item("emergency_fund_balance", band * 0.5, signed=True)
        outside = reasons.build_reason_item("emergency_fund_balance", band * 2, signed=True)

        self.assertNotEqual(inside.reason_text, outside.reason_text)

    def test_방향이_없는_항목은_signed여도_문구가_같다(self) -> None:
        item = reasons.build_reason_item("current_price", 0.7, signed=True)

        self.assertEqual(item.reason_text, reasons.REASON_TEXT[item.reason_code])


class LegacyUnsignedTest(unittest.TestCase):
    def test_signed_기본값은_거짓이고_문구가_바뀌지_않는다(self) -> None:
        for feature in DIRECTIONAL_FEATURES:
            with self.subTest(feature=feature):
                item = reasons.build_reason_item(feature, 1.0)

                self.assertEqual(item.reason_text, reasons.REASON_TEXT[item.reason_code])


class ReasoningEngineSignedTest(unittest.TestCase):
    def test_signed_분석은_부호에_맞는_문구를_낸다(self) -> None:
        engine = ReasoningEngine()
        out = engine.analyze(
            {"emergency_fund_balance": 1.5, "days_until_card_due": -2.0}, top_k=2, signed=True
        )
        by_feature = {r["feature"]: r for r in out}

        self.assertEqual(by_feature["emergency_fund_balance"]["impact_direction"], "positive")
        self.assertIn("충분", by_feature["emergency_fund_balance"]["reason_text"])
        self.assertEqual(by_feature["days_until_card_due"]["impact_direction"], "negative")
        self.assertIn("부담", by_feature["days_until_card_due"]["reason_text"])

    def test_signed_기본값은_예전과_같은_문구다(self) -> None:
        engine = ReasoningEngine()
        out = engine.analyze({"emergency_fund_balance": 1.5}, top_k=1)

        self.assertEqual(
            out[0]["reason_text"], reasons.REASON_TEXT["EMERGENCY_FUND_TOO_LOW"]
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
