from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import sqlite3

from ai.models import CrawlResult
from ai.models import HotDeal

_POST_ID_PATTERN = re.compile(r"/views/(\d+)")
_FOREIGN_CURRENCY_PATTERN = re.compile(r"(?:USD|JPY|CNY|US\$|¥|￥|円|엔|위안|달러|\$)", re.IGNORECASE)
_KRW_TOKEN_PATTERN = re.compile(r"(?:₩|원|KRW)", re.IGNORECASE)
_ALPHA_PATTERN = re.compile(r"[A-Za-z]")
_USD_PATTERN = re.compile(r"(?:\bUSD\b|US\$|달러|\$)", re.IGNORECASE)
_JPY_PATTERN = re.compile(r"(?:\bJPY\b|YEN|円|엔|¥|￥)", re.IGNORECASE)
_CNY_PATTERN = re.compile(r"(?:\bCNY\b|RMB|元|위안)", re.IGNORECASE)
_NUMERIC_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass(frozen=True)
class SaveStats:
    inserted: int
    updated: int


class SqliteCrawlStore:
    _USD_TO_KRW = 1500.0
    _JPY_TO_KRW = 9.5
    _CNY_TO_KRW = 215.0

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialize()

    @staticmethod
    def _extract_post_id(url: str) -> str | None:
        match = _POST_ID_PATTERN.search(url)
        if match is None:
            return None
        return match.group(1)

    @staticmethod
    def _normalize_krw_price(price: str | None) -> str | None:
        if price is None:
            return None
        normalized = price.strip()
        if normalized == "":
            return None
        if _FOREIGN_CURRENCY_PATTERN.search(normalized):
            converted = SqliteCrawlStore._convert_foreign_price_to_krw(normalized)
            return None if converted is None else str(converted)
        cleaned = _KRW_TOKEN_PATTERN.sub("", normalized)
        if _ALPHA_PATTERN.search(cleaned):
            return None
        digits = re.sub(r"[^0-9]", "", cleaned)
        if digits == "":
            return None
        return digits

    @staticmethod
    def _convert_foreign_price_to_krw(price_text: str) -> int | None:
        amount = SqliteCrawlStore._extract_amount(price_text)
        if amount is None:
            return None

        if _CNY_PATTERN.search(price_text):
            return int(round(amount * SqliteCrawlStore._CNY_TO_KRW))
        if _JPY_PATTERN.search(price_text):
            return int(round(amount * SqliteCrawlStore._JPY_TO_KRW))
        if _USD_PATTERN.search(price_text):
            return int(round(amount * SqliteCrawlStore._USD_TO_KRW))
        return None

    @staticmethod
    def _extract_amount(price_text: str) -> float | None:
        match = _NUMERIC_PATTERN.search(price_text.replace(",", ""))
        if match is None:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_items (
                    source TEXT NOT NULL,
                    post_id TEXT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price TEXT,
                    posted_at TEXT,
                    fetched_at TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    PRIMARY KEY (url)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_items_source_post_id
                ON crawl_items (source, post_id)
                """
            )

    def is_seen(self, deal: HotDeal) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM crawl_items WHERE url = ? LIMIT 1",
                (deal.url,),
            ).fetchone()
        return row is not None

    def save_result(self, result: CrawlResult) -> SaveStats:
        inserted = 0
        updated = 0
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            for deal in result.items:
                post_id = self._extract_post_id(deal.url)
                normalized_price = self._normalize_krw_price(deal.price)
                existing = connection.execute(
                    "SELECT 1 FROM crawl_items WHERE url = ? LIMIT 1",
                    (deal.url,),
                ).fetchone()

                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO crawl_items (
                            source,
                            post_id,
                            url,
                            title,
                            price,
                            posted_at,
                            fetched_at,
                            first_seen_at,
                            last_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result.source,
                            post_id,
                            deal.url,
                            deal.title,
                            normalized_price,
                            deal.posted_at,
                            result.fetched_at.isoformat(),
                            now,
                            now,
                        ),
                    )
                    inserted += 1
                    continue

                connection.execute(
                    """
                    UPDATE crawl_items
                    SET
                        source = ?,
                        post_id = ?,
                        title = ?,
                        price = ?,
                        posted_at = ?,
                        fetched_at = ?,
                        last_seen_at = ?
                    WHERE url = ?
                    """,
                    (
                        result.source,
                        post_id,
                        deal.title,
                        normalized_price,
                        deal.posted_at,
                        result.fetched_at.isoformat(),
                        now,
                        deal.url,
                    ),
                )
                updated += 1

        return SaveStats(inserted=inserted, updated=updated)
