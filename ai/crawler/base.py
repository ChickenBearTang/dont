from __future__ import annotations

from typing import Protocol

from ai.models import CrawlResult


class Crawler(Protocol):
    def crawl(self) -> CrawlResult:
        ...
