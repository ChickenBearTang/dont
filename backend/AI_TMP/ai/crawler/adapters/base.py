"""사이트 어댑터 인터페이스.

새 사이트를 붙이는 방법
    1. SiteAdapter 를 구현한다: site_id, capabilities, parse_listing(html).
       parse_listing 은 그 사이트의 마크업을 HotDeal 목록으로 바꾼다. 가격/날짜는
       사이트가 보여주는 원문 문자열 그대로 둔다 (해석은 BaseSiteAdapter.normalize 가 한다).
    2. 그 사이트의 실제 목록 HTML 을 tests/fixtures/crawler/ 에 저장하고,
       어댑터가 기대한 건수/필드를 뽑는지 테스트한다.
    3. registry.default_registry() 에 도메인과 함께 등록한다.
사이트마다 코드가 갈라지는 곳은 parse_listing 하나뿐이다. 가격/날짜 해석, 정규화, 품질 점검은
모든 사이트가 공유한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ai.models import HotDeal

from ..dates import parse_posted_at
from ..price import PriceStatus, parse_price_krw
from ..schema import FieldStatus, NormalizedDeal, SiteCapabilities


class SiteAdapter(Protocol):
    site_id: str
    capabilities: SiteCapabilities

    def parse_listing(self, html: str) -> list[HotDeal]:
        ...

    def normalize(self, deal: HotDeal, *, fetched_at: datetime) -> NormalizedDeal:
        ...


class BaseSiteAdapter:
    """normalize 를 공통으로 구현한다. 하위 클래스는 site_id/capabilities/parse_listing 만 채운다."""

    site_id: str
    capabilities: SiteCapabilities

    def parse_listing(self, html: str) -> list[HotDeal]:  # pragma: no cover - 하위 클래스가 구현
        raise NotImplementedError

    def normalize(self, deal: HotDeal, *, fetched_at: datetime) -> NormalizedDeal:
        caps = self.capabilities

        if caps.provides_price:
            price = parse_price_krw(deal.price)
            if price.status == PriceStatus.MISSING:
                price_field = FieldStatus.MISSING
            elif price.ok:
                price_field = FieldStatus.PARSED
            else:
                price_field = FieldStatus.UNPARSEABLE
            price_amount, price_status, price_raw = price.amount, price.status, deal.price
        else:
            price_amount, price_status, price_raw = None, PriceStatus.MISSING, deal.price
            price_field = FieldStatus.NOT_PROVIDED

        if caps.provides_posted_at:
            posted = parse_posted_at(deal.posted_at, now=fetched_at)
            posted_value, posted_field, posted_raw = posted.value, posted.field, deal.posted_at
        else:
            posted_value, posted_field, posted_raw = None, FieldStatus.NOT_PROVIDED, deal.posted_at

        return NormalizedDeal(
            site_id=self.site_id,
            title=deal.title,
            url=deal.url,
            price_krw=price_amount,
            price_status=price_status,
            price_field=price_field,
            price_raw=price_raw,
            posted_at=posted_value,
            posted_at_field=posted_field,
            posted_at_raw=posted_raw,
            fetched_at=fetched_at,
        )
