from __future__ import annotations

from html import unescape
import re
from urllib.parse import urljoin

from ai.models import HotDeal

BASE_DEAL_URL = "https://quasarzone.com"

_ENTRY_SPLIT_PATTERN = re.compile(
    r"<div[^>]*class=(['\"]).*?market-info-list.*?\1[^>]*>",
    re.IGNORECASE,
)
_SUBJECT_LINK_PATTERN = re.compile(
    r"<a(?=[^>]*class=(['\"]).*?subject-link.*?\1)(?=[^>]*href=(['\"])(.*?)\2)[^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
_PRICE_PATTERN = re.compile(
    r"<span[^>]*class=(['\"]).*?text-orange.*?\1[^>]*>(.*?)</span>",
    re.IGNORECASE | re.DOTALL,
)
_DATE_TAG_PATTERN = re.compile(
    r"<(?:span|p|div|li)[^>]*class=(['\"]).*?(?:date|time|regdate|created).*?\1[^>]*>(.*?)</(?:span|p|div|li)>",
    re.IGNORECASE | re.DOTALL,
)
_DATE_TEXT_PATTERN = re.compile(r"\b(\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}[./-]\d{1,2})\b")
_TAG_PATTERN = re.compile(r"<[^>]+>")


def _clean_text(value: str) -> str:
    no_tags = _TAG_PATTERN.sub(" ", value)
    return " ".join(unescape(no_tags).split())


def parse_hot_deals(html: str) -> list[HotDeal]:
    items: list[HotDeal] = []
    seen_urls: set[str] = set()
    blocks = _ENTRY_SPLIT_PATTERN.split(html)

    for block in blocks:
        subject_match = _SUBJECT_LINK_PATTERN.search(block)
        if subject_match is None:
            continue

        href = unescape(subject_match.group(3))
        title = _clean_text(subject_match.group(4))
        if not title:
            continue

        price_match = _PRICE_PATTERN.search(block)
        price = _clean_text(price_match.group(2)) if price_match else None
        posted_at = _extract_posted_at(block)
        absolute_url = urljoin(BASE_DEAL_URL, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        items.append(
            HotDeal(
                title=title,
                url=absolute_url,
                price=price,
                posted_at=posted_at,
            )
        )

    return items


def _extract_posted_at(block: str) -> str | None:
    tag_match = _DATE_TAG_PATTERN.search(block)
    if tag_match is not None:
        cleaned = _clean_text(tag_match.group(2))
        text_match = _DATE_TEXT_PATTERN.search(cleaned)
        if text_match is not None:
            return text_match.group(1)
        return cleaned if cleaned else None

    fallback = _clean_text(block)
    text_match = _DATE_TEXT_PATTERN.search(fallback)
    if text_match is None:
        return None
    return text_match.group(1)
