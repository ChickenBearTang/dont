from __future__ import annotations

from ai.data.hot_deal_parser import parse_hot_deals
from ai.models import HotDeal

from ..schema import SiteCapabilities
from .base import BaseSiteAdapter

QUASARZONE_DOMAIN = "quasarzone.com"


class QuasarzoneAdapter(BaseSiteAdapter):
    """퀘이사존 핫딜(qb_saleinfo) 목록.

    파싱은 기존 ai.data.hot_deal_parser 를 그대로 쓴다 (동작 변경 없음).
    목록 화면이 가격과 날짜를 주지만 모든 글에 있는 것은 아니다.
    """

    site_id = "quasarzone"
    capabilities = SiteCapabilities(
        provides_price=True,
        provides_posted_at=True,
        search_supported=True,
        expected_price_rate=0.5,
        expected_posted_at_rate=0.5,
    )

    def parse_listing(self, html: str) -> list[HotDeal]:
        return parse_hot_deals(html)
