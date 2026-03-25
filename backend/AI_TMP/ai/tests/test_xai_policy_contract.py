from __future__ import annotations

from datetime import datetime, timezone
import importlib
import unittest

from ..models import CrawlResult, HotDeal


ExplainabilityAnalyzer = importlib.import_module(
    "ai.xai.analyzer"
).ExplainabilityAnalyzer


class XAIPolicyContractTest(unittest.TestCase):
    def test_reason_count_is_capped_and_coupon_reason_not_invented(self) -> None:
        analyzer = ExplainabilityAnalyzer()
        crawl = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="Test Deal",
                    url="https://example.com/test",
                    price="150,000",
                )
            ],
        )

        payload = analyzer.analyze_crawl_result(crawl, top_k=10)
        item = payload["crawl"]["items"][0]

        self.assertLessEqual(len(item["reasons"]), 4)
        self.assertLessEqual(len(item["reason_codes"]), 4)
        self.assertLessEqual(len(item["reason_texts"]), 4)
        self.assertNotIn("PRICE_COUPON_DISCOUNT_APPLIED", item["reason_codes"])

    def test_counterfactual_variables_follow_phase1_policy(self) -> None:
        analyzer = ExplainabilityAnalyzer()
        crawl = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="Test Deal",
                    url="https://example.com/test-2",
                    price="250,000",
                )
            ],
        )

        payload = analyzer.analyze_crawl_result(crawl, top_k=3)
        item = payload["crawl"]["items"][0]
        allowed_variables = {
            "current_effective_price",
            "available_budget",
            "emergency_buffer",
        }
        for condition in item["counterfactual_conditions"]:
            self.assertIn(condition.get("variable"), allowed_variables)

    def test_supporting_evidence_references_only_reasoned_features(self) -> None:
        analyzer = ExplainabilityAnalyzer()
        crawl = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="Another Deal",
                    url="https://example.com/test-3",
                    price="90,000",
                )
            ],
        )

        payload = analyzer.analyze_crawl_result(crawl, top_k=3)
        item = payload["crawl"]["items"][0]
        reason_features = {reason.get("feature") for reason in item["reasons"]}

        for evidence in item["supporting_evidence"]:
            self.assertIn(evidence.get("feature"), reason_features)


if __name__ == "__main__":
    unittest.main()
