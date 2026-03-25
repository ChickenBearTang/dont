from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer


class XaiRuntimeEnginesTest(unittest.TestCase):
    def test_payload_includes_runtime_engine_metadata(self) -> None:
        analyzer = ExplainabilityAnalyzer()
        payload = analyzer.analyze_crawl_result(
            CrawlResult(
                source="quasarzone",
                fetched_at=datetime.now(timezone.utc),
                items=[
                    HotDeal(
                        title="테스트 상품",
                        url="https://example.com/item",
                        price="129000",
                    )
                ],
            ),
            top_k=3,
        )

        self.assertIn("runtime_engines", payload)
        runtime_engines = payload["runtime_engines"]
        self.assertIn("shap", runtime_engines)
        self.assertIn("dice", runtime_engines)
        self.assertIn("enabled", runtime_engines["shap"])
        self.assertIn("backend", runtime_engines["shap"])
        self.assertIn("enabled", runtime_engines["dice"])
        self.assertIn("backend", runtime_engines["dice"])


if __name__ == "__main__":
    unittest.main()
