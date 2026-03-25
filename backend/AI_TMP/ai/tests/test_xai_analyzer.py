from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer


class ExplainabilityAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = ExplainabilityAnalyzer()

    def test_analyze_crawl_result_happy_path_envelope_and_top_k(self) -> None:
        crawl = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="B Deal",
                    url="https://example.com/b",
                    price="2,000",
                ),
                HotDeal(
                    title="A Deal",
                    url="https://example.com/a",
                    price="1,000",
                ),
            ],
        )

        payload = self.analyzer.analyze_crawl_result(crawl, top_k=2)

        self.assertIn("schema_version", payload)
        self.assertIn("analyzer_id", payload)
        self.assertIn("generated_at", payload)
        self.assertIn("model_version", payload)
        self.assertIn("crawl", payload)
        self.assertIn("errors", payload)
        self.assertIn("statistics", payload)
        self.assertIn("finance_profile", payload)
        self.assertIn("rule_version", payload)
        self.assertIn("audit_logs", payload)
        self.assertEqual(payload["analyzer_id"], "xai-explainability")
        self.assertEqual(
            payload["model_version"], "financial-purchase-copilot-xai-model-v1"
        )
        self.assertEqual(payload["crawl"]["source"], "quasarzone")
        self.assertEqual(payload["errors"], [])
        self.assertGreaterEqual(len(payload["audit_logs"]), 1)
        self.assertIn("model_input_vector_hash", payload["audit_logs"][0])
        self.assertIn("data_snapshot_id", payload["audit_logs"][0])

        items = payload["crawl"]["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["item_id"], "https://example.com/a")
        self.assertEqual(items[1]["item_id"], "https://example.com/b")
        self.assertLessEqual(len(items[0]["reasons"]), 2)
        self.assertLessEqual(len(items[1]["reasons"]), 2)
        self.assertIn(
            items[0]["decision"], {"BUY_NOW", "WAIT", "NOT_RECOMMENDED", "REVIEW"}
        )
        self.assertLessEqual(len(items[0]["reason_codes"]), 4)
        self.assertLessEqual(len(items[0]["reason_texts"]), 4)
        self.assertIn("decision_confidence", items[0])
        self.assertIn("supporting_evidence", items[0])
        self.assertIn("counterfactual_conditions", items[0])
        self.assertIn("user_options", items[0])
        self.assertIn("data_snapshot_id", items[0])
        self.assertIn("rule_version", items[0])
        self.assertIsInstance(items[0]["counterfactuals"], list)
        self.assertIsInstance(items[0]["polished_summary"], str)
        self.assertEqual(items[0]["errors"], [])
        self.assertEqual(items[1]["errors"], [])

    def test_analyze_crawl_result_malformed_item_soft_fails(self) -> None:
        crawl = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="Valid Deal",
                    url="https://example.com/valid",
                    price="990",
                ),
                HotDeal(
                    title="",
                    url="https://example.com/malformed",
                    price=None,
                ),
            ],
        )

        payload = self.analyzer.analyze_crawl_result(crawl, top_k=3)

        items = payload["crawl"]["items"]
        self.assertEqual(len(items), 2)

        valid_item = next(
            item for item in items if item["item_id"] == "https://example.com/valid"
        )
        malformed_item = next(
            item for item in items if item["item_id"] == "https://example.com/malformed"
        )

        self.assertGreater(len(valid_item["reasons"]), 0)
        self.assertEqual(valid_item["errors"], [])
        self.assertIsInstance(valid_item["counterfactuals"], list)

        self.assertEqual(malformed_item["reasons"], [])
        self.assertEqual(len(malformed_item["errors"]), 1)
        self.assertEqual(
            malformed_item["errors"][0]["code"], "XAI_ITEM_VALIDATION_FAILED"
        )
        self.assertEqual(
            malformed_item["errors"][0]["item_id"], "https://example.com/malformed"
        )

        success_count = sum(1 for item in items if len(item["errors"]) == 0)
        error_count = sum(1 for item in items if len(item["errors"]) > 0)
        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 1)
        self.assertEqual(len(payload["errors"]), 1)


if __name__ == "__main__":
    unittest.main()
