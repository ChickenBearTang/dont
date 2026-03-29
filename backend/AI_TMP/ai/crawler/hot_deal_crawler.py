from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from ai.models import CrawlResult
from ai.models import HotDeal
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

    def _build_url(self, query_params: dict[str, int | str]) -> str:
        parsed = urlparse(self.source_url)
        existing_query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        merged_query = {**existing_query, **query_params}
        return urlunparse(parsed._replace(query=urlencode(merged_query)))

    def build_page_url(self, page: int = 1) -> str:
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        query_params = {
            "page": page,
            "sort": "num,reply",
            "direction": "DESC",
        }
        return self._build_url(query_params)

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
        return self._build_url(query_params)

    def search(self, keyword: str, page: int = 1) -> CrawlResult:
        search_url = self.build_search_url(keyword=keyword, page=page)
        html = self.fetch(search_url)
        items = parse_hot_deals(html)
        return CrawlResult(
            source=search_url,
            fetched_at=datetime.now(timezone.utc),
            items=items,
        )

    def crawl_until_overlap(
        self,
        keyword: str | None = None,
        start_page: int = 1,
        max_pages: int = 1000,
        overlap_threshold: int = 30,
        is_seen: Callable[[HotDeal], bool] | None = None,
    ) -> CrawlResult:
        normalized_keyword: str | None = None
        if keyword is not None:
            normalized_keyword = keyword.strip()
            if not normalized_keyword:
                raise ValueError("keyword must not be empty when provided")

        if start_page < 1:
            raise ValueError("start_page must be greater than or equal to 1")
        if max_pages < 1:
            raise ValueError("max_pages must be greater than or equal to 1")
        if overlap_threshold < 1:
            raise ValueError("overlap_threshold must be greater than or equal to 1")

        items: list[HotDeal] = []
        seen_urls: set[str] = set()
        consecutive_overlap = 0

        for page in range(start_page, start_page + max_pages):
            page_url = (
                self.build_search_url(normalized_keyword, page)
                if normalized_keyword is not None
                else self.build_page_url(page)
            )
            html = self.fetch(page_url)
            page_items = parse_hot_deals(html)
            if not page_items:
                break

            page_new_count = 0
            for deal in page_items:
                already_seen = deal.url in seen_urls
                already_stored = False
                if not already_seen and is_seen is not None:
                    already_stored = is_seen(deal)

                if already_seen or already_stored:
                    seen_urls.add(deal.url)
                    consecutive_overlap += 1
                    if consecutive_overlap >= overlap_threshold:
                        source = (
                            self.build_search_url(normalized_keyword, start_page)
                            if normalized_keyword is not None
                            else self.build_page_url(start_page)
                        )
                        return CrawlResult(
                            source=source,
                            fetched_at=datetime.now(timezone.utc),
                            items=items,
                        )
                    continue

                consecutive_overlap = 0
                seen_urls.add(deal.url)
                items.append(deal)
                page_new_count += 1

            if page_new_count == 0:
                break

        source = (
            self.build_search_url(normalized_keyword, start_page)
            if normalized_keyword is not None
            else self.build_page_url(start_page)
        )
        return CrawlResult(
            source=source,
            fetched_at=datetime.now(timezone.utc),
            items=items,
        )
