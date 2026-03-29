from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from ..models import HotDeal


class FeatureExtractor:
    _PRICE_TOKEN_PATTERN = re.compile(r"[0-9,]+")

    def normalize_price_to_int(self, price: str | None) -> int | None:
        if not isinstance(price, str):
            return None

        compact = "".join(self._PRICE_TOKEN_PATTERN.findall(price))
        if compact == "":
            return None

        digits_only = compact.replace(",", "")
        if digits_only == "":
            return None

        try:
            return int(digits_only)
        except ValueError:
            return None

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
