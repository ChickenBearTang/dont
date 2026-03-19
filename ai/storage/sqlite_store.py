from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import sqlite3

from ai.models import CrawlResult
from ai.models import HotDeal

_POST_ID_PATTERN = re.compile(r"/views/(\d+)")


@dataclass(frozen=True)
class SaveStats:
    inserted: int
    updated: int


class SqliteCrawlStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialize()

    @staticmethod
    def _extract_post_id(url: str) -> str | None:
        match = _POST_ID_PATTERN.search(url)
        if match is None:
            return None
        return match.group(1)

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
                            fetched_at,
                            first_seen_at,
                            last_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result.source,
                            post_id,
                            deal.url,
                            deal.title,
                            deal.price,
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
                        fetched_at = ?,
                        last_seen_at = ?
                    WHERE url = ?
                    """,
                    (
                        result.source,
                        post_id,
                        deal.title,
                        deal.price,
                        result.fetched_at.isoformat(),
                        now,
                        deal.url,
                    ),
                )
                updated += 1

        return SaveStats(inserted=inserted, updated=updated)
