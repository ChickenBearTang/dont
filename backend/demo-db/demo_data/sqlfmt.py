"""파이썬 값을 SQL 리터럴로 바꾸는 최소 도구. 시드를 .sql 파일로 내보낼 때만 쓴다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Raw:
    """그대로 SQL 에 넣는 조각 (서브쿼리 등). 사용자 입력을 넣는 데 쓰지 않는다."""

    sql: str


def quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def lit(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Raw):
        return value.sql
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise TypeError("돈은 정수(원)로 넘긴다: float 리터럴은 쓰지 않는다")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return f"TIMESTAMP '{value.isoformat(sep=' ', timespec='seconds')}'"
        return f"TIMESTAMPTZ '{value.isoformat(sep=' ', timespec='seconds')}'"
    if isinstance(value, date):
        return f"DATE '{value.isoformat()}'"
    if isinstance(value, str):
        return quote(value)
    raise TypeError(f"SQL 리터럴로 바꿀 수 없는 값: {type(value).__name__}")


def values_list(rows: Iterable[Sequence[object]]) -> str:
    return ",\n".join("    (" + ", ".join(lit(v) for v in row) + ")" for row in rows)


def chunks(rows: Sequence[Sequence[object]], size: int = 400) -> Iterable[Sequence[Sequence[object]]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def insert_rows(
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[object]],
    suffix: str = "",
) -> str:
    """단순 INSERT ... VALUES (값에 Raw 서브쿼리를 넣을 수 있다). suffix 는 ON CONFLICT 같은 꼬리."""
    cols = ", ".join(columns)
    tail = f"\n{suffix}" if suffix else ""
    out = []
    for part in chunks(rows):
        out.append(f"INSERT INTO {table} ({cols}) VALUES\n{values_list(part)}{tail};")
    return "\n".join(out)
