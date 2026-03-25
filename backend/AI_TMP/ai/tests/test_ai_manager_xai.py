from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ai.manager import AIPipelineManager
from ai.models import CrawlResult, HotDeal


class _FakeCrawler:
    def crawl(self) -> CrawlResult:
        return CrawlResult(
            source="test-source",
            fetched_at=datetime.now(timezone.utc),
            items=[HotDeal(title="Deal", url="https://example.com/deal", price="1000")],
        )


class AIPipelineManagerXAITest(unittest.TestCase):
    def test_run_returns_xai_fallback_envelope_when_soft_fail_enabled(self) -> None:
        def _broken_analyzer(_: CrawlResult) -> dict[str, object]:
            raise ValueError("xai failed")

        manager = AIPipelineManager(
            crawler=_FakeCrawler(),
            analyzer=_broken_analyzer,
            analyzer_soft_fail=True,
        )

        payload = manager.run()

        self.assertIsInstance(payload, dict)
        self.assertEqual(
            payload.get("schema_version"), "financial-purchase-copilot-xai-v1"
        )
        self.assertEqual(payload.get("analyzer_id"), "xai-manager-fallback")
        crawl = payload.get("crawl")
        self.assertIsInstance(crawl, dict)
        if not isinstance(crawl, dict):
            self.fail("crawl must be a dict")
        self.assertEqual(crawl.get("source"), "test-source")
        items = crawl.get("items")
        self.assertIsInstance(items, list)
        if not isinstance(items, list) or len(items) == 0:
            self.fail("items must be a non-empty list")
        first_item = items[0]
        self.assertEqual(first_item.get("item_id"), "https://example.com/deal")
        self.assertEqual(first_item.get("decision"), "REVIEW")

    def test_run_returns_analyzer_payload_when_successful(self) -> None:
        expected = {"ok": True, "shape": "xai"}

        manager = AIPipelineManager(
            crawler=_FakeCrawler(),
            analyzer=lambda _: expected,
            analyzer_soft_fail=True,
        )

        payload = manager.run()
        self.assertEqual(payload, expected)


if __name__ == "__main__":
    unittest.main()
