"""PostgreSQL 에서 상품 테이블: DDL 제약, 적재, 읽기, 식별기 연결. 서버가 없으면 건너뛴다."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ..crawler.identity import ProductResolver
from ..crawler.identity.tables import pgio
from ..crawler.identity.tables.csvio import read_tables
from ..crawler.identity.tables.loader import PACKAGED_DIR, load_default_tables
from ..crawler.identity.tables.models import (
    AliasRow,
    CatalogRow,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
)
from ._pg_fixture import TempPostgres

_server: TempPostgres | None = None


def setUpModule() -> None:
    global _server
    _server = TempPostgres()  # 없으면 SkipTest


def tearDownModule() -> None:
    if _server is not None:
        _server.close()


def A(cid, text, **kw):
    kw.setdefault("status", "approved")
    return AliasRow(cid, text, **kw)


def sample() -> ProductTables:
    return ProductTables(
        [
            CatalogRow("kc:logi:yr0087", "logitech", "YR0087", display_name="Logitech MX Master 3S", product_line="MX Master",
                       category="mouse", manufacturer="Logitech Europe S.A.", kc_certified_yn="Y",
                       kc_info={"management_numbers": ["R-R-LGE-1"], "countries": ["중국"]}, source="kc", verified_yn="Y",
                       compatible_brands=("asus",), benign_suffixes=("블랙",)),
            CatalogRow("import:acme", "acme", "ACME X1", kc_certified_yn="N", source="import_only"),
        ],
        [A("kc:logi:yr0087", "MX Master S3", alias_type="misspelling", note="뒤집힌 표기"),
         A("kc:logi:yr0087", "엠엑스 마스터", alias_kind="line", alias_type="korean"),
         A("import:acme", "아크미 엑스원", status="pending", source="crawl_suggested")],
        [SourcingCategoryRow("DIRECT", "해외직구", "N", "N", "N", 30, "메모"), SourcingCategoryRow("OFFICIAL", "정식수입", "Y", "Y", "Y", 10)],
        [SourcingSignalRow("DIRECT", "domain", "aliexpress.com", 10), SourcingSignalRow("DIRECT", "keyword", "직구", 50, "N", "꺼둠"),
         SourcingSignalRow("OFFICIAL", "keyword", "정발", 50)],
    )


class PgCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = _server.new_database()  # type: ignore[union-attr]
        pgio.apply_schema(self.dsn)

    def query(self, sql, params=None):
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            return connection.execute(sql, params).fetchall()

    def execute(self, sql, params=None):
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            connection.execute(sql, params)


class SchemaTest(PgCase):
    def test_표와_뷰가_만들어지고_다시_실행해도_안전하다(self) -> None:
        pgio.apply_schema(self.dsn)
        pgio.apply_schema(self.dsn)

        tables = {r[0] for r in self.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")}
        self.assertEqual(
            tables, {"product_catalog", "product_aliases", "sourcing_categories", "sourcing_signals", "v_product_alias_conflicts"},
        )

    def test_YN_열은_허용된_값만_받는다(self) -> None:
        import psycopg

        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M', 'm')")
        bad = [
            ("UPDATE product_catalog SET kc_certified_yn = 'X'", None),
            ("UPDATE product_catalog SET verified_yn = 'U'", None),  # 검수 여부는 Y/N 만
            ("UPDATE product_catalog SET source = 'web'", None),
            ("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, status) VALUES ('a', 'x y', 'xy', 'ok')", None),
            ("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, alias_kind) VALUES ('a', 'x y', 'xy', 'both')", None),
            ("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, brand_required_yn) VALUES ('a', 'x y', 'xy', 'U')", None),
            ("INSERT INTO sourcing_categories (category_code, label_ko, kc_record_expected_yn, price_pool_yn) VALUES ('C', 'c', 'Y', 'U')", None),
            ("INSERT INTO sourcing_categories (category_code, label_ko, kc_record_expected_yn, price_pool_yn) VALUES ('C', 'c', 'Q', 'Y')", None),
        ]
        for sql, params in bad:
            with self.assertRaises(psycopg.errors.CheckViolation, msg=sql):
                self.execute(sql, params)

    def test_인증_기록_기대와_인증_여부는_모름_U를_받는다(self) -> None:
        self.execute("INSERT INTO sourcing_categories (category_code, label_ko, kc_record_expected_yn, price_pool_yn) VALUES ('C', 'c', 'U', 'N')")
        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm, kc_certified_yn) VALUES ('a', 'b', 'M', 'm', 'U')")

    def test_고아_별칭과_고아_신호는_외래키로_막는다(self) -> None:
        import psycopg

        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('none', 'x y', 'xy')")
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.execute("INSERT INTO sourcing_signals (category_code, match_type, pattern, pattern_norm) VALUES ('none', 'keyword', '직구', '직구')")

    def test_상품을_지우면_그_별칭도_지워진다(self) -> None:
        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M', 'm')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('a', 'x y', 'xy')")

        self.execute("DELETE FROM product_catalog WHERE catalog_id = 'a'")

        self.assertEqual(self.query("SELECT COUNT(*) FROM product_aliases")[0][0], 0)

    def test_상품_id를_바꾸면_별칭이_따라간다(self) -> None:
        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M', 'm')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('a', 'x y', 'xy')")

        self.execute("UPDATE product_catalog SET catalog_id = 'a2' WHERE catalog_id = 'a'")

        self.assertEqual(self.query("SELECT catalog_id FROM product_aliases"), [("a2",)])

    def test_유일성_제약(self) -> None:
        import psycopg

        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M-1', 'm1')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('a', 'x y', 'xy')")
        self.execute("INSERT INTO sourcing_categories (category_code, label_ko, kc_record_expected_yn, price_pool_yn) VALUES ('C', 'c', 'Y', 'Y')")
        self.execute("INSERT INTO sourcing_signals (category_code, match_type, pattern, pattern_norm) VALUES ('C', 'keyword', '직구', '직구')")
        for sql in (
            "INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'x', 'Q', 'q')",  # id
            "INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a2', 'b', 'M 1', 'm1')",  # 브랜드+모델
            "INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('a', 'X-Y', 'xy')",  # 같은 상품의 같은 이름
            "INSERT INTO sourcing_signals (category_code, match_type, pattern, pattern_norm) VALUES ('C', 'keyword', '직 구', '직구')",
        ):
            with self.assertRaises(psycopg.errors.UniqueViolation, msg=sql):
                self.execute(sql)

    def test_같은_이름의_다른_종류는_허용한다(self) -> None:
        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M', 'm')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, alias_kind) VALUES ('a', 'x y', 'xy', 'model')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, alias_kind) VALUES ('a', 'x y', 'xy', 'line')")

    def test_새_별칭은_승인_전_상태로_들어간다(self) -> None:
        self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES ('a', 'b', 'M', 'm')")
        self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm) VALUES ('a', 'x y', 'xy')")

        self.assertEqual(self.query("SELECT status, alias_kind, alias_type, brand_required_yn FROM product_aliases"),
                         [("pending", "model", "other", "N")])

    def test_충돌_뷰는_승인된_정확한_이름의_충돌만_보여준다(self) -> None:
        for cid, brand in (("a", "x"), ("b", "y"), ("c", "z")):
            self.execute("INSERT INTO product_catalog (catalog_id, brand, model_code, model_code_norm) VALUES (%s, %s, %s, %s)", (cid, brand, cid, cid))
        rows = [
            ("a", "same", "model", "approved"), ("b", "same", "model", "approved"),   # 충돌
            ("a", "pend", "model", "approved"), ("b", "pend", "model", "pending"),    # 승인 전이라 아님
            ("a", "fam", "line", "approved"), ("b", "fam", "line", "approved"),       # 제품군은 여러 상품에 걸쳐도 됨
            ("a", "solo", "model", "approved"), ("c", "other", "model", "approved"),
        ]
        for cid, norm, kind, status in rows:
            self.execute("INSERT INTO product_aliases (catalog_id, alias_text, alias_norm, alias_kind, status) VALUES (%s, %s, %s, %s, %s)", (cid, norm + " x", norm, kind, status))

        self.assertEqual(self.query("SELECT alias_norm, products, catalog_ids FROM v_product_alias_conflicts"), [("same", 2, ["a", "b"])])


class WriteLoadTest(PgCase):
    def test_쓰고_읽으면_같다(self) -> None:
        original = sample()

        report = pgio.write_tables(self.dsn, original)
        loaded = pgio.load_tables(self.dsn)

        self.assertEqual(report["written"], {"product_catalog": 2, "product_aliases": 3, "sourcing_categories": 2, "sourcing_signals": 3})
        self.assertEqual(report["skipped_existing"], {"product_catalog": 0, "product_aliases": 0, "sourcing_categories": 0, "sourcing_signals": 0})
        self.assertEqual(report["issues"], [])
        key = lambda r: tuple(str(v) for v in vars(r).values())  # noqa: E731
        self.assertEqual(sorted(loaded.catalog, key=key), sorted(original.catalog, key=key))
        self.assertEqual(sorted(loaded.aliases, key=key), sorted(original.aliases, key=key))
        self.assertEqual(sorted(loaded.categories, key=key), sorted(original.categories, key=key))
        self.assertEqual(sorted(loaded.signals, key=key), sorted(original.signals, key=key))

    def test_JSON_열의_한글과_목록이_그대로_돌아온다(self) -> None:
        pgio.write_tables(self.dsn, sample())

        row = next(r for r in pgio.load_tables(self.dsn).catalog if r.catalog_id == "kc:logi:yr0087")

        self.assertEqual(row.kc_info, {"management_numbers": ["R-R-LGE-1"], "countries": ["중국"]})
        self.assertEqual((row.compatible_brands, row.benign_suffixes), (("asus",), ("블랙",)))

    def test_비교용_값은_파이썬과_같은_규칙으로_저장한다(self) -> None:
        pgio.write_tables(self.dsn, sample())

        self.assertEqual(self.query("SELECT model_code_norm FROM product_catalog WHERE catalog_id = 'import:acme'"), [("acmex1",)])
        self.assertIn(("mxmasters3",), self.query("SELECT alias_norm FROM product_aliases"))
        self.assertIn(("직구",), self.query("SELECT pattern_norm FROM sourcing_signals"))

    def test_다시_가져와도_이미_있는_행은_건드리지_않는다(self) -> None:
        pgio.write_tables(self.dsn, sample())
        # 사람이 DB 에서 고친 값
        self.execute("UPDATE product_aliases SET status = 'rejected', reviewed_by = 'kim' WHERE alias_norm = 'mxmasters3'")
        self.execute("UPDATE sourcing_categories SET reviewed_yn = 'Y', price_pool_yn = 'Y' WHERE category_code = 'DIRECT'")
        self.execute("UPDATE product_catalog SET display_name = '손으로 고친 이름' WHERE catalog_id = 'import:acme'")

        report = pgio.write_tables(self.dsn, sample())

        self.assertEqual(report["written"], {"product_catalog": 0, "product_aliases": 0, "sourcing_categories": 0, "sourcing_signals": 0})
        self.assertEqual(report["skipped_existing"], {"product_catalog": 2, "product_aliases": 3, "sourcing_categories": 2, "sourcing_signals": 3})
        self.assertEqual(self.query("SELECT status, reviewed_by FROM product_aliases WHERE alias_norm = 'mxmasters3'"), [("rejected", "kim")])
        self.assertEqual(self.query("SELECT reviewed_yn, price_pool_yn FROM sourcing_categories WHERE category_code = 'DIRECT'"), [("Y", "Y")])
        self.assertEqual(self.query("SELECT display_name FROM product_catalog WHERE catalog_id = 'import:acme'"), [("손으로 고친 이름",)])

    def test_새_행만_추가된다(self) -> None:
        pgio.write_tables(self.dsn, sample())
        more = sample()
        more.aliases.append(A("kc:logi:yr0087", "마스터 쓰리에스"))

        report = pgio.write_tables(self.dsn, more)

        self.assertEqual(report["written"]["product_aliases"], 1)
        self.assertEqual(self.query("SELECT COUNT(*) FROM product_aliases")[0][0], 4)

    def test_update를_명시하면_덮어쓴다(self) -> None:
        pgio.write_tables(self.dsn, sample())
        changed = sample()
        changed.aliases[0] = A("kc:logi:yr0087", "MX Master S3", alias_type="colloquial", status="rejected")
        changed.categories[0] = SourcingCategoryRow("DIRECT", "해외직구(수정)", "N", "Y", "Y", 31, "바뀜")
        changed.catalog[1] = CatalogRow("import:acme", "acme", "ACME X1", display_name="바뀐 이름", kc_certified_yn="N", source="import_only")

        report = pgio.write_tables(self.dsn, changed, update=True)

        self.assertEqual(report["written"]["product_aliases"], 3)  # 새로 넣은 것과 고쳐 쓴 것을 합친 수
        self.assertEqual(self.query("SELECT alias_type, status FROM product_aliases WHERE alias_norm = 'mxmasters3'"), [("colloquial", "rejected")])
        self.assertEqual(self.query("SELECT label_ko, price_pool_yn, reviewed_yn FROM sourcing_categories WHERE category_code = 'DIRECT'"), [("해외직구(수정)", "Y", "Y")])
        self.assertEqual(self.query("SELECT display_name FROM product_catalog WHERE catalog_id = 'import:acme'"), [("바뀐 이름",)])

    def test_update로_이미_승인된_별칭의_종류와_메모를_고칠_수_있다(self) -> None:
        """승인 상태를 유지한 채 고치는 경우. 이미 DB 에 있는 별칭이라는 이유로 갱신이 버려지면 안 된다."""
        pgio.write_tables(self.dsn, sample())
        changed = sample()
        changed.aliases[0] = A("kc:logi:yr0087", "MX Master S3", alias_type="colloquial", note="바뀐 메모", brand_required_yn="Y")

        report = pgio.write_tables(self.dsn, changed, update=True)

        self.assertEqual([i for i in report["issues"] if i.level == "error"], [])
        self.assertEqual(self.query("SELECT alias_type, note, brand_required_yn, status FROM product_aliases WHERE alias_norm = 'mxmasters3'"),
                         [("colloquial", "바뀐 메모", "Y", "approved")])

    def test_다시_가져오면_이미_있는_별칭은_경고_없이_이미_있음으로_센다(self) -> None:
        pgio.write_tables(self.dsn, sample())

        report = pgio.write_tables(self.dsn, sample())

        self.assertEqual(report["issues"], [])
        self.assertEqual(report["skipped_existing"]["product_aliases"], 3)

    def test_dry_run은_쓰지_않고_같은_개수를_알려준다(self) -> None:
        planned = pgio.write_tables(self.dsn, sample(), dry_run=True)
        self.assertEqual(self.query("SELECT COUNT(*) FROM product_catalog")[0][0], 0)

        real = pgio.write_tables(self.dsn, sample())

        self.assertTrue(planned["dry_run"])
        self.assertEqual(planned["written"], real["written"])
        again = pgio.write_tables(self.dsn, sample(), dry_run=True)
        self.assertEqual(again["written"], {"product_catalog": 0, "product_aliases": 0, "sourcing_categories": 0, "sourcing_signals": 0})
        self.assertEqual(again["skipped_existing"]["product_catalog"], 2)
        updating = pgio.write_tables(self.dsn, sample(), dry_run=True, update=True)
        self.assertEqual(updating["written"]["product_catalog"], 2)

    def test_검증에_걸린_행은_DB에_들어가지_않고_알려진다(self) -> None:
        tables = sample()
        tables.aliases += [A("ghost", "유령 이름"), A("kc:logi:yr0087", "3s")]  # 고아, 너무 짧음
        tables.signals.append(SourcingSignalRow("DIRECT", "domain", "https://bad.com/x"))

        report = pgio.write_tables(self.dsn, tables)

        self.assertEqual(sorted(i.code for i in report["issues"]), ["ALIAS_ORPHAN", "ALIAS_TOO_GENERIC", "SIGNAL_BAD_DOMAIN"])
        self.assertEqual(report["written"]["product_aliases"], 3)
        self.assertEqual(self.query("SELECT COUNT(*) FROM sourcing_signals")[0][0], 3)

    def test_DB에_이미_있는_상품과_표기를_기준으로_검증한다(self) -> None:
        pgio.write_tables(self.dsn, sample())
        later = ProductTables(
            [CatalogRow("kc:other:z1", "other", "Z1")],
            [A("import:acme", "MX Master S3"),          # 다른 상품이 이미 쓰는 이름
             A("kc:other:z1", "YR0087"),                # 다른 상품의 모델 코드
             A("import:acme", "아크미 신제품"),          # 이미 있는 상품(다른 가져오기)에 새 별칭: 허용
             A("kc:ghost:x", "유령 상품 이름")],         # 어디에도 없는 상품
        )

        report = pgio.write_tables(self.dsn, later)

        self.assertEqual(sorted((i.code, i.key) for i in report["issues"]), [
            ("ALIAS_CONFLICT", "import:acme / MX Master S3"), ("ALIAS_CONFLICT", "kc:other:z1 / YR0087"),
            ("ALIAS_ORPHAN", "kc:ghost:x / 유령 상품 이름"),
        ])
        self.assertEqual(report["written"], {"product_catalog": 1, "product_aliases": 1, "sourcing_categories": 0, "sourcing_signals": 0})

    def test_DB의_승인_전_별칭과_제품군_이름은_이름을_선점하지_않는다(self) -> None:
        pgio.write_tables(self.dsn, ProductTables(
            [CatalogRow("a", "x", "A1"), CatalogRow("b", "y", "B1")],
            [A("a", "후보 이름", status="pending"), A("a", "제품군 이름", alias_kind="line")],
        ))

        report = pgio.write_tables(self.dsn, ProductTables([], [A("b", "후보 이름"), A("b", "제품군 이름")]))

        self.assertEqual(report["issues"], [])
        self.assertEqual(report["written"]["product_aliases"], 2)

    def test_DB의_승인된_정확한_이름은_다른_상품이_쓸_수_없다(self) -> None:
        pgio.write_tables(self.dsn, ProductTables([CatalogRow("a", "x", "A1"), CatalogRow("b", "y", "B1")], [A("a", "공용 이름")]))

        report = pgio.write_tables(self.dsn, ProductTables([], [A("b", "공용 이름")]))

        self.assertEqual([i.code for i in report["issues"]], ["ALIAS_CONFLICT"])
        self.assertEqual(report["written"]["product_aliases"], 0)

    def test_가져오기_도중_실패하면_아무것도_바뀌지_않는다(self) -> None:
        import psycopg

        pgio.write_tables(self.dsn, ProductTables([CatalogRow("old", "logitech", "X1")]))
        # 검증은 DB 의 브랜드+모델 중복을 모르므로 DB 제약이 마지막으로 막는다. update=True 에서는 예외가 된다.
        batch = ProductTables([CatalogRow("new:ok", "acme", "A1"), CatalogRow("new:dup", "logitech", "x-1")])

        with self.assertRaises(psycopg.errors.UniqueViolation):
            pgio.write_tables(self.dsn, batch, update=True)

        self.assertEqual(self.query("SELECT catalog_id FROM product_catalog ORDER BY 1"), [("old",)])

    def test_빈_표를_가져와도_된다(self) -> None:
        report = pgio.write_tables(self.dsn, ProductTables())

        self.assertEqual(sum(report["written"].values()), 0)


class EndToEndTest(PgCase):
    def test_시드와_패키지_초기_파일을_DB에_넣고_DB에서_식별한다(self) -> None:
        import json

        from ..crawler.identity.catalog import _DEFAULT_PATH
        from ..crawler.identity.tables.overlay import tables_from_catalog_entries

        packaged, parse_issues = read_tables(PACKAGED_DIR)
        self.assertEqual(parse_issues, [])
        seed = tables_from_catalog_entries(json.loads(_DEFAULT_PATH.read_text(encoding="utf-8"))["products"])
        everything = ProductTables(seed.catalog, [*seed.aliases, *packaged.aliases], packaged.categories, packaged.signals)

        report = pgio.write_tables(self.dsn, everything)

        self.assertEqual([i for i in report["issues"] if i.level == "error"], [])
        # 'rtx4090' 처럼 모델 코드와 같거나, '에어팟 프로 2'/'에어팟프로2' 처럼 비교값이 같은 인라인 별칭은 하나만 남는다
        redundant = [i for i in report["issues"] if i.code in ("ALIAS_SAME_AS_MODEL", "ALIAS_DUPLICATE")]
        self.assertGreater(len(redundant), 0)
        self.assertEqual(report["written"]["product_catalog"], len(seed.catalog))
        self.assertEqual(report["written"]["product_aliases"], len(everything.aliases) - len(redundant))

        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": self.dsn, "AI_PRODUCT_TABLES_DIR": ""}):
            tables, issues, origin = load_default_tables()
            resolver = ProductResolver()
            identity = resolver.resolve("로지텍 MX Master S3 무선 마우스 해외직구")
            seeded = resolver.resolve("로지텍 엠엑스 마스터 3s")  # 시드 JSON 의 인라인 별칭도 DB 로 옮겨졌다

        self.assertEqual((origin, issues), ("postgres", []))
        self.assertEqual(len(tables.aliases), len(everything.aliases) - len(redundant))
        self.assertEqual(identity.canonical_id, "logitech:mx-master-3s")
        self.assertIn("catalog code 'mxmasters3' (alias: misspelling)", identity.evidence)
        self.assertEqual((identity.sourcing_category, identity.price_pool), ("DIRECT_PURCHASE", False))
        self.assertEqual(seeded.canonical_id, "logitech:mx-master-3s")

    def test_DB에서_거절한_시드_별칭은_파일의_인라인_별칭으로_되살아나지_않는다(self) -> None:
        import json

        from ..crawler.identity.catalog import _DEFAULT_PATH
        from ..crawler.identity.tables.overlay import tables_from_catalog_entries

        seed = tables_from_catalog_entries(json.loads(_DEFAULT_PATH.read_text(encoding="utf-8"))["products"])
        pgio.write_tables(self.dsn, seed)
        self.execute("UPDATE product_aliases SET status = 'rejected' WHERE alias_norm = 'mx마스터3s'")

        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": self.dsn, "AI_PRODUCT_TABLES_DIR": ""}):
            rejected = ProductResolver().resolve("로지텍 mx마스터3s")
            kept = ProductResolver().resolve("로지텍 엠엑스 마스터 3s")

        self.assertNotEqual(rejected.canonical_id, "logitech:mx-master-3s")
        self.assertEqual(kept.canonical_id, "logitech:mx-master-3s")

    def test_DB의_상품_행과_별칭으로_파일에_없는_직구_전용_상품을_식별한다(self) -> None:
        pgio.write_tables(self.dsn, ProductTables(
            [CatalogRow("import:acme-x1", "acme", "ACME X1", kc_certified_yn="N", source="import_only")],
            [A("import:acme-x1", "아크미 엑스원")],
            [SourcingCategoryRow("DIRECT_PURCHASE", "해외직구", "N", "N")], [SourcingSignalRow("DIRECT_PURCHASE", "keyword", "직구")],
        ))

        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": self.dsn, "AI_PRODUCT_TABLES_DIR": ""}):
            identity = ProductResolver().resolve("아크미 엑스원 직구 99,000원")

        self.assertEqual((identity.canonical_id, identity.sourcing_category), ("import:acme-x1", "DIRECT_PURCHASE"))
        self.assertEqual(identity.warnings, ())  # 직구는 인증 기록이 없는 것이 정상이라 공백 경고가 없다

    def test_DB를_읽지_못하면_조용히_비우지_않고_예외를_낸다(self) -> None:
        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": f"host={_server.sock} port=1 dbname=none user=test", "AI_PRODUCT_TABLES_DIR": ""}):  # type: ignore[union-attr]
            with self.assertRaises(Exception):
                ProductResolver()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
