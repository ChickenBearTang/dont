from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from ai.models import CrawlResult
from ai.data.hot_deal_parser import parse_hot_deals

DEFAULT_SOURCE_URL = "https://quasarzone.com/bbs/qb_saleinfo"


def default_fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "wt-ai-crawler/1.0"})
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


class HotDealCrawler:
    def __init__(
        self,
        source_url: str = DEFAULT_SOURCE_URL,
        fetch: Callable[[str], str] = default_fetch,
    ) -> None:
        self.source_url = source_url
        self.fetch = fetch

    def crawl(self) -> CrawlResult:
        html = self.fetch(self.source_url)
        items = parse_hot_deals(html)
        return CrawlResult(
            source=self.source_url,
            fetched_at=datetime.now(timezone.utc),
            items=items,
        )

    def build_search_url(self, keyword: str, page: int = 1) -> str:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            raise ValueError("keyword must not be empty")

        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        query_params = {
            "page": page,
            "kind": "subject",
            "keyword": normalized_keyword,
            "sort": "num,reply",
            "direction": "DESC",
        }
        parsed = urlparse(self.source_url)
        existing_query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        merged_query = {**existing_query, **query_params}
        return urlunparse(parsed._replace(query=urlencode(merged_query)))

    def search(self, keyword: str, page: int = 1) -> CrawlResult:
        search_url = self.build_search_url(keyword=keyword, page=page)
        html = self.fetch(search_url)
        items = parse_hot_deals(html)
        return CrawlResult(
            source=search_url,
            fetched_at=datetime.now(timezone.utc),
            items=items,
        )
