from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

from ai.models import HotDeal

BASE_DEAL_URL = "https://arca.live"
_WHITESPACE_PATTERN = re.compile(r"\s+")
_TRAILING_REPLY_PATTERN = re.compile(r"\s*\[\d+\]\s*$")


def _clean_text(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", unescape(value)).strip()


class _ArcaLiveHotDealHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[HotDeal] = []
        self._seen_urls: set[str] = set()

        self._in_row = False
        self._row_depth = 0
        self._current_store: str | None = None
        self._current_title_href: str | None = None
        self._current_title_parts: list[str] = []
        self._current_price_parts: list[str] = []
        self._current_posted_at: str | None = None

        self._capture_store = False
        self._capture_title = False
        self._capture_price = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = _class_set(attr_map.get("class"))

        if tag == "div" and {"vrow", "hybrid"}.issubset(classes):
            self._start_row()
            return

        if not self._in_row:
            return

        if tag == "div":
            self._row_depth += 1

        if tag == "span" and "deal-store" in classes:
            self._capture_store = True
            return

        if tag == "a" and {"title", "hybrid-title"}.issubset(classes):
            href = attr_map.get("href")
            if href:
                self._current_title_href = href
                self._capture_title = True
            return

        if tag == "span" and "deal-price" in classes:
            self._capture_price = True
            return

        if tag == "time":
            datetime_value = attr_map.get("datetime")
            if datetime_value:
                self._current_posted_at = _clean_text(datetime_value)

    def handle_endtag(self, tag: str) -> None:
        if not self._in_row:
            return

        if tag == "span":
            self._capture_store = False
            self._capture_price = False
            return

        if tag == "a":
            self._capture_title = False
            return

        if tag == "div":
            self._row_depth -= 1
            if self._row_depth == 0:
                self._finish_row()

    def handle_data(self, data: str) -> None:
        if not self._in_row:
            return

        if self._capture_store:
            self._current_title_parts.append("")
            self._current_store = _append_text(self._current_store, data)
            return

        if self._capture_title:
            self._current_title_parts.append(data)
            return

        if self._capture_price:
            self._current_price_parts.append(data)

    def _start_row(self) -> None:
        self._in_row = True
        self._row_depth = 1
        self._current_store = None
        self._current_title_href = None
        self._current_title_parts = []
        self._current_price_parts = []
        self._current_posted_at = None
        self._capture_store = False
        self._capture_title = False
        self._capture_price = False

    def _finish_row(self) -> None:
        raw_title = _clean_text("".join(self._current_title_parts))
        title = _TRAILING_REPLY_PATTERN.sub("", raw_title).strip()
        price = _clean_text("".join(self._current_price_parts)) or None
        href = self._current_title_href
        store = _clean_text(self._current_store or "")

        if href and title:
            if store:
                title = f"[{store}] {title}"
            absolute_url = urljoin(BASE_DEAL_URL, href)
            if absolute_url not in self._seen_urls:
                self._seen_urls.add(absolute_url)
                self.items.append(
                    HotDeal(
                        title=title,
                        url=absolute_url,
                        price=price,
                        posted_at=self._current_posted_at,
                    )
                )

        self._in_row = False
        self._row_depth = 0


def _class_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {token for token in value.split() if token}


def _append_text(current: str | None, chunk: str) -> str:
    cleaned_chunk = _clean_text(chunk)
    if not cleaned_chunk:
        return current or ""
    if not current:
        return cleaned_chunk
    return f"{current} {cleaned_chunk}"


def parse_arcalive_hot_deals(html: str) -> list[HotDeal]:
    parser = _ArcaLiveHotDealHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.items
