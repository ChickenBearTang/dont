from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from ai.models import CrawlResult
from ai.models import HotDeal
from ai.data.hot_deal_parser import parse_hot_deals

from .adapters import SiteAdapter
from .quality import QualityReport, assess_batch
from .registry import AdapterRegistry, default_registry
from .schema import NormalizedDeal
from .validation import Severity, validate_deal

DEFAULT_SOURCE_URL = "https://quasarzone.com/bbs/qb_saleinfo"


def default_fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "wt-ai-crawler/1.0"})
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


@dataclass(frozen=True)
class NormalizedCrawl:
    source: str
    site_id: str
    fetched_at: datetime
    deals: list[NormalizedDeal]  # 오류가 없는 글 (경고는 issues 에 코드로 남아 있다)
    quality: QualityReport
    quarantined: list[NormalizedDeal] = field(default_factory=list)  # 오류 수준 이슈가 있어 쓰지 않는 글


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

    def crawl_normalized(
        self,
        adapter: SiteAdapter | None = None,
        registry: AdapterRegistry | None = None,
        resolver: Any = None,
    ) -> NormalizedCrawl:
        """사이트 어댑터로 읽고 공통 스키마로 정규화한 뒤 오염을 검증하고 수집 품질을 점검한다.

        adapter 를 주지 않으면 source_url 의 도메인으로 레지스트리에서 찾는다. 등록되지
        않은 사이트는 UnknownSiteError 다 (다른 사이트의 파서로 읽지 않는다).
        오류 수준 이슈가 있는 글은 quarantined 로 분리한다. resolver(identity.ProductResolver)를
        주면 글마다 제조사·모델 단위 식별 결과를 붙인다.
        quality.ok 가 False 면 사이트 마크업이 바뀌었을 가능성이 있으니 저장 전에 확인한다.
        """
        resolved = adapter or (registry or default_registry()).adapter_for_url(self.source_url)
        html = self.fetch(self.source_url)
        listing = resolved.parse_listing(html)
        fetched_at = datetime.now(timezone.utc)

        clean: list[NormalizedDeal] = []
        quarantined: list[NormalizedDeal] = []
        for deal in listing:
            normalized = resolved.normalize(deal, fetched_at=fetched_at)
            found = validate_deal(normalized, now=fetched_at)
            normalized = replace(
                normalized,
                issues=tuple(i.code for i in found),
                identity=resolver.resolve(normalized.title, url=normalized.url) if resolver is not None else None,
            )
            (quarantined if any(i.severity == Severity.ERROR for i in found) else clean).append(normalized)

        return NormalizedCrawl(
            source=self.source_url,
            site_id=resolved.site_id,
            fetched_at=fetched_at,
            deals=clean,
            quality=assess_batch(clean + quarantined, resolved.capabilities),
            quarantined=quarantined,
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
