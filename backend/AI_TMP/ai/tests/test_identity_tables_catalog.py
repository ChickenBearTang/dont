"""별칭/카탈로그 테이블을 Catalog 에 얹고, 유통경로를 식별 결과에 붙이는 흐름."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ..crawler.hot_deal_crawler import HotDealCrawler
from ..crawler.identity import BrandLexicon, Catalog, CatalogEntry, IdentityStatus, ProductResolver
from ..crawler.identity.tables.csvio import FILES, write_tables
from ..crawler.identity.tables.loader import PACKAGED_DIR, load_default_tables
from ..crawler.identity.tables.models import (
    AliasRow,
    CatalogRow,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
)
from ..crawler.identity.tables.overlay import (
    alias_rows_from_entries,
    apply_tables,
    row_from_entry,
    tables_from_catalog_entries,
)
from ..crawler.identity.tables.sourcing import SourcingClassifier


def E(cid, model, line="MX Master", brand="logitech", **kw):
    return CatalogEntry(id=cid, brand=brand, line=line, model=model, category="mouse", **kw)


def base_catalog():
    return Catalog([
        E("logi:3s", "MX Master 3S"), E("logi:3", "MX Master 3"), E("logi:4", "MX Master 4"),
        E("sam:buds", "Galaxy Buds3", line="Galaxy Buds", brand="samsung"),
    ])


def A(cid, text, **kw):
    kw.setdefault("status", "approved")
    return AliasRow(cid, text, **kw)


def resolve(tables, title, **kw):
    catalog, _ = apply_tables(base_catalog(), tables)
    return ProductResolver(catalog=catalog, sourcing=SourcingClassifier([], []), lexicon=BrandLexicon.load()).resolve(title, **kw)


class AliasOverlayTest(unittest.TestCase):
    def test_승인된_별칭으로_상품을_정확히_찾고_어떤_이름으로_맞았는지_남긴다(self) -> None:
        tables = ProductTables(aliases=[A("logi:3s", "MX Master S3", alias_type="misspelling")])

        identity = resolve(tables, "로지텍 MX Master S3 무선 마우스")

        self.assertEqual((identity.status, identity.canonical_id), (IdentityStatus.RESOLVED_CATALOG, "logi:3s"))
        self.assertIn("catalog code 'mxmasters3' (alias: misspelling)", identity.evidence)

    def test_모델_자체_코드로_맞으면_별칭_표시가_없다(self) -> None:
        identity = resolve(ProductTables(), "로지텍 MX Master 3S")

        self.assertEqual(identity.canonical_id, "logi:3s")
        self.assertIn("catalog code 'mxmaster3s'", identity.evidence)

    def test_승인_전_별칭과_거절한_별칭은_쓰지_않는다(self) -> None:
        for status in ("pending", "rejected"):
            tables = ProductTables(aliases=[A("logi:3s", "마스터 삼에스", status=status)])

            self.assertNotEqual(resolve(tables, "로지텍 마스터 삼에스").canonical_id, "logi:3s", status)

    def test_비슷한_모델은_뒤집힌_이름이_있어도_서로_섞이지_않는다(self) -> None:
        tables = ProductTables(aliases=[
            A("logi:3s", "MX Master S3", alias_type="misspelling"), A("logi:3", "로지텍 마스터 3", alias_type="colloquial"),
            A("logi:3s", "로지텍 마스터 3S", alias_type="colloquial"),
        ])

        self.assertEqual(resolve(tables, "로지텍 MX Master S3").canonical_id, "logi:3s")
        self.assertEqual(resolve(tables, "로지텍 마스터 3S 마우스").canonical_id, "logi:3s")
        self.assertEqual(resolve(tables, "로지텍 마스터 3 마우스").canonical_id, "logi:3")
        self.assertEqual(resolve(tables, "로지텍 MX Master 3 마우스").canonical_id, "logi:3")
        # '3' 이름이 '3S' 글의 앞부분에 걸려 버전을 바꾸지 않는다
        self.assertNotEqual(resolve(tables, "로지텍 마스터 3S 마우스").canonical_id, "logi:3")

    def test_브랜드_조건이_있는_이름은_제목에_그_브랜드가_있을_때만_맞는다(self) -> None:
        tables = ProductTables(aliases=[A("logi:3s", "마스터 3S", brand_required_yn="Y")])

        self.assertEqual(resolve(tables, "로지텍 마스터 3S 마우스").canonical_id, "logi:3s")
        self.assertEqual(resolve(tables, "마스터 3S 마우스").status, IdentityStatus.UNRESOLVED)  # 브랜드 없음
        self.assertNotEqual(resolve(tables, "삼성 마스터 3S 마우스").canonical_id, "logi:3s")  # 다른 브랜드

    def test_브랜드_조건은_그_이름에만_걸린다(self) -> None:
        tables = ProductTables(aliases=[A("logi:3s", "마스터 3S", brand_required_yn="Y")])

        self.assertEqual(resolve(tables, "MX Master 3S 마우스").canonical_id, "logi:3s")  # 모델 자체 코드는 브랜드 없이도 맞는다

    def test_제품군_이름만_말한_제목은_고르지_않고_후보를_준다(self) -> None:
        tables = ProductTables(aliases=[A(cid, "엠엑스 마스터", alias_kind="line") for cid in ("logi:3s", "logi:3", "logi:4")])

        identity = resolve(tables, "로지텍 엠엑스 마스터 무선 마우스")

        self.assertEqual(identity.status, IdentityStatus.AMBIGUOUS_VARIANT)
        self.assertEqual(sorted(identity.candidates), ["logi:3", "logi:3s", "logi:4"])
        self.assertIsNone(identity.canonical_id)

    def test_제품군_이름에_버전이_붙으면_그_상품으로_정해진다(self) -> None:
        tables = ProductTables(aliases=[A(cid, "엠엑스 마스터", alias_kind="line") for cid in ("logi:3s", "logi:3", "logi:4")])

        self.assertEqual(resolve(tables, "로지텍 MX Master 4 엠엑스 마스터").canonical_id, "logi:4")

    def test_충돌하는_별칭은_붙이지_않고_알리며_나머지는_정상_동작한다(self) -> None:
        tables = ProductTables(aliases=[
            A("logi:3s", "마스터 삼"), A("logi:3", "마스터 삼"),  # 두 상품이 주장
            A("logi:4", "MX Master 3S"),  # 다른 상품의 모델 코드
            A("logi:3", "엠엑스 마스터 쓰리"),  # 정상
        ])

        catalog, issues = apply_tables(base_catalog(), tables)

        self.assertEqual(sorted(i.code for i in issues), ["ALIAS_CONFLICT"] * 3)
        self.assertEqual(catalog.get("logi:3s").aliases, ())
        self.assertEqual(catalog.get("logi:4").aliases, ())
        self.assertEqual(catalog.get("logi:3").aliases, ("엠엑스 마스터 쓰리",))
        self.assertEqual(catalog.issues, issues)

    def test_파일_카탈로그에_이미_있는_별칭과_같으면_충돌로_본다(self) -> None:
        base = Catalog([E("logi:3s", "MX Master 3S", aliases=("마스터삼에스",)), E("logi:3", "MX Master 3")])

        catalog, issues = apply_tables(base, ProductTables(aliases=[A("logi:3", "마스터 삼에스")]))

        self.assertEqual([i.code for i in issues], ["ALIAS_CONFLICT"])
        self.assertEqual(catalog.get("logi:3").aliases, ())

    def test_원래_카탈로그는_바뀌지_않고_두_번_얹어도_중복이_없다(self) -> None:
        base = base_catalog()
        tables = ProductTables(aliases=[A("logi:3s", "MX Master S3")])

        once, _ = apply_tables(base, tables)
        twice, issues = apply_tables(once, tables)

        self.assertEqual(base.get("logi:3s").aliases, ())
        self.assertEqual(once.get("logi:3s").aliases, ("MX Master S3",))
        self.assertEqual(twice.get("logi:3s").aliases, ("MX Master S3",))
        self.assertEqual(issues, [])

    def test_별칭이_모델_코드와_같으면_경고하고_붙이지_않는다(self) -> None:
        catalog, issues = apply_tables(base_catalog(), ProductTables(aliases=[A("logi:3s", "mx-master-3s")]))

        self.assertEqual(catalog.get("logi:3s").aliases, ())
        self.assertEqual([(i.level, i.code) for i in issues], [("warning", "ALIAS_SAME_AS_MODEL")])

    def test_고아_별칭은_알리고_나머지는_얹는다(self) -> None:
        catalog, issues = apply_tables(base_catalog(), ProductTables(aliases=[A("ghost", "유령 이름"), A("logi:3", "마스터 쓰리")]))

        self.assertEqual([i.code for i in issues], ["ALIAS_ORPHAN"])
        self.assertEqual(catalog.get("logi:3").aliases, ("마스터 쓰리",))

    def test_기존_별칭_뒤에_더하고_원래_별칭은_유지한다(self) -> None:
        base = Catalog([E("logi:3s", "MX Master 3S", aliases=("엠엑스 마스터 3s",))])

        catalog, _ = apply_tables(base, ProductTables(aliases=[A("logi:3s", "MX Master S3")]))

        self.assertEqual(catalog.get("logi:3s").aliases, ("엠엑스 마스터 3s", "MX Master S3"))


class CatalogRowOverlayTest(unittest.TestCase):
    def test_테이블의_카탈로그_행으로_없는_상품을_더한다(self) -> None:
        row = CatalogRow("import:acme-x1", "acme", "ACME X1", product_line="X", category="mouse", kc_certified_yn="N", source="import_only")
        tables = ProductTables([row], [A("import:acme-x1", "아크미 엑스원")])

        catalog, issues = apply_tables(base_catalog(), tables)

        entry = catalog.get("import:acme-x1")
        self.assertEqual((entry.source, entry.kc_certified, entry.model), ("import_only", "N", "ACME X1"))
        self.assertEqual(entry.aliases, ("아크미 엑스원",))
        self.assertEqual(issues, [])
        self.assertEqual(len(catalog), len(base_catalog()) + 1)

    def test_테이블의_행이_같은_id의_파일_항목을_대체한다(self) -> None:
        """테이블이 맨 위 층이다. DB 에서 고친 값이 시드 JSON 보다 우선해야 한다."""
        base = Catalog([E("logi:3s", "MX Master 3S", aliases=("파일 별칭",), requires_brand=False), E("logi:3", "MX Master 3")])
        row = CatalogRow("logi:3s", "logitech", "MX Master 3S", product_line="MX Master", requires_brand_yn="Y", kc_certified_yn="Y", verified_yn="Y")

        catalog, issues = apply_tables(base, ProductTables([row], [A("logi:3s", "DB 별칭 하나")]))

        entry = catalog.get("logi:3s")
        self.assertEqual((entry.requires_brand, entry.kc_certified, entry.verified), (True, "Y", True))
        self.assertEqual(entry.aliases, ("DB 별칭 하나",))  # 파일의 인라인 별칭은 이어받지 않는다
        self.assertEqual(issues, [])
        self.assertEqual(len(catalog), 2)
        self.assertEqual(base.get("logi:3s").aliases, ("파일 별칭",))  # 원본은 그대로

    def test_대체하면_예전_표기는_비워져_다른_상품이_쓸_수_있다(self) -> None:
        base = Catalog([E("logi:3s", "MX Master 3S"), E("logi:3", "MX Master 3")])
        replaced = CatalogRow("logi:3s", "logitech", "MX Master 3S Plus")  # 모델 코드가 바뀜
        tables = ProductTables([replaced], [A("logi:3", "MX Master 3S")])  # 예전 코드를 이제 다른 상품이 쓴다

        catalog, issues = apply_tables(base, tables)

        self.assertEqual(issues, [])
        self.assertEqual(catalog.get("logi:3s").model, "MX Master 3S Plus")
        self.assertEqual(catalog.get("logi:3").aliases, ("MX Master 3S",))

    def test_대체하려는_행의_코드가_다른_상품과_겹치면_예전_항목을_둔다(self) -> None:
        base = Catalog([E("logi:3s", "MX Master 3S"), E("logi:3", "MX Master 3")])
        clashing = CatalogRow("logi:3s", "logitech", "MX Master 3")

        catalog, issues = apply_tables(base, ProductTables([clashing]))

        self.assertEqual(catalog.get("logi:3s").model, "MX Master 3S")
        self.assertEqual([i.code for i in issues], ["CATALOG_CODE_CLASH"])

    def test_모델_코드가_다른_상품과_같으면_더하지_않는다(self) -> None:
        row = CatalogRow("new:dup", "logitech", "MX Master 3S")

        catalog, issues = apply_tables(base_catalog(), ProductTables([row]))

        self.assertIsNone(catalog.get("new:dup"))
        self.assertEqual([i.code for i in issues], ["CATALOG_CODE_CLASH"])

    def test_행의_모든_속성이_항목으로_옮겨진다(self) -> None:
        row = CatalogRow(
            "kc:x", "nvidia", "RTX 9090", product_line="RTX", category="gpu", kc_certified_yn="Y", kc_info={"management_numbers": ["R-1"]},
            source="kc", verified_yn="Y", requires_brand_yn="Y", compatible_brands=("asus",), benign_suffixes=("oc",),
        )

        entry = apply_tables(Catalog([]), ProductTables([row]))[0].get("kc:x")

        self.assertEqual(
            (entry.brand, entry.line, entry.category, entry.verified, entry.requires_brand, entry.compatible_brands,
             entry.benign_suffixes, entry.source, entry.kc, entry.kc_certified),
            ("nvidia", "RTX", "gpu", True, True, ("asus",), ("oc",), "kc", {"management_numbers": ["R-1"]}, "Y"),
        )


class EntryConversionTest(unittest.TestCase):
    def test_KC_항목은_인증_Y로_바뀌고_파생모델_별칭은_kc_derived가_된다(self) -> None:
        entry = {"id": "kc:s:r510", "brand": "samsung", "line": "", "model": "SM-R510", "category": "무선이어폰", "aliases": ["SM-R511"],
                 "verified": True, "source": "kc", "requires_brand": False,
                 "kc": {"management_numbers": ["R-R-1"], "manufacturers": ["Samsung Electronics"], "countries": ["KR"], "first_date": "2024-01-01"}}

        row = row_from_entry(entry)
        aliases = alias_rows_from_entries([entry])

        self.assertEqual((row.kc_certified_yn, row.source, row.verified_yn, row.manufacturer), ("Y", "kc", "Y", "Samsung Electronics"))
        self.assertEqual(row.kc_info["management_numbers"], ["R-R-1"])
        self.assertEqual([(a.alias_text, a.alias_type, a.source, a.status) for a in aliases], [("SM-R511", "kc_derived", "kc", "approved")])

    def test_시드_항목은_인증_여부를_확인_안_함으로_둔다(self) -> None:
        row = row_from_entry({"id": "s:1", "brand": "logitech", "model": "MX", "aliases": ["엠엑스"]})

        self.assertEqual((row.kc_certified_yn, row.source, row.verified_yn), ("U", "seed", "N"))
        self.assertEqual(alias_rows_from_entries([{"id": "s:1", "brand": "b", "model": "m", "aliases": ["엠엑스", "!!"]}])[0].alias_type, "other")


class SeedToTablesTest(unittest.TestCase):
    def test_시드를_테이블로_옮긴_뒤_얹어도_식별_결과가_같다(self) -> None:
        import json

        from ..crawler.identity.catalog import _DEFAULT_PATH

        entries = json.loads(_DEFAULT_PATH.read_text(encoding="utf-8"))["products"]
        tables = tables_from_catalog_entries(entries)
        base = Catalog.load()

        merged, issues = apply_tables(base, tables)

        self.assertEqual([i for i in issues if i.level == "error"], [])
        self.assertEqual(len(tables.catalog), len(entries))
        self.assertEqual(len(merged), len(base))
        for a, b in zip(base.entries, merged.entries):
            self.assertEqual((a.id, a.model, a.line, a.requires_brand, a.compatible_brands, a.benign_suffixes),
                             (b.id, b.model, b.line, b.requires_brand, b.compatible_brands, b.benign_suffixes))
            self.assertEqual(set(a.codes), set(b.codes))  # 표기는 같은 이름의 중복('에어팟 프로 2'/'에어팟프로2')이 하나로 합쳐질 수 있어 비교용 값으로 본다
        for title in ("로지텍 MX Master 3S", "엠엑스 마스터 3s 로지텍", "MSI 지포스 RTX 4070 SUPER 벤투스", "갤럭시 버즈3 프로"):
            self.assertEqual(Catalog.load().match(title).status, merged.match(title).status, title)


CATS = [
    SourcingCategoryRow("OFFICIAL", "정식수입", "Y", "Y", "Y"), SourcingCategoryRow("PARALLEL", "병행수입", "U", "N"),
    SourcingCategoryRow("DIRECT", "해외직구", "N", "N"),
]
SIGNALS = [
    SourcingSignalRow("DIRECT", "keyword", "직구", 50), SourcingSignalRow("DIRECT", "domain", "aliexpress.com", 10),
    SourcingSignalRow("PARALLEL", "keyword", "병행", 50), SourcingSignalRow("OFFICIAL", "keyword", "정발", 50),
]


def sourcing_resolver(catalog=None):
    return ProductResolver(catalog=catalog or base_catalog(), sourcing=SourcingClassifier(CATS, SIGNALS), lexicon=BrandLexicon.load())


class ResolverSourcingTest(unittest.TestCase):
    def test_유통경로가_식별_결과에_붙고_상품_식별은_그대로다(self) -> None:
        plain = sourcing_resolver().resolve("로지텍 MX Master 3S 마우스")
        direct = sourcing_resolver().resolve("로지텍 MX Master 3S 마우스 해외직구")

        self.assertEqual((direct.status, direct.canonical_id, direct.group_key), (plain.status, plain.canonical_id, plain.group_key))
        self.assertEqual((direct.sourcing_status, direct.sourcing_category, direct.price_pool), ("classified", "DIRECT", False))
        self.assertEqual(direct.sourcing_evidence, ("keyword '직구' -> DIRECT",))

    def test_신호가_없으면_경로를_채우지_않는다(self) -> None:
        identity = sourcing_resolver().resolve("로지텍 MX Master 3S 마우스")

        self.assertEqual((identity.sourcing_status, identity.sourcing_category, identity.price_pool, identity.sourcing_evidence), ("none", None, None, ()))
        self.assertEqual(identity.series_key, identity.group_key)

    def test_가격을_합치지_않는_경로는_가격_이력_단위가_따로_나뉜다(self) -> None:
        resolver = sourcing_resolver()
        official = resolver.resolve("로지텍 MX Master 3S 마우스 정발")
        parallel = resolver.resolve("로지텍 MX Master 3S 마우스 병행")
        direct = resolver.resolve("로지텍 MX Master 3S 마우스 직구")
        unmarked = resolver.resolve("로지텍 MX Master 3S 마우스")

        self.assertEqual(official.series_key, "logi:3s")  # price_pool_yn=Y: 합쳐도 된다
        self.assertEqual(unmarked.series_key, "logi:3s")
        self.assertEqual(parallel.series_key, "logi:3s|parallel")
        self.assertEqual(direct.series_key, "logi:3s|direct")
        self.assertEqual({official.canonical_id, parallel.canonical_id, direct.canonical_id}, {"logi:3s"})  # 상품은 같다

    def test_신뢰하지_못한_식별도_경로를_나눈다(self) -> None:
        identity = sourcing_resolver().resolve("에이콤 신형 X1 마우스 직구")

        self.assertFalse(identity.trusted)
        self.assertTrue(identity.series_key.endswith("|direct"))
        self.assertTrue(identity.series_key.startswith("unverified:"))

    def test_주소의_도메인도_신호로_쓴다(self) -> None:
        identity = sourcing_resolver().resolve("로지텍 MX Master 3S", url="https://ko.aliexpress.com/item/1.html")

        self.assertEqual(identity.sourcing_category, "DIRECT")
        self.assertEqual(identity.sourcing_evidence, ("domain 'aliexpress.com' -> DIRECT",))

    def test_신호가_충돌하면_고르지_않고_경고한다(self) -> None:
        identity = sourcing_resolver().resolve("로지텍 MX Master 3S 병행 직구")

        self.assertEqual((identity.sourcing_status, identity.sourcing_category, identity.price_pool), ("conflict", None, None))
        self.assertIn("SOURCING_CONFLICT: DIRECT, PARALLEL", identity.warnings)
        self.assertEqual(identity.canonical_id, "logi:3s")  # 상품 식별은 영향받지 않는다
        self.assertEqual(identity.series_key, "logi:3s")

    def test_인증_기록을_기대하는_경로인데_인증_연결이_없으면_카탈로그_공백으로_알린다(self) -> None:
        identity = sourcing_resolver().resolve("로지텍 MX Master 3S 정발")

        self.assertTrue(any(w.startswith("KC_RECORD_EXPECTED_BUT_MISSING: OFFICIAL") for w in identity.warnings), identity.warnings)

    def test_인증_기록이_연결된_항목이면_경고하지_않는다(self) -> None:
        catalog = Catalog([E("logi:3s", "MX Master 3S", kc_certified="Y")])

        identity = sourcing_resolver(catalog).resolve("로지텍 MX Master 3S 정발")

        self.assertEqual(identity.warnings, ())

    def test_카탈로그에_없는_상품도_인증_기록이_기대되면_알린다(self) -> None:
        identity = sourcing_resolver().resolve("에이콤 신형 X1 마우스 정발")

        self.assertTrue(any(w.startswith("KC_RECORD_EXPECTED_BUT_MISSING") for w in identity.warnings))

    def test_인증_기록이_없는_것이_정상인_경로나_미확인_경로는_경고하지_않는다(self) -> None:
        for title in ("로지텍 MX Master 3S 직구", "로지텍 MX Master 3S 병행", "에이콤 신형 X1 마우스 직구"):
            identity = sourcing_resolver().resolve(title)
            self.assertFalse(any(w.startswith("KC_RECORD") for w in identity.warnings), (title, identity.warnings))

    def test_기존_경고를_지우지_않고_이어_붙인다(self) -> None:
        identity = sourcing_resolver().resolve("삼성 MX Master 3S 정발")  # 브랜드-모델 충돌 경고 + 경로

        self.assertTrue(any(w.startswith("BRAND_MODEL_CONFLICT") for w in identity.warnings))
        self.assertEqual(identity.sourcing_category, "OFFICIAL")

    def test_경로_분류기가_없으면_이전과_같다(self) -> None:
        resolver = ProductResolver(catalog=base_catalog(), sourcing=SourcingClassifier([], []), lexicon=BrandLexicon.load())

        identity = resolver.resolve("로지텍 MX Master 3S 직구 정발")

        self.assertEqual((identity.sourcing_status, identity.sourcing_category), ("none", None))


class DefaultTablesTest(unittest.TestCase):
    """패키지에 든 초기 파일(data/tables)로 기본 식별기가 동작한다."""

    @classmethod
    def setUpClass(cls) -> None:
        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": "", "AI_PRODUCT_TABLES_DIR": ""}):
            cls.resolver = ProductResolver()

    def test_초기_파일에는_걸러지는_행이_없다(self) -> None:
        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": "", "AI_PRODUCT_TABLES_DIR": ""}):
            tables, parse_issues, origin = load_default_tables()
        catalog, issues = apply_tables(Catalog.load(), tables)

        self.assertEqual((origin, parse_issues, issues), ("packaged", [], []))
        self.assertEqual(SourcingClassifier.from_tables(tables).issues, [])
        self.assertGreater(len(tables.aliases), 0)

    def test_MX_Master_S3는_3S로_맞고_근거에_별칭_종류가_남는다(self) -> None:
        identity = self.resolver.resolve("로지텍 MX Master S3 무선 마우스")

        self.assertEqual(identity.canonical_id, "logitech:mx-master-3s")
        self.assertIn("catalog code 'mxmasters3' (alias: misspelling)", identity.evidence)

    def test_비슷한_이름의_다른_모델과_섞이지_않는다(self) -> None:
        self.assertEqual(self.resolver.resolve("로지텍 마스터 3S 마우스").canonical_id, "logitech:mx-master-3s")
        self.assertEqual(self.resolver.resolve("로지텍 마스터 3 마우스").canonical_id, "logitech:mx-master-3")
        self.assertEqual(self.resolver.resolve("로지텍 마스터 4 마우스").canonical_id, "logitech:mx-master-4")

    def test_브랜드_없이_마스터만_말하면_고르지_않는다(self) -> None:
        for title in ("마스터 3S 마우스", "삼성 마스터 3S 마우스"):
            self.assertIsNone(self.resolver.resolve(title).canonical_id, title)

    def test_제품군만_말하면_후보를_준다(self) -> None:
        identity = self.resolver.resolve("로지텍 엠엑스 마스터 무선 마우스")

        self.assertEqual(identity.status, IdentityStatus.AMBIGUOUS_VARIANT)
        self.assertEqual(
            sorted(identity.candidates),
            ["logitech:mx-master-2s", "logitech:mx-master-3", "logitech:mx-master-3s", "logitech:mx-master-4"],
        )

    def test_직구_병행수입_정발을_구분한다(self) -> None:
        cases = {
            "로지텍 MX Master 3S 해외직구": ("DIRECT_PURCHASE", False),
            "로지텍 MX Master 3S 병행수입": ("PARALLEL_IMPORT", False),
            "로지텍 MX Master 3S 국내 정발": ("OFFICIAL_IMPORT", True),
            "로지텍 MX Master 3S 구매대행 해외직구": ("PURCHASING_AGENCY", False),
        }
        for title, (category, pool) in cases.items():
            identity = self.resolver.resolve(title)
            self.assertEqual((identity.sourcing_category, identity.price_pool), (category, pool), title)
            self.assertEqual(identity.canonical_id, "logitech:mx-master-3s", title)

    def test_도메인으로_직구를_알아본다(self) -> None:
        identity = self.resolver.resolve("로지텍 MX Master 3S 마우스", url="https://www.amazon.com/dp/B0")

        self.assertEqual(identity.sourcing_category, "DIRECT_PURCHASE")

    def test_직구_정발이_함께_있으면_충돌이다(self) -> None:
        identity = self.resolver.resolve("로지텍 MX Master 3S 정발 직구")

        self.assertEqual(identity.sourcing_status, "conflict")

    def test_초기_경로_규칙은_모두_미검수로_표시돼_있다(self) -> None:
        with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DSN": "", "AI_PRODUCT_TABLES_DIR": ""}):
            tables, _, _ = load_default_tables()

        self.assertTrue(tables.categories)
        self.assertTrue(all(c.reviewed_yn == "N" for c in tables.categories))


class EnvironmentTest(unittest.TestCase):
    def test_환경변수로_다른_디렉터리의_테이블을_쓴다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_tables(Path(tmp), ProductTables(
                [CatalogRow("import:acme", "acme", "ACME X1", kc_certified_yn="N", source="import_only")],
                [A("import:acme", "아크미 엑스원")], CATS, SIGNALS,
            ))
            with patch.dict(os.environ, {"AI_PRODUCT_TABLES_DIR": tmp, "AI_PRODUCT_TABLES_DSN": ""}):
                tables, issues, origin = load_default_tables()
                resolver = ProductResolver()
                identity = resolver.resolve("아크미 엑스원 직구")

        self.assertEqual((origin.startswith("csv:"), issues), (True, []))
        self.assertEqual((identity.canonical_id, identity.sourcing_category), ("import:acme", "DIRECT"))

    def test_지정한_디렉터리가_있으면_패키지_초기_파일은_쓰지_않는다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"AI_PRODUCT_TABLES_DIR": tmp, "AI_PRODUCT_TABLES_DSN": ""}):
            identity = ProductResolver().resolve("로지텍 MX Master S3 무선 마우스 해외직구")

        self.assertNotEqual(identity.canonical_id, "logitech:mx-master-3s")  # 초기 별칭 없음
        self.assertIsNone(identity.sourcing_category)  # 초기 신호 없음

    def test_패키지_초기_파일_경로가_존재한다(self) -> None:
        self.assertEqual(sorted(p.name for p in PACKAGED_DIR.iterdir()), sorted(FILES.values()))


class CrawlerPassesUrlTest(unittest.TestCase):
    def test_글_주소를_식별기에_넘긴다(self) -> None:
        seen: list[tuple[str, str | None]] = []

        class Stub:
            def resolve(self, title, *, url=None, page_html=None):
                seen.append((title, url))
                return None

        html = '<div class="market-info-list"><a href="/bbs/qb_saleinfo/views/9" class="subject-link ">로지텍 MX Master 3S</a></div>'
        HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=lambda url: html).crawl_normalized(resolver=Stub())

        self.assertEqual(seen, [("로지텍 MX Master 3S", "https://quasarzone.com/bbs/qb_saleinfo/views/9")])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
