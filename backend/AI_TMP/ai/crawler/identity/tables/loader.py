"""기본 테이블 읽기: 어디서 읽을지는 환경변수로 정한다 (하나만 쓴다).

    AI_PRODUCT_TABLES_DSN   PostgreSQL 에서 읽는다 (예: postgresql://user:pw@host:5432/db)
    AI_PRODUCT_TABLES_DIR   CSV 파일 4개가 든 디렉터리에서 읽는다 (product_catalog.csv ...)
    (둘 다 없으면)           패키지에 든 초기 파일(data/tables)을 쓴다

DB 가 지정되면 DB 가 기준이다. 패키지의 초기 파일은 DB 에 한 번 가져와서(scripts/catalog_tables.py import) 쓰고,
둘을 겹쳐 쓰지 않는다. 읽는 데 실패하면(DB 연결 불가 등) 조용히 비어 있는 채로 넘어가지 않고 예외를 낸다.
"""

from __future__ import annotations

import os
from pathlib import Path

from .csvio import read_tables
from .models import Issue, ProductTables
from .pgio import load_tables as load_pg_tables

PACKAGED_DIR = Path(__file__).resolve().parents[1] / "data" / "tables"


def load_default_tables() -> tuple[ProductTables, list[Issue], str]:
    """(테이블, 읽다가 걸린 문제, 출처 설명)"""
    dsn = os.getenv("AI_PRODUCT_TABLES_DSN", "").strip()
    if dsn:
        return load_pg_tables(dsn), [], "postgres"
    directory = os.getenv("AI_PRODUCT_TABLES_DIR", "").strip()
    if directory:
        tables, issues = read_tables(Path(directory))
        return tables, issues, f"csv:{directory}"
    tables, issues = read_tables(PACKAGED_DIR)
    return tables, issues, "packaged"
