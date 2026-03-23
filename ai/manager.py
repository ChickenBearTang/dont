from __future__ import annotations

from typing import Any, Callable

from ai.crawler.base import Crawler
from ai.models import CrawlResult
from ai.xai.types import XAIContracts


class AIPipelineManager:
    def __init__(
        self,
        crawler: Crawler,
        analyzer: Callable[[CrawlResult], Any] | None = None,
    ) -> None:
        self.crawler = crawler
        self.analyzer = analyzer

    def run(self) -> Any:
        crawl_result = self.crawler.crawl()
        if self.analyzer is None:
            return crawl_result
        try:
            return self.analyzer(crawl_result)
        except Exception:
            return {
                "errors": [
                    {"code": "ANALYZER_FAILED", "message": "분석기 실행에 실패했습니다"}
                ],
                "crawl": {"source": crawl_result.source, "items": []},
                "schema_version": XAIContracts.SCHEMA_VERSION,
                "spec_version": XAIContracts.SPEC_VERSION,
            }
