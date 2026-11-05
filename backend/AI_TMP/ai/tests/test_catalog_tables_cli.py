"""scripts/catalog_tables.py: 종료 코드와 보고서. 서버가 없으면 건너뛴다."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from ..crawler.identity.tables import pgio
from ..crawler.identity.tables.csvio import read_tables, write_tables
from ..crawler.identity.tables.models import AliasRow, CatalogRow, ProductTables, SourcingCategoryRow, SourcingSignalRow
from ..scripts import catalog_tables as cli
from ._pg_fixture import TempPostgres

_server: TempPostgres | None = None


def setUpModule() -> None:
    global _server
    _server = TempPostgres()


def tearDownModule() -> None:
    if _server is not None:
        _server.close()


def run(*args: str) -> tuple[int, dict | str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(list(args))
    text = out.getvalue().strip()
    try:
        return code, json.loads(text)
    except json.JSONDecodeError:
        return code, text


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = _server.new_database()  # type: ignore[union-attr]
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def count(self, table: str) -> int:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def good_dir(self) -> Path:
        write_tables(self.dir, ProductTables(
            [CatalogRow("logi:a", "logitech", "MX A")], [AliasRow("logi:a", "마스터 에이", status="approved")],
            [SourcingCategoryRow("DIRECT", "직구", "N", "N")], [SourcingSignalRow("DIRECT", "keyword", "직구")],
        ))
        return self.dir


class CommandTest(CliCase):
    def test_schema는_DDL_경로를_출력한다(self) -> None:
        code, out = run("schema")

        self.assertEqual(code, 0)
        self.assertTrue(Path(str(out)).exists())
        self.assertTrue(str(out).endswith("product_tables_v1.sql"))

    def test_init_db는_표를_만들고_다시_실행해도_된다(self) -> None:
        self.assertEqual(run("init-db", "--dsn", self.dsn)[0], 0)
        self.assertEqual(run("init-db", "--dsn", self.dsn)[0], 0)
        self.assertEqual(self.count("product_aliases"), 0)

    def test_가져오기_dry_run은_쓰지_않는다(self) -> None:
        run("init-db", "--dsn", self.dsn)

        code, report = run("import", "--dsn", self.dsn, "--csv-dir", str(self.good_dir()), "--dry-run")

        self.assertEqual(code, 0)
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["written"], {"product_catalog": 1, "product_aliases": 1, "sourcing_categories": 1, "sourcing_signals": 1})
        self.assertEqual(self.count("product_catalog"), 0)

    def test_가져오기는_넣고_다시_가져오면_건드리지_않는다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        directory = self.good_dir()

        code, first = run("import", "--dsn", self.dsn, "--csv-dir", str(directory))
        code2, second = run("import", "--dsn", self.dsn, "--csv-dir", str(directory))

        self.assertEqual((code, code2), (0, 0))
        self.assertEqual(sum(first["written"].values()), 4)
        self.assertEqual(sum(second["written"].values()), 0)
        self.assertEqual(sum(second["skipped_existing"].values()), 4)
        self.assertEqual(first["offered"], {"product_catalog": 1, "product_aliases": 1, "sourcing_categories": 1, "sourcing_signals": 1})

    def test_seed_옵션은_시드_카탈로그와_패키지_초기_파일을_함께_가져온다(self) -> None:
        run("init-db", "--dsn", self.dsn)

        code, report = run("import", "--dsn", self.dsn, "--seed")

        self.assertEqual(code, 0, report)
        self.assertEqual(report["written"]["product_catalog"], 39)
        self.assertEqual(self.count("sourcing_signals"), 24)
        self.assertGreater(self.count("product_aliases"), 40)

    def test_카탈로그_JSON을_행으로_옮겨_가져온다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        path = self.dir / "kc.json"
        path.write_text(json.dumps({"products": [
            {"id": "kc:samsung:smr510", "brand": "samsung", "model": "SM-R510", "category": "무선이어폰", "aliases": ["SM-R511"],
             "verified": True, "source": "kc", "kc": {"management_numbers": ["R-1"], "manufacturers": ["Samsung"]}},
        ]}), encoding="utf-8")
        empty = self.dir / "empty"
        empty.mkdir()

        code, report = run("import", "--dsn", self.dsn, "--catalog-json", str(path), "--csv-dir", str(empty))

        self.assertEqual(code, 0, report)
        loaded = pgio.load_tables(self.dsn)
        self.assertEqual([(r.catalog_id, r.kc_certified_yn, r.source) for r in loaded.catalog], [("kc:samsung:smr510", "Y", "kc")])
        self.assertEqual([(a.alias_text, a.alias_type, a.status) for a in loaded.aliases], [("SM-R511", "kc_derived", "approved")])

    def test_오류_행이_있으면_종료_코드_2이고_나머지는_들어간다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        directory = self.good_dir()
        with (directory / "product_aliases.csv").open("a", encoding="utf-8", newline="") as handle:
            handle.write("ghost,유령 이름,model,other,N,approved,curated,,\n")

        code, report = run("import", "--dsn", self.dsn, "--csv-dir", str(directory))

        self.assertEqual(code, 2)
        self.assertEqual([i["code"] for i in report["issues"]], ["ALIAS_ORPHAN"])
        self.assertEqual(self.count("product_aliases"), 1)

    def test_CSV_형식_오류도_종료_코드_2로_알린다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        directory = self.good_dir()
        (directory / "sourcing_signals.csv").write_text("category_code,match_type,pattern,priority\nDIRECT,keyword,직구,abc\n", encoding="utf-8")

        code, report = run("import", "--dsn", self.dsn, "--csv-dir", str(directory))

        self.assertEqual(code, 2)
        self.assertEqual([i["code"] for i in report["issues"]], ["CSV_BAD_ROW"])

    def test_update는_이미_있는_행을_덮어쓴다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        directory = self.good_dir()
        run("import", "--dsn", self.dsn, "--csv-dir", str(directory))
        write_tables(directory, ProductTables([], [], [SourcingCategoryRow("DIRECT", "직구(수정)", "N", "Y", "Y")], []), only=["categories"])

        code, report = run("import", "--dsn", self.dsn, "--csv-dir", str(directory), "--update")

        self.assertEqual(code, 0, report)
        self.assertEqual(pgio.load_tables(self.dsn).categories[0].label_ko, "직구(수정)")

    def test_내보내기는_DB를_CSV로_쓰고_다시_읽으면_같다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        run("import", "--dsn", self.dsn, "--csv-dir", str(self.good_dir()))
        out = self.dir / "dump"

        code, report = run("export", "--dsn", self.dsn, "--out", str(out))

        self.assertEqual(code, 0)
        self.assertEqual(report["counts"], {"product_catalog": 1, "product_aliases": 1, "sourcing_categories": 1, "sourcing_signals": 1})
        exported, issues = read_tables(out)
        self.assertEqual((issues, exported.counts()), ([], report["counts"]))
        self.assertEqual(exported.aliases, pgio.load_tables(self.dsn).aliases)

    def test_validate는_파일을_DB_없이_검사하고_오류가_있으면_종료_코드_1이다(self) -> None:
        directory = self.good_dir()

        self.assertEqual(run("validate", "--csv-dir", str(directory))[0], 0)

        with (directory / "product_aliases.csv").open("a", encoding="utf-8", newline="") as handle:
            handle.write("ghost,유령 이름,model,other,N,approved,curated,,\n")
        code, report = run("validate", "--csv-dir", str(directory))

        self.assertEqual(code, 1)
        self.assertEqual(report["counts"]["product_aliases"], 2)
        self.assertEqual(report["usable"]["product_aliases"], 1)

    def test_validate_는_시드_카탈로그를_함께_보면_초기_별칭이_고아가_아니다(self) -> None:
        self.assertEqual(run("validate", "--csv-dir", str(cli.PACKAGED_DIR))[0], 1)  # 카탈로그 없이는 고아
        code, report = run("validate", "--csv-dir", str(cli.PACKAGED_DIR), "--seed")

        self.assertEqual(code, 0, report)
        self.assertEqual([i for i in report["issues"] if i["level"] == "error"], [])

    def test_validate는_DB도_검사한다(self) -> None:
        run("init-db", "--dsn", self.dsn)
        run("import", "--dsn", self.dsn, "--csv-dir", str(self.good_dir()))

        code, report = run("validate", "--dsn", self.dsn)

        self.assertEqual(code, 0)
        self.assertEqual(report["usable"], report["counts"])

    def test_dsn은_인자가_환경변수보다_우선한다(self) -> None:
        from unittest.mock import patch

        with patch.dict("os.environ", {"AI_PRODUCT_TABLES_DSN": "postgresql://env"}):
            self.assertEqual(cli.resolve_dsn("postgresql://arg"), "postgresql://arg")
            self.assertEqual(cli.resolve_dsn(None), "postgresql://env")
        with patch.dict("os.environ", {"AI_PRODUCT_TABLES_DSN": "", "AI_POSTGRES_DSN": "postgresql://crawl"}):
            self.assertEqual(cli.resolve_dsn(None), "postgresql://crawl")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
