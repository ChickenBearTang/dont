from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Iterator
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from config import get_env


@dataclass(frozen=True)
class DbUserProfile:
    user_id: str
    name: str
    monthly_income: int


def _parse_postgres_dsn() -> str:
    jdbc_url = get_env("DB_URL")
    if not jdbc_url:
        raise ValueError("DB_URL is not configured")

    raw_url = jdbc_url.removeprefix("jdbc:")
    parsed = urlparse(raw_url)
    if parsed.scheme != "postgresql":
        raise ValueError(f"Unsupported DB_URL scheme: {parsed.scheme}")

    user = get_env("DB_USERNAME")
    password = get_env("DB_PASSWORD")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(_parse_postgres_dsn(), row_factory=dict_row)
    try:
        yield connection
    finally:
        connection.close()


def _month_bounds(report_month: str) -> tuple[date, date]:
    value = report_month.strip()
    if len(value) == 7:
        month_start = datetime.strptime(value, "%Y-%m").date().replace(day=1)
    elif len(value) == 10:
        month_start = datetime.strptime(value, "%Y-%m-%d").date().replace(day=1)
    else:
        raise ValueError(f"Invalid report_month format: {report_month}")
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1)
    return month_start, month_end


def _date_bounds(start_date: str, end_date: str) -> tuple[date, date]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    return start, end


def _parse_date(raw: str) -> date:
    value = raw.strip()
    if "-" in value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.strptime(value, "%Y%m%d").date()


def _normalize_amount(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return int(value)
    return int(value)


def _normalize_time(value: Any) -> str:
    if value is None:
        return "000000"
    if isinstance(value, time):
        return value.strftime("%H%M%S")

    text = str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.ljust(6, "0")[:6] if digits else "000000"


def _combine_datetime(day: date, raw_time: Any) -> datetime:
    return datetime.strptime(f"{day.strftime('%Y%m%d')}{_normalize_time(raw_time)}", "%Y%m%d%H%M%S")


def _estimate_monthly_income(connection: psycopg.Connection, user_id: int, month_start: date, month_end: date) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select coalesce(sum(at.transaction_amount), 0) as income
            from account_transactions at
            join accounts a on a.id = at.account_id
            where a.user_id = %s
              and at.transaction_type = '1'
              and at.transaction_date >= %s
              and at.transaction_date < %s
            """,
            (user_id, month_start, month_end),
        )
        row = cursor.fetchone() or {}
        current_month_income = _normalize_amount(row.get("income"))
        if current_month_income > 0:
            return current_month_income

        cursor.execute(
            """
            select coalesce(avg(month_total), 0) as avg_income
            from (
                select date_trunc('month', at.transaction_date)::date as month_key,
                       sum(at.transaction_amount) as month_total
                from account_transactions at
                join accounts a on a.id = at.account_id
                where a.user_id = %s
                  and at.transaction_type = '1'
                  and at.transaction_date >= (%s - interval '3 month')
                  and at.transaction_date < %s
                group by month_key
            ) monthly_income
            """,
            (user_id, month_start, month_end),
        )
        fallback_row = cursor.fetchone() or {}
        average_income = _normalize_amount(fallback_row.get("avg_income"))
        return average_income if average_income > 0 else 1_000_000


def fetch_user_profile(connection: psycopg.Connection, user_id: int, report_month: str) -> DbUserProfile:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select id, name
            from users
            where id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"User not found: {user_id}")

    month_start, month_end = _month_bounds(report_month)
    return DbUserProfile(
        user_id=str(row["id"]),
        name=str(row["name"]),
        monthly_income=_estimate_monthly_income(connection, user_id, month_start, month_end),
    )


def fetch_card_transactions(connection: psycopg.Connection, user_id: int, report_month: str) -> list[dict[str, Any]]:
    month_start, month_end = _month_bounds(report_month)
    return fetch_card_transactions_between(connection, user_id, month_start, month_end)


def fetch_card_transactions_between(
    connection: psycopg.Connection, user_id: int, start_date: date, end_exclusive: date
) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select id,
                   transaction_date,
                   transaction_time,
                   merchant_name,
                   category_name,
                   transaction_amount,
                   transaction_type,
                   approval_no,
                   description
            from card_transactions
            where user_id = %s
              and transaction_date >= %s
              and transaction_date < %s
            order by transaction_date asc, transaction_time asc, id asc
            """,
            (user_id, start_date, end_exclusive),
        )
        rows = cursor.fetchall()

    transactions: list[dict[str, Any]] = []
    for row in rows:
        approved_at = _combine_datetime(row["transaction_date"], row["transaction_time"])
        transactions.append(
            {
                "transaction_id": str(row["approval_no"] or row["id"]),
                "user_id": str(user_id),
                "approved_at": approved_at,
                "merchant_name": row["merchant_name"] or "Unknown",
                "amount": _normalize_amount(row["transaction_amount"]),
                "category": row["category_name"] or "기타",
                "subcategory": row["description"] or row["category_name"] or "기타",
                "payment_method": "card",
                "status": row["transaction_type"] or "approved",
                "is_recurring": False,
            }
        )
    return transactions


def _account_category(summary: str | None, memo: str | None) -> str:
    combined = f"{summary or ''} {memo or ''}"
    return "card_bill" if "카드" in combined and "대금" in combined else "general"


def fetch_account_transactions(connection: psycopg.Connection, user_id: int, report_month: str) -> list[dict[str, Any]]:
    month_start, month_end = _month_bounds(report_month)
    return fetch_account_transactions_between(connection, user_id, month_start, month_end)


def fetch_account_transactions_between(
    connection: psycopg.Connection, user_id: int, start_date: date, end_exclusive: date
) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select at.id,
                   at.transaction_date,
                   at.transaction_time,
                   at.transaction_type,
                   at.transaction_summary,
                   at.transaction_memo,
                   at.transaction_amount,
                   at.after_balance
            from account_transactions at
            join accounts a on a.id = at.account_id
            where a.user_id = %s
              and at.transaction_date >= %s
              and at.transaction_date < %s
            order by at.transaction_date asc, at.transaction_time asc, at.id asc
            """,
            (user_id, start_date, end_exclusive),
        )
        rows = cursor.fetchall()

    transactions: list[dict[str, Any]] = []
    for row in rows:
        transacted_at = _combine_datetime(row["transaction_date"], row["transaction_time"])
        summary = row["transaction_summary"] or "Unknown"
        memo = row["transaction_memo"] or "general"
        transactions.append(
            {
                "transaction_id": str(row["id"]),
                "user_id": str(user_id),
                "transacted_at": transacted_at,
                "transaction_type": "in" if str(row["transaction_type"]) == "1" else "out",
                "counterparty": summary,
                "amount": _normalize_amount(row["transaction_amount"]),
                "category": _account_category(summary, memo),
                "subcategory": memo,
                "balance_after": _normalize_amount(row["after_balance"]),
            }
        )
    return transactions


def fetch_valid_justifications(
    connection: psycopg.Connection, user_id: int, report_month: str
) -> list[dict[str, Any]]:
    month_start, _ = _month_bounds(report_month)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select id, user_message, ai_response, created_at
            from fin_consumption_justification
            where user_id = %s
              and target_month = %s
              and is_valid = true
            order by created_at asc
            """,
            (user_id, month_start),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "message": row["user_message"],
            "aiResponse": row["ai_response"],
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def fetch_justification_history(
    connection: psycopg.Connection, user_id: int, report_month: str
) -> list[dict[str, str]]:
    month_start, _ = _month_bounds(report_month)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select user_message, ai_response
            from fin_consumption_justification
            where user_id = %s
              and target_month = %s
            order by created_at asc
            """,
            (user_id, month_start),
        )
        rows = cursor.fetchall()

    history: list[dict[str, str]] = []
    for row in rows:
        history.append({"role": "user", "message": row["user_message"]})
        history.append({"role": "assistant", "message": row["ai_response"]})
    return history


def build_date_range(connection: psycopg.Connection, user_id: int, start_date: str, end_date: str) -> tuple[DbUserProfile, list[dict[str, Any]], list[dict[str, Any]]]:
    start, end = _date_bounds(start_date, end_date)
    end_exclusive = end + timedelta(days=1)
    reference_month = start.strftime("%Y-%m")
    profile = fetch_user_profile(connection, user_id, reference_month)
    cards = fetch_card_transactions_between(connection, user_id, start, end_exclusive)
    accounts = fetch_account_transactions_between(connection, user_id, start, end_exclusive)
    return profile, cards, accounts
