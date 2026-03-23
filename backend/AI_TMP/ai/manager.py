from __future__ import annotations

from typing import Any, Callable

from ai.crawler.base import Crawler
from ai.models import CrawlResult


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
        return self.analyzer(crawl_result)
