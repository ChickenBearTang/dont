from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import importlib
import re
from typing import Any, Callable

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
_PRIMARY_PRICE_TOKEN_PATTERN = re.compile(r"\d{1,3}(?:,\d{3})+|\d{4,9}")
_TITLE_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\uAC00-\uD7A3]+(?:\.[A-Za-z0-9]+)*")
_STORE_PREFIX_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*")
_GENERIC_SEARCH_TOKENS = {
    "\uAD6C\uB9E4",
    "\uC694\uCCAD",
    "\uD2B9\uAC00",
    "\uC815\uBC1C",
    "\uC9C1\uAD6C",
    "\uBB34\uB8CC",
    "\uBB34\uBC30",
    "\uB2F9\uC77C\uCD9C\uACE0",
    "\uD589\uC0AC",
    "\uD560\uC778",
}
_MEANINGFUL_SHORT_TOKENS = {
    "\uD329",
    "g",
    "kg",
    "ml",
    "l",
}
_SEARCH_TOKEN_ALIASES = {
    "\uADF8\uB7A8": "gram",
    "gram": "gram",
    "\uC5D8\uC9C0": "lg",
    "lg": "lg",
    "\uB9E5\uBD81": "macbook",
    "macbook": "macbook",
    "\uC560\uD50C": "apple",
    "apple": "apple",
    "\uB85C\uC9C0\uD14D": "logitech",
    "logitech": "logitech",
}
_GRAM_WEIGHT_PATTERN = re.compile(r"(?<![a-z])\d+\s*그램")
_GRAM_SPLIT_PATTERNS = (
    (re.compile(r"lg그램", re.IGNORECASE), "lg 그램"),
    (re.compile(r"lggram", re.IGNORECASE), "lg gram"),
)
_HANGUL_DIGIT_BOUNDARY_PATTERN = re.compile(r"(?<=[가-힣])(?=\d)|(?<=\d)(?=[가-힣])")
_GRAM_SERIES_BOUNDARY_PATTERN = re.compile(r"(?<=gram)(?=\d)", re.IGNORECASE)
_BRAND_TOKENS = {
    "lg",
    "apple",
    "logitech",
    "samsung",
    "asus",
    "lenovo",
    "hp",
    "dell",
    "msi",
    "gigabyte",
    "zotac",
    "anker",
    "razer",
    "vgn",
    "atk",
    "thermalright",
}
_SERIES_TOKENS = {
    "gram",
    "macbook",
    "galaxybook",
    "mx",
    "master",
    "superlight",
    "ultra",
    "pro",
    "air",
}
_SPEC_TOKEN_PATTERN = re.compile(
    r"(?<![a-z0-9])\d+(?:\.\d+)?\s*(?:gb|tb|kg|g|ml|l|\uD329|\uC778\uCE58|hz|w|mah|mm|cm|m)(?![a-z])",
    re.IGNORECASE,
)


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
    _MIN_VALID_PRICE_KRW = 100
    _MAX_VALID_PRICE_KRW = 100_000_000

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
    def _canonicalize_search_token(token: str) -> str:
        lowered = token.strip().lower()
        if lowered == "":
            return ""
        return _SEARCH_TOKEN_ALIASES.get(lowered, lowered)

    @classmethod
    def _prepare_title_for_tokenizing(cls, title: str | None) -> str:
        if title is None:
            return ""
        normalized = cls._strip_store_prefix(title).lower()
        for pattern, replacement in _GRAM_SPLIT_PATTERNS:
            normalized = pattern.sub(replacement, normalized)
        normalized = _GRAM_SERIES_BOUNDARY_PATTERN.sub(" ", normalized)
        normalized = _HANGUL_DIGIT_BOUNDARY_PATTERN.sub(" ", normalized)
        normalized = _GRAM_WEIGHT_PATTERN.sub(" ", normalized)
        return normalized

    @staticmethod
    def _strip_store_prefix(title: str | None) -> str:
        if title is None:
            return ""
        return _STORE_PREFIX_PATTERN.sub("", title).strip()

    @classmethod
    def _extract_store_tokens(cls, title: str | None) -> list[str]:
        if title is None:
            return []
        match = _STORE_PREFIX_PATTERN.match(title)
        if match is None:
            return []
        return cls._extract_search_tokens(match.group(1), drop_generic=False)

    @classmethod
    def _extract_search_tokens(
        cls,
        title: str | None,
        *,
        drop_generic: bool,
    ) -> list[str]:
        if title is None:
            return []
        tokens: list[str] = []
        seen: set[str] = set()
        prepared_title = cls._prepare_title_for_tokenizing(title)
        for raw_token in _TITLE_TOKEN_PATTERN.findall(prepared_title):
            token = cls._canonicalize_search_token(raw_token)
            if token == "":
                continue
            if drop_generic and token in _GENERIC_SEARCH_TOKENS:
                continue
            if (
                len(token) < 2
                and not token.isdigit()
                and token not in _MEANINGFUL_SHORT_TOKENS
            ):
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
        merged_tokens: list[str] = []
        index = 0
        while index < len(tokens):
            current = tokens[index]
            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if (
                current.isdigit()
                and next_token in _MEANINGFUL_SHORT_TOKENS
            ):
                merged_tokens.append(f"{current}{next_token}")
                index += 2
                continue
            merged_tokens.append(current)
            index += 1
        return merged_tokens

    @classmethod
    def _normalize_title_for_search(cls, title: str | None) -> str:
        return " ".join(cls._extract_search_tokens(title, drop_generic=False))

    @classmethod
    def _build_search_token_text(cls, title: str | None) -> str:
        tokens = cls._extract_search_tokens(title, drop_generic=False)
        if len(tokens) == 0:
            return ""
        return f" {' '.join(tokens)} "

    @staticmethod
    def _build_token_text(tokens: list[str]) -> str:
        if len(tokens) == 0:
            return ""
        return f" {' '.join(tokens)} "

    @classmethod
    def _extract_brand_tokens(cls, title: str | None) -> list[str]:
        tokens = cls._extract_search_tokens(title, drop_generic=False)
        return [token for token in tokens if token in _BRAND_TOKENS]

    @classmethod
    def _extract_model_tokens(cls, title: str | None) -> list[str]:
        tokens = cls._extract_search_tokens(title, drop_generic=True)
        model_tokens = [
            token
            for token in tokens
            if any(character.isdigit() for character in token)
            and any(character.isalpha() for character in token)
            and len(token) >= 5
        ]
        phrase_model = ""
        if len(model_tokens) == 0:
            phrase_model = cls._extract_phrase_model_token(tokens)
        if phrase_model != "" and phrase_model not in model_tokens:
            model_tokens.append(phrase_model)
        return model_tokens

    @classmethod
    def _extract_series_tokens(cls, title: str | None) -> list[str]:
        tokens = cls._extract_search_tokens(title, drop_generic=True)
        series_tokens = [token for token in tokens if token in _SERIES_TOKENS]
        phrase_series = cls._extract_phrase_series_token(tokens)
        if (
            phrase_series != ""
            and phrase_series not in series_tokens
            and phrase_series != " ".join(series_tokens[: len(phrase_series.split())])
        ):
            series_tokens.append(phrase_series)
        return series_tokens

    @classmethod
    def _extract_spec_tokens(cls, title: str | None) -> list[str]:
        prepared_title = cls._prepare_title_for_tokenizing(title)
        if prepared_title == "":
            return []
        tokens: list[str] = []
        seen: set[str] = set()
        for match in _SPEC_TOKEN_PATTERN.finditer(prepared_title):
            token = re.sub(r"\s+", "", match.group(0).lower())
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
        return tokens

    @classmethod
    def _extract_phrase_series_token(cls, tokens: list[str]) -> str:
        if len(tokens) < 4:
            return ""
        if tokens[0] not in _BRAND_TOKENS:
            return ""

        candidate: list[str] = []
        for token in tokens[1:]:
            if token in _GENERIC_SEARCH_TOKENS:
                continue
            if any(character.isdigit() for character in token):
                break
            if token in _MEANINGFUL_SHORT_TOKENS:
                break
            if len(token) < 2:
                continue
            candidate.append(token)
            if len(candidate) >= 2:
                break
        return " ".join(candidate)

    @classmethod
    def _extract_phrase_model_token(cls, tokens: list[str]) -> str:
        if len(tokens) < 4:
            return ""
        if tokens[0] not in _BRAND_TOKENS:
            return ""

        numeric_start: int | None = None
        for index, token in enumerate(tokens[1:], start=1):
            if any(character.isdigit() for character in token):
                numeric_start = index
                break
        if numeric_start is None:
            return ""

        candidate: list[str] = []
        for token in tokens[numeric_start:]:
            if token in _GENERIC_SEARCH_TOKENS:
                continue
            if len(token) < 2 and not token.isdigit():
                continue
            candidate.append(token)
            if len(candidate) >= 3:
                break
        return " ".join(candidate)

    @classmethod
    def _build_query_token_groups(cls, phrases: list[str]) -> list[list[str]]:
        groups: list[list[str]] = []
        seen_groups: set[tuple[str, ...]] = set()
        for phrase in phrases:
            tokens = cls._extract_search_tokens(phrase, drop_generic=True)
            if len(tokens) == 0:
                continue
            group_key = tuple(tokens)
            if group_key in seen_groups:
                continue
            seen_groups.add(group_key)
            groups.append(tokens)
        return groups

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
        token_match = _PRIMARY_PRICE_TOKEN_PATTERN.search(cleaned)
        if token_match is None:
            return None
        digits = token_match.group(0).replace(",", "")
        parsed = int(digits)
        if not PostgresCrawlStore._is_reasonable_price(parsed):
            return None
        return str(parsed)

    @classmethod
    def _is_reasonable_price(cls, value: int | float | None) -> bool:
        if value is None:
            return False
        numeric = float(value)
        return cls._MIN_VALID_PRICE_KRW <= numeric <= cls._MAX_VALID_PRICE_KRW

    @staticmethod
    def _convert_foreign_price_to_krw(price_text: str) -> int | None:
        amount = PostgresCrawlStore._extract_amount(price_text)
        if amount is None:
            return None

        # "¥" can represent both JPY and CNY; prioritize explicit CNY markers.
        if _CNY_PATTERN.search(price_text):
            converted = int(round(amount * PostgresCrawlStore._CNY_TO_KRW))
            return (
                converted
                if PostgresCrawlStore._is_reasonable_price(converted)
                else None
            )
        if _JPY_PATTERN.search(price_text):
            converted = int(round(amount * PostgresCrawlStore._JPY_TO_KRW))
            return (
                converted
                if PostgresCrawlStore._is_reasonable_price(converted)
                else None
            )
        if _USD_PATTERN.search(price_text):
            converted = int(round(amount * PostgresCrawlStore._USD_TO_KRW))
            return (
                converted
                if PostgresCrawlStore._is_reasonable_price(converted)
                else None
            )
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
                        normalized_title TEXT NOT NULL DEFAULT '',
                        search_tokens TEXT NOT NULL DEFAULT '',
                        store_tokens TEXT NOT NULL DEFAULT '',
                        brand_tokens TEXT NOT NULL DEFAULT '',
                        model_tokens TEXT NOT NULL DEFAULT '',
                        series_tokens TEXT NOT NULL DEFAULT '',
                        spec_tokens TEXT NOT NULL DEFAULT '',
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
                    ADD COLUMN IF NOT EXISTS normalized_title TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS search_tokens TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS store_tokens TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS brand_tokens TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS model_tokens TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS series_tokens TEXT NOT NULL DEFAULT ''
                    """
                )
                cursor.execute(
                    """
                    ALTER TABLE crawl_items
                    ADD COLUMN IF NOT EXISTS spec_tokens TEXT NOT NULL DEFAULT ''
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
                    CREATE INDEX IF NOT EXISTS idx_crawl_items_outlier
                    ON crawl_items (is_outlier)
                    """
                )
                cursor.execute(
                    """
                    SELECT url, title
                    FROM crawl_items
                    WHERE COALESCE(normalized_title, '') = ''
                       OR COALESCE(search_tokens, '') = ''
                       OR COALESCE(store_tokens, '') = ''
                       OR COALESCE(brand_tokens, '') = ''
                       OR COALESCE(model_tokens, '') = ''
                       OR COALESCE(series_tokens, '') = ''
                       OR COALESCE(spec_tokens, '') = ''
                    """
                )
                rows_to_backfill = cursor.fetchall()
                for row in rows_to_backfill:
                    url = str(row[0])
                    title = str(row[1])
                    brand_tokens = self._build_token_text(
                        self._extract_brand_tokens(title)
                    )
                    store_tokens = self._build_token_text(
                        self._extract_store_tokens(title)
                    )
                    model_tokens = self._build_token_text(
                        self._extract_model_tokens(title)
                    )
                    series_tokens = self._build_token_text(
                        self._extract_series_tokens(title)
                    )
                    spec_tokens = self._build_token_text(
                        self._extract_spec_tokens(title)
                    )
                    cursor.execute(
                        """
                        UPDATE crawl_items
                        SET normalized_title = %s,
                            search_tokens = %s,
                            store_tokens = %s,
                            brand_tokens = %s,
                            model_tokens = %s,
                            series_tokens = %s,
                            spec_tokens = %s
                        WHERE url = %s
                        """,
                        (
                            self._normalize_title_for_search(title),
                            self._build_search_token_text(title),
                            store_tokens,
                            brand_tokens,
                            model_tokens,
                            series_tokens,
                            spec_tokens,
                            url,
                        ),
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
                    normalized_title = self._normalize_title_for_search(deal.title)
                    search_tokens = self._build_search_token_text(deal.title)
                    store_tokens = self._build_token_text(
                        self._extract_store_tokens(deal.title)
                    )
                    brand_tokens = self._build_token_text(
                        self._extract_brand_tokens(deal.title)
                    )
                    model_tokens = self._build_token_text(
                        self._extract_model_tokens(deal.title)
                    )
                    series_tokens = self._build_token_text(
                        self._extract_series_tokens(deal.title)
                    )
                    spec_tokens = self._build_token_text(
                        self._extract_spec_tokens(deal.title)
                    )
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
                                normalized_title,
                                search_tokens,
                                store_tokens,
                                brand_tokens,
                                model_tokens,
                                series_tokens,
                                spec_tokens,
                                price,
                                posted_at,
                                fetched_at,
                                first_seen_at,
                                last_seen_at,
                                is_outlier,
                                outlier_reason,
                                outlier_marked_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NULL, NULL)
                            """,
                            (
                                result.source,
                                post_id,
                                deal.url,
                                deal.title,
                                normalized_title,
                                search_tokens,
                                store_tokens,
                                brand_tokens,
                                model_tokens,
                                series_tokens,
                                spec_tokens,
                                normalized_price,
                                deal.posted_at,
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
                            normalized_title = %s,
                            search_tokens = %s,
                            store_tokens = %s,
                            brand_tokens = %s,
                            model_tokens = %s,
                            series_tokens = %s,
                            spec_tokens = %s,
                            price = %s,
                            posted_at = %s,
                            fetched_at = %s,
                            last_seen_at = %s,
                            is_outlier = FALSE,
                            outlier_reason = NULL,
                            outlier_marked_at = NULL
                        WHERE url = %s
                        """,
                        (
                            result.source,
                            post_id,
                            deal.title,
                            normalized_title,
                            search_tokens,
                            store_tokens,
                            brand_tokens,
                            model_tokens,
                            series_tokens,
                            spec_tokens,
                            normalized_price,
                            deal.posted_at,
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
                total_count = (
                    int(total_count_row[0]) if total_count_row is not None else 0
                )
                cursor.execute(
                    """
                    SELECT post_id, title, price, url, posted_at, COALESCE(is_outlier, FALSE), outlier_reason
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
            }
            for row in rows
        ]
        return PostgresSampleResult(total_count=total_count, sample_items=sample_items)

    def read_price_stats(
        self,
        days: int,
        *,
        title_keywords: list[str] | None = None,
        brand_tokens: list[str] | None = None,
        model_tokens: list[str] | None = None,
    ) -> dict[str, float | int | None]:
        if days <= 0:
            raise ValueError("days must be greater than 0")

        normalized_keywords = self._normalize_filters(title_keywords or [])
        token_groups = self._build_query_token_groups(normalized_keywords)
        title_clause = ""
        title_params: list[object] = []
        if len(token_groups) > 0:
            group_clauses: list[str] = []
            for group in token_groups:
                group_clauses.append(
                    "("
                    + " AND ".join(
                        ["COALESCE(search_tokens, '') LIKE %s"] * len(group)
                    )
                    + ")"
                )
                title_params.extend([f"% {token} %" for token in group])
            title_clause = " AND (" + " OR ".join(group_clauses) + ")"

        brand_clause = ""
        brand_params: list[object] = []
        normalized_brands = self._normalize_filters(brand_tokens or [])
        if len(normalized_brands) > 0:
            brand_clause = " AND (" + " OR ".join(
                ["COALESCE(brand_tokens, '') LIKE %s"] * len(normalized_brands)
            ) + ")"
            brand_params = [f"% {brand} %" for brand in normalized_brands]

        model_clause = ""
        model_params: list[object] = []
        normalized_models = self._normalize_filters(model_tokens or [])
        if len(normalized_models) > 0:
            model_clause = " AND (" + " OR ".join(
                ["COALESCE(model_tokens, '') LIKE %s"] * len(normalized_models)
            ) + ")"
            model_params = [f"% {model} %" for model in normalized_models]

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    WITH normalized AS (
                        SELECT
                            title,
                            search_tokens,
                            brand_tokens,
                            model_tokens,
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
                      AND numeric_price BETWEEN %s AND %s
                      {title_clause}
                      {brand_clause}
                      {model_clause}
                    """,
                    tuple(
                        [days, self._MIN_VALID_PRICE_KRW, self._MAX_VALID_PRICE_KRW]
                        + title_params
                        + brand_params
                        + model_params
                    ),
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
        *,
        title_keywords: list[str] | None = None,
        brand_tokens: list[str] | None = None,
        model_tokens: list[str] | None = None,
    ) -> dict[str, dict[str, float | int | None]]:
        return {
            "30d": self.read_price_stats(
                30,
                title_keywords=title_keywords,
                brand_tokens=brand_tokens,
                model_tokens=model_tokens,
            ),
            "90d": self.read_price_stats(
                90,
                title_keywords=title_keywords,
                brand_tokens=brand_tokens,
                model_tokens=model_tokens,
            ),
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
