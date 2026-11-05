"""상품 카탈로그 · 별칭 · 유통경로(직구/병행수입) 규칙 테이블 관리.

    cd backend/AI_TMP
    export AI_PRODUCT_TABLES_DSN=postgresql://user:pw@host:5432/db     # 또는 --dsn

    python -m ai.scripts.catalog_tables init-db                        # 테이블/뷰 만들기 (여러 번 실행해도 안전)
    python -m ai.scripts.catalog_tables import --seed --dry-run        # 가져올 내용 검증만 (DB 는 읽기만)
    python -m ai.scripts.catalog_tables import --seed                  # 시드 카탈로그 + 패키지 초기 별칭/규칙 가져오기
    python -m ai.scripts.catalog_tables import --catalog-json catalog_kc.json     # KC 가져오기 결과도 카탈로그 행으로
    python -m ai.scripts.catalog_tables import --csv-dir reviewed/ --update       # 검수한 CSV 로 덮어쓰기(명시했을 때만)
    python -m ai.scripts.catalog_tables export --out dump/             # DB -> CSV (검수/백업)
    python -m ai.scripts.catalog_tables validate --csv-dir reviewed/   # 파일 검증 (DB 없이)
    python -m ai.scripts.catalog_tables validate                       # DB 검증

가져오기는 기본이 '없는 행만 넣기'라서 DB 에서 사람이 고친 별칭/규칙을 덮어쓰지 않는다. 검증에서 걸린 행은
DB 에 넣지 않고 보고서(issues)에 이유를 적는다. 오류 행이 있으면 종료 코드가 2 다 (나머지 행은 들어간다).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.crawler.identity.catalog import _DEFAULT_PATH as SEED_PATH  # noqa: E402
from ai.crawler.identity.dbio import default_dsn  # noqa: E402
from ai.crawler.identity.tables import pgio  # noqa: E402
from ai.crawler.identity.tables.csvio import read_tables, write_tables  # noqa: E402
from ai.crawler.identity.tables.loader import PACKAGED_DIR  # noqa: E402
from ai.crawler.identity.tables.models import Issue, ProductTables  # noqa: E402
from ai.crawler.identity.tables.overlay import tables_from_catalog_entries  # noqa: E402
from ai.crawler.identity.tables.validate import clean_tables  # noqa: E402


def resolve_dsn(arg: str | None) -> str:
    return arg or os.environ.get("AI_PRODUCT_TABLES_DSN", "").strip() or default_dsn()


def load_input(csv_dir: Path | None, catalog_jsons: list[Path], *, seed: bool) -> tuple[ProductTables, list[Issue]]:
    """가져올 내용: 카탈로그 JSON(시드, KC 결과)을 행으로 옮긴 것 + CSV 디렉터리(기본: 패키지 초기 파일)."""
    tables = ProductTables()
    issues: list[Issue] = []
    entries: list[dict] = []
    if seed:
        entries += json.loads(SEED_PATH.read_text(encoding="utf-8"))["products"]
    for path in catalog_jsons:
        entries += json.loads(Path(path).read_text(encoding="utf-8"))["products"]
    if entries:
        converted = tables_from_catalog_entries(entries)
        tables.catalog += converted.catalog
        tables.aliases += converted.aliases
    csv_tables, csv_issues = read_tables(csv_dir or PACKAGED_DIR)
    issues += csv_issues
    tables.catalog += csv_tables.catalog
    tables.aliases += csv_tables.aliases
    tables.categories += csv_tables.categories
    tables.signals += csv_tables.signals
    return tables, issues


def _print(report: dict) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=1))


def _issues_json(issues: list[Issue]) -> list[dict]:
    return [i.to_dict() for i in issues]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage product catalog / alias / sourcing-rule tables")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("schema", help="DDL 파일 경로를 출력한다")

    init = sub.add_parser("init-db", help="테이블/뷰를 만든다")
    init.add_argument("--dsn")

    imp = sub.add_parser("import", help="CSV/JSON 을 DB 로 가져온다")
    imp.add_argument("--dsn")
    imp.add_argument("--csv-dir", type=Path, help="product_*.csv, sourcing_*.csv 가 든 디렉터리 (기본: 패키지 초기 파일)")
    imp.add_argument("--catalog-json", type=Path, action="append", default=[], help="카탈로그 JSON (시드, kc_import 결과). 여러 번 가능")
    imp.add_argument("--seed", action="store_true", help="패키지의 시드 카탈로그(catalog_seed.json)도 가져온다")
    imp.add_argument("--update", action="store_true", help="이미 있는 행을 덮어쓴다 (사람이 DB 에서 고친 값이 사라진다)")
    imp.add_argument("--dry-run", action="store_true", help="검증과 개수만 보고 쓰지 않는다")

    exp = sub.add_parser("export", help="DB 를 CSV 로 내보낸다")
    exp.add_argument("--dsn")
    exp.add_argument("--out", type=Path, required=True)

    val = sub.add_parser("validate", help="검증만 한다 (--csv-dir 이면 DB 없이)")
    val.add_argument("--dsn")
    val.add_argument("--csv-dir", type=Path)
    val.add_argument("--catalog-json", type=Path, action="append", default=[], help="CSV 별칭이 가리키는 카탈로그 JSON (--csv-dir 일 때)")
    val.add_argument("--seed", action="store_true", help="패키지 시드 카탈로그를 카탈로그로 함께 본다 (--csv-dir 일 때)")

    args = parser.parse_args(argv)

    if args.command == "schema":
        print(pgio.SCHEMA_PATH)
        return 0

    if args.command == "init-db":
        pgio.apply_schema(resolve_dsn(args.dsn))
        print("ok: tables and view are ready")
        return 0

    if args.command == "import":
        tables, parse_issues = load_input(args.csv_dir, args.catalog_json, seed=args.seed)
        report = pgio.write_tables(resolve_dsn(args.dsn), tables, update=args.update, dry_run=args.dry_run)
        issues = [*parse_issues, *report["issues"]]
        _print({**{k: v for k, v in report.items() if k != "issues"}, "offered": tables.counts(), "issues": _issues_json(issues)})
        return 2 if any(i.level == "error" for i in issues) else 0

    if args.command == "export":
        tables = pgio.load_tables(resolve_dsn(args.dsn))
        paths = write_tables(args.out, tables)
        _print({"written": [str(p) for p in paths], "counts": tables.counts()})
        return 0

    # validate
    if args.csv_dir is not None:
        tables, issues = load_input(args.csv_dir, args.catalog_json, seed=args.seed)
    else:
        tables, issues = pgio.load_tables(resolve_dsn(args.dsn)), []
    cleaned, found = clean_tables(tables)
    issues += found
    _print({"counts": tables.counts(), "usable": cleaned.counts(), "issues": _issues_json(issues)})
    return 1 if any(i.level == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
