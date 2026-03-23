from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ai import AIPipelineManager
from ai.models import CrawlResult, HotDeal


class _FakeCrawler:
    def crawl(self) -> CrawlResult:
        return CrawlResult(
            source="test-source",
            fetched_at=datetime.now(timezone.utc),
            items=[HotDeal(title="Deal", url="https://example.com/deal", price="1000")],
        )


class AIPipelineManagerTest(unittest.TestCase):
    def test_run_returns_crawl_result_without_analyzer(self) -> None:
        manager = AIPipelineManager(crawler=_FakeCrawler())

        result = manager.run()

        self.assertEqual(result.source, "test-source")
        self.assertEqual(len(result.items), 1)

    def test_run_uses_analyzer_when_provided(self) -> None:
        manager = AIPipelineManager(
            crawler=_FakeCrawler(),
            analyzer=lambda result: {"count": len(result.items)},
        )

        result = manager.run()

        self.assertEqual(result, {"count": 1})


if __name__ == "__main__":
    unittest.main()
