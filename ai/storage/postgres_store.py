from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import importlib
import re
from typing import Any, Callable

from ai.models import CrawlResult
from ai.models import HotDeal
from ai.storage.base import SaveStats

_POST_ID_PATTERN = re.compile(r"/views/(\d+)")


@dataclass(frozen=True)
class PostgresSampleResult:
    total_count: int
    sample_items: list[dict[str, str | None]]


class PostgresCrawlStore:
    def __init__(
        self,
        dsn: str,
        connector: Callable[[str], Any] | None = None,
    ) -> None:
        self.dsn = dsn
        self._connector = connector or self._default_connector
        self._initialize()

    @staticmethod
    def _default_connector(dsn: str) -> Any:
        try:
            psycopg_module = importlib.import_module("psycopg")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "psycopg package is required for PostgreSQL storage"
            ) from exc
        connect = getattr(psycopg_module, "connect", None)
        if connect is None:
            raise RuntimeError("psycopg.connect is unavailable")
        return connect(dsn)

    def _connect(self) -> Any:
        return self._connector(self.dsn)

    @staticmethod
    def _extract_post_id(url: str) -> str | None:
        match = _POST_ID_PATTERN.search(url)
        if match is None:
            return None
        return match.group(1)

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def _initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS crawl_items (
                        source TEXT NOT NULL,
                        post_id TEXT,
                        url TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        price TEXT,
                        fetched_at TIMESTAMPTZ NOT NULL,
                        first_seen_at TIMESTAMPTZ NOT NULL,
                        last_seen_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_crawl_items_source_post_id
                    ON crawl_items (source, post_id)
                    """
                )

    def is_seen(self, deal: HotDeal) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM crawl_items WHERE url = %s LIMIT 1",
                    (deal.url,),
                )
                row = cursor.fetchone()
        return row is not None

    def save_result(self, result: CrawlResult) -> SaveStats:
        inserted = 0
        updated = 0
        now = self._now_utc()

        with self._connect() as connection:
            with connection.cursor() as cursor:
                for deal in result.items:
                    post_id = self._extract_post_id(deal.url)
                    cursor.execute(
                        "SELECT 1 FROM crawl_items WHERE url = %s LIMIT 1",
                        (deal.url,),
                    )
                    existing = cursor.fetchone()

                    if existing is None:
                        cursor.execute(
                            """
                            INSERT INTO crawl_items (
                                source,
                                post_id,
                                url,
                                title,
                                price,
                                fetched_at,
                                first_seen_at,
                                last_seen_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                result.source,
                                post_id,
                                deal.url,
                                deal.title,
                                deal.price,
                                result.fetched_at,
                                now,
                                now,
                            ),
                        )
                        inserted += 1
                        continue

                    cursor.execute(
                        """
                        UPDATE crawl_items
                        SET
                            source = %s,
                            post_id = %s,
                            title = %s,
                            price = %s,
                            fetched_at = %s,
                            last_seen_at = %s
                        WHERE url = %s
                        """,
                        (
                            result.source,
                            post_id,
                            deal.title,
                            deal.price,
                            result.fetched_at,
                            now,
                            deal.url,
                        ),
                    )
                    updated += 1

        return SaveStats(inserted=inserted, updated=updated)

    def read_samples(self, sample_limit: int) -> PostgresSampleResult:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM crawl_items")
                total_count_row = cursor.fetchone()
                total_count = int(total_count_row[0]) if total_count_row is not None else 0
                cursor.execute(
                    """
                    SELECT post_id, title, price, url
                    FROM crawl_items
                    ORDER BY last_seen_at DESC
                    LIMIT %s
                    """,
                    (sample_limit,),
                )
                rows = cursor.fetchall()

        sample_items = [
            {
                "post_id": row[0],
                "title": row[1],
                "price": row[2],
                "url": row[3],
            }
            for row in rows
        ]
        return PostgresSampleResult(total_count=total_count, sample_items=sample_items)

    def read_price_stats(self, days: int) -> dict[str, float | int | None]:
        if days <= 0:
            raise ValueError("days must be greater than 0")

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*)::BIGINT,
                        AVG(NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT),
                        MIN(NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT),
                        MAX(NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT)
                    FROM crawl_items
                    WHERE fetched_at >= NOW() - (%s * INTERVAL '1 day')
                    """,
                    (days,),
                )
                row = cursor.fetchone()

        if row is None:
            return {"count": 0, "avg_price": None, "min_price": None, "max_price": None}

        return {
            "count": int(row[0] or 0),
            "avg_price": float(row[1]) if row[1] is not None else None,
            "min_price": float(row[2]) if row[2] is not None else None,
            "max_price": float(row[3]) if row[3] is not None else None,
        }

    def read_window_stats(self) -> dict[str, dict[str, float | int | None]]:
        return {
            "30d": self.read_price_stats(30),
            "90d": self.read_price_stats(90),
        }
