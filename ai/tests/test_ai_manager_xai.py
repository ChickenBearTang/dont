from __future__ import annotations

from datetime import datetime, timezone
import importlib
import unittest

from ai import AIPipelineManager
from ai.models import CrawlResult, HotDeal


ExplainabilityAnalyzer = importlib.import_module("ai.xai.analyzer").ExplainabilityAnalyzer


class _FakeCrawler:
    def crawl(self) -> CrawlResult:
        return CrawlResult(
            source="test-source",
            fetched_at=datetime.now(timezone.utc),
            items=[HotDeal(title="Deal", url="https://example.com/deal", price="1000")],
        )


class AIPipelineManagerXAITest(unittest.TestCase):
    def test_run_returns_xai_envelope_with_real_analyzer(self) -> None:
        analyzer = ExplainabilityAnalyzer()
        manager = AIPipelineManager(
            crawler=_FakeCrawler(),
            analyzer=lambda result: analyzer.analyze_crawl_result(result, top_k=2),
        )

        run_result = manager.run()

        self.assertIsInstance(run_result, dict)
        self.assertIn("schema_version", run_result)
        self.assertIn("crawl", run_result)

    def test_run_soft_fails_when_analyzer_raises(self) -> None:
        def bad_analyzer(_: CrawlResult) -> dict[str, object]:
            raise RuntimeError("boom")

        manager = AIPipelineManager(crawler=_FakeCrawler(), analyzer=bad_analyzer)

        run_result = manager.run()

        self.assertIsInstance(run_result, dict)
        self.assertEqual(run_result["schema_version"], "1.0")
        self.assertEqual(run_result["crawl"], {"source": "test-source", "items": []})
        self.assertEqual(
            run_result["errors"],
            [{"code": "ANALYZER_FAILED", "message": "분석기 실행에 실패했습니다"}],
        )


if __name__ == "__main__":
    unittest.main()
