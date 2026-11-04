from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from ..crawler.price import parse_price_krw
from ..models import HotDeal


class FeatureExtractor:
    def normalize_price_to_int(self, price: str | None) -> int | None:
        """가격 문자열 -> 원화 정수. 단일 파서(ai.crawler.price)에 위임한다.

        예전에는 문자열 속 모든 숫자를 이어 붙여 "5% 할인 21,200원" 이 521200 이 됐다.
        읽을 수 없으면 None 이고, 이유는 parse_price_krw 의 status 로 알 수 있다.
        """
        return parse_price_krw(price).amount

    def extract_features(self, deal: HotDeal) -> dict[str, Any]:
        title = deal.title if isinstance(deal.title, str) else ""
        price_int = self.normalize_price_to_int(deal.price)
        parsed_url = urlparse(deal.url if isinstance(deal.url, str) else "")
        url_domain = parsed_url.netloc

        has_title = title.strip() != ""
        has_price = price_int is not None

        missing_fields: list[str] = []
        if not has_title:
            missing_fields.append("title")
        if not has_price:
            missing_fields.append("price")
        if url_domain == "":
            missing_fields.append("url_domain")

        return {
            "title_len": len(title),
            "has_title": has_title,
            "has_price": has_price,
            "price_int": price_int,
            "url_domain": url_domain,
            "missing_fields": missing_fields,
        }
