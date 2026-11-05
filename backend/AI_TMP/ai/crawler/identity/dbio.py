"""크롤 DB 에서 제목을 뽑고, 사람이 붙인 정답을 읽는다 (읽기 전용).

테스트 환경의 DB 에는 수집한 제목이 들어 있다(crawl_items.title). 거기서 라벨링할 제목을 뽑고,
사람이 DB 에 붙인 정답(예: 별도 테이블의 title, product_id)을 읽어 평가에 쓴다.
쓰기/수정은 하지 않으며, 정답을 읽는 SQL 은 SELECT 문 하나만 받아들인다.
"""

from __future__ import annotations

import importlib
import os
import re
from typing import Any, Callable

Connector = Callable[[str], Any]


def default_dsn() -> str:
    """run_to_postgres 와 같은 규칙: AI_POSTGRES_DSN, 없으면 AI_POSTGRES_* 조각으로 조립."""
    explicit = os.environ.get("AI_POSTGRES_DSN", "").strip()
    if explicit:
        return explicit
    host = os.environ.get("AI_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("AI_POSTGRES_PORT", "55432")
    db = os.environ.get("AI_POSTGRES_DB", "ai_crawl")
    user = os.environ.get("AI_POSTGRES_USER", "ai_user")
    password = os.environ.get("AI_POSTGRES_PASSWORD", "ai_password")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _connect(dsn: str, connector: Connector | None) -> Any:
    if connector is not None:
        return connector(dsn)
    try:
        return importlib.import_module("psycopg").connect(dsn)
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg package is required to read the crawl database") from exc


def _query(dsn: str, sql: str, params: list[Any], connector: Connector | None) -> list[tuple[Any, ...]]:
    connection = _connect(dsn, connector)
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or None)
            return list(cursor.fetchall())
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


def fetch_titles(
    dsn: str,
    *,
    source: str | None = None,
    since: str | None = None,
    limit: int | None = None,
    connector: Connector | None = None,
) -> list[str]:
    where: list[str] = []
    params: list[Any] = []
    if source:
        where.append("source = %s")
        params.append(source)
    if since:
        where.append("last_seen_at >= %s")
        params.append(since)
    sql = "SELECT title FROM crawl_items"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY last_seen_at DESC"
    if limit:
        sql += " LIMIT %s"
        params.append(int(limit))
    rows = _query(dsn, sql, params, connector)
    return [str(r[0]) for r in rows if r and isinstance(r[0], str) and r[0].strip()]


_SELECT_ONLY = re.compile(r"^\s*select\b", re.IGNORECASE)


def _check_read_only(sql: str) -> str:
    # 주석을 지운 뒤 세미콜론이 끝에만 있어야 한다 (문장 하나). 'SELECT' 로 시작해야 한다.
    stripped = re.sub(r"--[^\n]*", "", sql)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL).strip().rstrip(";").strip()
    if not stripped or not _SELECT_ONLY.match(stripped) or ";" in stripped:
        raise ValueError("정답을 읽는 SQL 은 SELECT 문 하나만 받는다")
    return stripped


def fetch_labels(dsn: str, sql: str, *, connector: Connector | None = None) -> list[dict[str, Any]]:
    """(title, id) 를 돌려주는 SELECT 로 정답을 읽는다. id 가 비면 '카탈로그에 없음'(None)이다."""
    safe_sql = _check_read_only(sql)
    rows = _query(dsn, safe_sql, [], connector)
    labeled: list[dict[str, Any]] = []
    for row in rows:
        title, gold = row[0], row[1]
        if not isinstance(title, str) or not title.strip():
            continue
        labeled.append({"kind": "labeled", "title": title, "id": (str(gold).strip() or None) if gold is not None else None})
    return labeled
