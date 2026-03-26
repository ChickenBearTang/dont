from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer


class _FakeDiceEngine:
    def suggest(self, **_: object) -> tuple[list[dict[str, object]], dict[str, object]]:
        return [
            {
                "type": "dice",
                "variable": "available_budget",
                "action": "increase",
                "suggested_change": 120000,
                "threshold": 620000,
                "message": "Increase budget to improve decision",
            },
            {
                "type": "dice",
                "variable": "current_effective_price",
                "action": "decrease",
                "suggested_change": 30000,
                "threshold": 159000,
                "message": "Wait for lower price",
            },
        ], {"enabled": True, "backend": "dice_ml"}


class XaiDiceKoreanMessagesTest(unittest.TestCase):
    def test_counterfactual_messages_are_korean_even_when_dice_returns_english(
        self,
    ) -> None:
        analyzer = ExplainabilityAnalyzer(dice_counterfactual_engine=_FakeDiceEngine())
        payload = analyzer.analyze_crawl_result(
            CrawlResult(
                source="quasarzone",
                fetched_at=datetime.now(timezone.utc),
                items=[
                    HotDeal(
                        title="테스트 상품",
                        url="https://example.com/item",
                        price="189000",
                    )
                ],
            ),
            top_k=3,
        )

        item = payload["crawl"]["items"][0]
        messages = [
            str(counterfactual.get("message", ""))
            for counterfactual in item.get("counterfactuals", [])
        ]

        self.assertGreaterEqual(len(messages), 1)
        for message in messages:
            self.assertRegex(message, r"[가-힣]")

    def test_unknown_counterfactual_shape_falls_back_to_korean_message(self) -> None:
        analyzer = ExplainabilityAnalyzer(dice_counterfactual_engine=_FakeDiceEngine())
        normalized = analyzer._normalize_counterfactual_messages(
            [
                {
                    "type": "dice",
                    "variable": "unexpected_metric",
                    "action": "unexpected_action",
                    "message": "Unrecognized English text",
                }
            ]
        )

        self.assertEqual(len(normalized), 1)
        self.assertRegex(str(normalized[0].get("message", "")), r"[가-힣]")

    def test_missing_suggested_change_still_returns_korean_message(self) -> None:
        analyzer = ExplainabilityAnalyzer(dice_counterfactual_engine=_FakeDiceEngine())
        normalized = analyzer._normalize_counterfactual_messages(
            [
                {
                    "type": "dice",
                    "variable": "available_budget",
                    "action": "increase",
                    "suggested_change": None,
                    "message": "Increase available budget",
                }
            ]
        )

        self.assertEqual(len(normalized), 1)
        self.assertRegex(str(normalized[0].get("message", "")), r"[가-힣]")

    def test_emergency_buffer_delta_is_stabilized_by_savebox_and_30d_avg(self) -> None:
        stabilized = ExplainabilityAnalyzer._stabilize_counterfactual_suggestions(
            [
                {
                    "type": "dice",
                    "variable": "emergency_buffer",
                    "action": "increase",
                    "suggested_change": 999999,
                    "threshold": 1234567,
                    "message": "Increase emergency fund",
                }
            ],
            price_value=50_000,
            monthly_spending_30d=600_000,
            savebox_balance=100_000,
            window_stats={"30d": {"avg_price": 40_000}},
        )

        self.assertEqual(len(stabilized), 1)
        self.assertEqual(stabilized[0]["variable"], "emergency_buffer")
        self.assertEqual(stabilized[0]["action"], "increase")
        self.assertEqual(stabilized[0]["suggested_change"], 550_000)
        self.assertEqual(stabilized[0]["threshold"], 650_000.0)
        self.assertEqual(stabilized[0]["stabilized_by"], "savebox_avg30d_rule_v2")

    def test_emergency_suggestion_is_injected_when_missing(self) -> None:
        stabilized = ExplainabilityAnalyzer._stabilize_counterfactual_suggestions(
            [
                {
                    "type": "dice",
                    "variable": "available_budget",
                    "action": "increase",
                    "suggested_change": 215123,
                    "threshold": 800000,
                }
            ],
            price_value=50_000,
            monthly_spending_30d=600_000,
            savebox_balance=100_000,
            window_stats={"30d": {"avg_price": 40_000}},
        )

        self.assertGreaterEqual(len(stabilized), 1)
        self.assertEqual(stabilized[0]["variable"], "emergency_buffer")
        self.assertEqual(stabilized[0]["suggested_change"], 550_000)
        self.assertEqual(stabilized[1]["variable"], "available_budget")
        self.assertEqual(stabilized[1]["suggested_change"], 220_000)


if __name__ == "__main__":
    unittest.main()
