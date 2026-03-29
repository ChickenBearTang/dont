from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import importlib
import re
from typing import Any, Callable
from urllib.parse import unquote

from ..models import CrawlResult
from ..models import HotDeal
from .base import SaveStats

_POST_ID_PATTERN = re.compile(r"/views/(\d+)")
_FOREIGN_CURRENCY_PATTERN = re.compile(r"(?:USD|JPY|CNY|US\$|¥|￥|円|엔|위안|달러|\$)", re.IGNORECASE)
_KRW_TOKEN_PATTERN = re.compile(r"(?:₩|원|KRW)", re.IGNORECASE)
_ALPHA_PATTERN = re.compile(r"[A-Za-z]")
_USD_PATTERN = re.compile(r"(?:\bUSD\b|US\$|달러|\$)", re.IGNORECASE)
_JPY_PATTERN = re.compile(r"(?:\bJPY\b|YEN|円|엔|¥|￥)", re.IGNORECASE)
_CNY_PATTERN = re.compile(r"(?:\bCNY\b|RMB|元|위안)", re.IGNORECASE)
_NUMERIC_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")
_ITEM_FAMILY_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9\uac00-\ud7a3]+")


@dataclass(frozen=True)
class PostgresSampleResult:
    total_count: int
    sample_items: list[dict[str, str | bool | None]]


@dataclass(frozen=True)
class OutlierScopeResult:
    channel: str
    keyword: str
    reviewed_count: int
    marked_count: int
    lower_bound: float | None
    upper_bound: float | None


@dataclass(frozen=True)
class OutlierMarkResult:
    reviewed_rows: int
    marked_rows: int
    scopes: list[OutlierScopeResult]


class PostgresCrawlStore:
    _USD_TO_KRW = 1500.0
    _JPY_TO_KRW = 9.5
    _CNY_TO_KRW = 215.0
    _ITEM_FAMILY_ALIASES: dict[str, str] = {
        "f87": "f87",
        "f87pro": "f87",
        "mxmaster3": "mx_master",
        "mxmaster3s": "mx_master",
        "mxmaster": "mx_master",
        "mx": "mx_master",
        "vxer1": "vxe_r1",
        "vxe": "vxe_r1",
        "vxer1pro": "vxe_r1",
    }

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
    def _normalize_item_family_text(value: str | None) -> str:
        if value is None:
            return ""
        lowered = value.lower()
        try:
            lowered = unquote(lowered)
        except Exception:
            pass
        return _ITEM_FAMILY_NORMALIZE_PATTERN.sub("", lowered)

    @classmethod
    def classify_item_family(cls, *, title: str | None, url: str | None = None) -> str | None:
        normalized = cls._normalize_item_family_text(f"{title or ''} {url or ''}")
        if normalized == "":
            return None
        if "vxer1" in normalized or ("vxe" in normalized and "r1" in normalized):
            return "vxe_r1"
        if (
            "f87" in normalized
            or "f87pro" in normalized
            or "\ub3c5\uac70\ubbf887" in normalized
            or ("\ub3c5\uac70\ubbf8" in normalized and "87" in normalized)
        ):
            return "f87"
        has_mx = "mx" in normalized
        has_master_like = (
            "master" in normalized
            or "\ub9c8\uc2a4\ud130" in normalized
            or "\ub9c8\uc6b0\uc2a4" in normalized
            or "\ub9c8\uc2a4\uc5b4" in normalized
        )
        has_generation = "3s" in normalized or "3" in normalized
        if has_mx and has_master_like and has_generation:
            return "mx_master"
        return None

    @classmethod
    def normalize_item_family_filter(cls, raw_value: str | None) -> str | None:
        normalized = cls._normalize_item_family_text(raw_value)
        if normalized == "":
            return None
        alias = cls._ITEM_FAMILY_ALIASES.get(normalized)
        if alias is not None:
            return alias
        return cls.classify_item_family(title=raw_value, url=None)

    @staticmethod
    def _normalize_krw_price(price: str | None) -> str | None:
        if price is None:
            return None
        normalized = price.strip()
        if normalized == "":
            return None
        if _FOREIGN_CURRENCY_PATTERN.search(normalized):
            converted = PostgresCrawlStore._convert_foreign_price_to_krw(normalized)
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
        amount = PostgresCrawlStore._extract_amount(price_text)
        if amount is None:
            return None

        if _CNY_PATTERN.search(price_text):
            return int(round(amount * PostgresCrawlStore._CNY_TO_KRW))
        if _JPY_PATTERN.search(price_text):
            return int(round(amount * PostgresCrawlStore._JPY_TO_KRW))
        if _USD_PATTERN.search(price_text):
            return int(round(amount * PostgresCrawlStore._USD_TO_KRW))
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
                        posted_at TEXT,
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
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS posted_at TEXT
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS is_outlier BOOLEAN NOT NULL DEFAULT FALSE
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS outlier_reason TEXT
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS outlier_marked_at TIMESTAMPTZ
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS item_family TEXT
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_crawl_items_outlier
                    ON crawl_items (is_outlier)
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_crawl_items_item_family
                    ON crawl_items (item_family)
                    """
                )
                self._backfill_item_family(cursor)

    def _backfill_item_family(self, cursor: Any, batch_size: int = 500) -> None:
        while True:
            cursor.execute(
                """
                SELECT url, title
                FROM crawl_items
                WHERE COALESCE(item_family, '') = ''
                ORDER BY last_seen_at DESC
                LIMIT %s
                """,
                (batch_size,),
            )
            rows = cursor.fetchall()
            if len(rows) == 0:
                return
            for row in rows:
                url = str(row[0]) if row[0] is not None else ""
                title = str(row[1]) if row[1] is not None else ""
                item_family = self.classify_item_family(title=title, url=url)
                if item_family is None:
                    continue
                cursor.execute(
                    """
                    UPDATE crawl_items
                    SET item_family = %s
                    WHERE url = %s
                    """,
                    (item_family, url),
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
                    normalized_price = self._normalize_krw_price(deal.price)
                    item_family = self.classify_item_family(title=deal.title, url=deal.url)
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
                                posted_at,
                                fetched_at,
                                first_seen_at,
                                last_seen_at,
                                item_family,
                                is_outlier,
                                outlier_reason,
                                outlier_marked_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NULL, NULL)
                            """,
                            (
                                result.source,
                                post_id,
                                deal.url,
                                deal.title,
                                normalized_price,
                                deal.posted_at,
                                result.fetched_at,
                                now,
                                now,
                                item_family,
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
                            posted_at = %s,
                            fetched_at = %s,
                            last_seen_at = %s,
                            item_family = %s,
                            is_outlier = FALSE,
                            outlier_reason = NULL,
                            outlier_marked_at = NULL
                        WHERE url = %s
                        """,
                        (
                            result.source,
                            post_id,
                            deal.title,
                            normalized_price,
                            deal.posted_at,
                            result.fetched_at,
                            now,
                            item_family,
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
                total_count = (
                    int(total_count_row[0]) if total_count_row is not None else 0
                )
                cursor.execute(
                    """
                    SELECT
                        post_id,
                        title,
                        price,
                        url,
                        posted_at,
                        COALESCE(is_outlier, FALSE),
                        outlier_reason,
                        item_family
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
                "posted_at": row[4] if len(row) > 4 else None,
                "is_outlier": bool(row[5]) if len(row) > 5 else False,
                "outlier_reason": row[6] if len(row) > 6 else None,
                "item_family": row[7] if len(row) > 7 else None,
            }
            for row in rows
        ]
        return PostgresSampleResult(total_count=total_count, sample_items=sample_items)

    def read_price_stats(
        self,
        days: int,
        item_family: str | None = None,
    ) -> dict[str, float | int | None]:
        if days <= 0:
            raise ValueError("days must be greater than 0")
        normalized_family = self.normalize_item_family_filter(item_family)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                if normalized_family is None:
                    cursor.execute(
                        """
                        WITH normalized AS (
                            SELECT
                                CASE
                                    WHEN posted_at ~ '^\\d{4}[./-]\\d{1,2}[./-]\\d{1,2}$' THEN
                                        to_date(replace(replace(posted_at, '.', '-'), '/', '-'), 'YYYY-MM-DD')::timestamp
                                    WHEN posted_at ~ '^\\d{1,2}[./-]\\d{1,2}$' THEN
                                        to_date(
                                            extract(year from now())::text || '-' || replace(replace(posted_at, '.', '-'), '/', '-'),
                                            'YYYY-MM-DD'
                                        )::timestamp
                                    ELSE NULL
                                END AS posted_at_ts,
                                fetched_at,
                                NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT AS numeric_price,
                                COALESCE(is_outlier, FALSE) AS is_outlier
                            FROM crawl_items
                        )
                        SELECT
                            COUNT(*)::BIGINT,
                            AVG(numeric_price),
                            MIN(numeric_price),
                            MAX(numeric_price)
                        FROM normalized
                        WHERE COALESCE(posted_at_ts, fetched_at) >= NOW() - (%s * INTERVAL '1 day')
                          AND is_outlier = FALSE
                        """,
                        (days,),
                    )
                else:
                    cursor.execute(
                        """
                        WITH normalized AS (
                            SELECT
                                CASE
                                    WHEN posted_at ~ '^\\d{4}[./-]\\d{1,2}[./-]\\d{1,2}$' THEN
                                        to_date(replace(replace(posted_at, '.', '-'), '/', '-'), 'YYYY-MM-DD')::timestamp
                                    WHEN posted_at ~ '^\\d{1,2}[./-]\\d{1,2}$' THEN
                                        to_date(
                                            extract(year from now())::text || '-' || replace(replace(posted_at, '.', '-'), '/', '-'),
                                            'YYYY-MM-DD'
                                        )::timestamp
                                    ELSE NULL
                                END AS posted_at_ts,
                                fetched_at,
                                NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT AS numeric_price,
                                COALESCE(is_outlier, FALSE) AS is_outlier,
                                item_family
                            FROM crawl_items
                        )
                        SELECT
                            COUNT(*)::BIGINT,
                            AVG(numeric_price),
                            MIN(numeric_price),
                            MAX(numeric_price)
                        FROM normalized
                        WHERE COALESCE(posted_at_ts, fetched_at) >= NOW() - (%s * INTERVAL '1 day')
                          AND is_outlier = FALSE
                          AND item_family = %s
                        """,
                        (days, normalized_family),
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

    def read_window_stats(
        self,
        item_family: str | None = None,
    ) -> dict[str, dict[str, float | int | None]]:
        return {
            "30d": self.read_price_stats(30, item_family=item_family),
            "90d": self.read_price_stats(90, item_family=item_family),
        }

    @staticmethod
    def _normalize_filters(values: list[str]) -> list[str]:
        normalized = [value.strip().lower() for value in values if value.strip()]
        deduped: list[str] = []
        seen: set[str] = set()
        for value in normalized:
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

    @staticmethod
    def _percentile(sorted_values: list[float], ratio: float) -> float:
        if len(sorted_values) == 0:
            raise ValueError("sorted_values must not be empty")
        if len(sorted_values) == 1:
            return sorted_values[0]

        rank = (len(sorted_values) - 1) * ratio
        lower_index = int(rank)
        upper_index = min(lower_index + 1, len(sorted_values) - 1)
        weight = rank - lower_index
        return (
            sorted_values[lower_index] * (1.0 - weight)
            + sorted_values[upper_index] * weight
        )

    @classmethod
    def _iqr_bounds(
        cls,
        prices: list[float],
        *,
        iqr_multiplier: float,
    ) -> tuple[float, float]:
        sorted_values = sorted(prices)
        q1 = cls._percentile(sorted_values, 0.25)
        q3 = cls._percentile(sorted_values, 0.75)
        iqr = q3 - q1
        lower_bound = max(q1 - (iqr * iqr_multiplier), 0.0)
        upper_bound = q3 + (iqr * iqr_multiplier)
        return lower_bound, upper_bound

    def mark_price_outliers(
        self,
        *,
        channels: list[str],
        keywords: list[str],
        days: int = 90,
        iqr_multiplier: float = 1.5,
        min_group_size: int = 4,
    ) -> OutlierMarkResult:
        if days <= 0:
            raise ValueError("days must be greater than 0")
        if iqr_multiplier <= 0:
            raise ValueError("iqr_multiplier must be greater than 0")
        if min_group_size < 3:
            raise ValueError("min_group_size must be at least 3")

        normalized_channels = self._normalize_filters(channels)
        normalized_keywords = self._normalize_filters(keywords)
        if len(normalized_channels) == 0:
            raise ValueError("channels must not be empty")
        if len(normalized_keywords) == 0:
            raise ValueError("keywords must not be empty")

        reviewed_rows = 0
        marked_rows = 0
        scope_results: list[OutlierScopeResult] = []
        marked_at = self._now_utc()

        with self._connect() as connection:
            with connection.cursor() as cursor:
                for channel in normalized_channels:
                    channel_like = f"%{channel}%"
                    for keyword in normalized_keywords:
                        keyword_like = f"%{keyword}%"

                        cursor.execute(
                            """
                            SELECT
                                url,
                                title,
                                NULLIF(
                                    regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'),
                                    ''
                                )::BIGINT AS numeric_price
                            FROM crawl_items
                            WHERE fetched_at >= NOW() - (%s * INTERVAL '1 day')
                              AND LOWER(source) LIKE %s
                              AND LOWER(title) LIKE %s
                              AND NULLIF(
                                    regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'),
                                    ''
                              ) IS NOT NULL
                            """,
                            (days, channel_like, keyword_like),
                        )
                        rows = cursor.fetchall()

                        cursor.execute(
                            """
                            UPDATE crawl_items
                            SET
                                is_outlier = FALSE,
                                outlier_reason = NULL,
                                outlier_marked_at = NULL
                            WHERE fetched_at >= NOW() - (%s * INTERVAL '1 day')
                              AND LOWER(source) LIKE %s
                              AND LOWER(title) LIKE %s
                            """,
                            (days, channel_like, keyword_like),
                        )

                        parsed_rows = [
                            (str(row[0]), float(row[2]))
                            for row in rows
                            if row[2] is not None and float(row[2]) > 0
                        ]
                        reviewed_count = len(parsed_rows)
                        reviewed_rows += reviewed_count

                        if reviewed_count < min_group_size:
                            scope_results.append(
                                OutlierScopeResult(
                                    channel=channel,
                                    keyword=keyword,
                                    reviewed_count=reviewed_count,
                                    marked_count=0,
                                    lower_bound=None,
                                    upper_bound=None,
                                )
                            )
                            continue

                        prices = [price for _, price in parsed_rows]
                        lower_bound, upper_bound = self._iqr_bounds(
                            prices,
                            iqr_multiplier=iqr_multiplier,
                        )
                        outlier_urls = [
                            url
                            for url, price in parsed_rows
                            if price < lower_bound or price > upper_bound
                        ]

                        reason = (
                            "IQR_OUTLIER"
                            f"(channel={channel},keyword={keyword},"
                            f"lower={int(lower_bound)},upper={int(upper_bound)})"
                        )
                        for url in outlier_urls:
                            cursor.execute(
                                """
                                UPDATE crawl_items
                                SET
                                    is_outlier = TRUE,
                                    outlier_reason = %s,
                                    outlier_marked_at = %s
                                WHERE url = %s
                                """,
                                (reason, marked_at, url),
                            )

                        marked_count = len(outlier_urls)
                        marked_rows += marked_count
                        scope_results.append(
                            OutlierScopeResult(
                                channel=channel,
                                keyword=keyword,
                                reviewed_count=reviewed_count,
                                marked_count=marked_count,
                                lower_bound=lower_bound,
                                upper_bound=upper_bound,
                            )
                        )

        return OutlierMarkResult(
            reviewed_rows=reviewed_rows,
            marked_rows=marked_rows,
            scopes=scope_results,
        )
