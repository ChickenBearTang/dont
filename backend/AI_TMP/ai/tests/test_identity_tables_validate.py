"""상품 테이블(카탈로그/별칭/유통경로 규칙) 검증과 CSV 입출력."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ..crawler.identity.tables.csvio import COLUMNS, FILES, read_tables, write_tables
from ..crawler.identity.tables.models import (
    AliasRow,
    CatalogRow,
    ProductTables,
    SourcingCategoryRow,
    SourcingSignalRow,
    normalize_pattern,
)
from ..crawler.identity.tables.validate import clean_aliases, clean_catalog, clean_sourcing, clean_tables


def cat(cid="logi:a", model="MX Master 3S", brand="logitech", **kw):
    return CatalogRow(cid, brand, model, **kw)


def alias(cid="logi:a", text="마스터 3S 마우스", **kw):
    kw.setdefault("status", "approved")
    return AliasRow(cid, text, **kw)


def codes(issues):
    return sorted(i.code for i in issues)


class NormTest(unittest.TestCase):
    def test_별칭_비교값은_공백_하이픈_대소문자를_무시한다(self) -> None:
        self.assertEqual(AliasRow("x", "MX-Master  S3").alias_norm, "mxmasters3")
        self.assertEqual(cat(model="SM-R510").model_code_norm, "smr510")

    def test_신호_패턴_정규화(self) -> None:
        self.assertEqual(normalize_pattern("keyword", "해외 직구"), "해외직구")
        self.assertEqual(normalize_pattern("keyword", " 직구! "), "직구")
        self.assertEqual(normalize_pattern("token", "iPhone  15"), "iphone 15")
        self.assertEqual(normalize_pattern("token", "iphone15"), "iphone15")
        self.assertEqual(normalize_pattern("domain", " AliExpress.COM. "), "aliexpress.com")


class CatalogValidationTest(unittest.TestCase):
    def test_정상_행은_통과한다(self) -> None:
        kept, issues = clean_catalog([cat(), cat("logi:b", "MX Master 4")])

        self.assertEqual(len(kept), 2)
        self.assertEqual(issues, [])

    def test_필수_값이_비면_거부한다(self) -> None:
        for bad in (cat(cid=""), cat(brand="  "), cat(model="--")):
            kept, issues = clean_catalog([bad])
            self.assertEqual((kept, codes(issues)), ([], ["CATALOG_EMPTY_FIELD"]), bad)

    def test_허용되지_않는_값을_거부한다(self) -> None:
        for bad in (cat(kc_certified_yn="X"), cat(verified_yn="U"), cat(requires_brand_yn="y "), cat(source="web")):
            kept, issues = clean_catalog([bad])
            self.assertEqual((kept, codes(issues)), ([], ["CATALOG_BAD_VALUE"]), bad)

    def test_인증_여부는_미확인_U를_허용하지만_검수_여부는_Y_N만이다(self) -> None:
        self.assertEqual(len(clean_catalog([cat(kc_certified_yn="U")])[0]), 1)
        self.assertEqual(clean_catalog([cat(verified_yn="U")])[0], [])

    def test_id_중복은_뒤의_행을_뺀다(self) -> None:
        kept, issues = clean_catalog([cat("same"), cat("same", "Other 9")])

        self.assertEqual([r.model_code for r in kept], ["MX Master 3S"])
        self.assertEqual(codes(issues), ["CATALOG_DUPLICATE_ID"])

    def test_같은_브랜드의_같은_모델_코드는_표기가_달라도_중복이다(self) -> None:
        kept, issues = clean_catalog([cat("a", "MX Master 3S"), cat("b", "mx-master-3s")])

        self.assertEqual([r.catalog_id for r in kept], ["a"])
        self.assertEqual(codes(issues), ["CATALOG_DUPLICATE_MODEL"])

    def test_다른_브랜드의_같은_모델_코드는_허용한다(self) -> None:
        kept, issues = clean_catalog([cat("a", "K2", brand="keychron"), cat("b", "K2", brand="other")])

        self.assertEqual(len(kept), 2)
        self.assertEqual(issues, [])


class AliasValidationTest(unittest.TestCase):
    IDS = {"logi:a", "logi:b"}

    def clean(self, rows, reserved=None):
        return clean_aliases(rows, known_ids=self.IDS, reserved_codes=reserved or {})

    def test_정상_별칭은_통과한다(self) -> None:
        kept, issues = self.clean([alias()])

        self.assertEqual(len(kept), 1)
        self.assertEqual(issues, [])

    def test_없는_상품에_붙은_별칭은_거부한다(self) -> None:
        kept, issues = self.clean([alias("nope")])

        self.assertEqual((kept, codes(issues)), ([], ["ALIAS_ORPHAN"]))

    def test_비교할_글자가_없는_별칭은_거부한다(self) -> None:
        for text in ("", "!!", "a"):
            kept, issues = self.clean([alias(text=text)])
            self.assertEqual((kept, codes(issues)), ([], ["ALIAS_EMPTY"]), text)

    def test_허용되지_않는_값은_거부한다(self) -> None:
        for bad in (alias(alias_kind="both"), alias(alias_type="nick"), alias(status="ok"), alias(brand_required_yn="U"), alias(source="web")):
            kept, issues = self.clean([bad])
            self.assertEqual((kept, codes(issues)), ([], ["ALIAS_BAD_VALUE"]), bad)

    def test_짧거나_숫자뿐인_이름은_브랜드_조건_없이는_거부한다(self) -> None:
        for text in ("3s", "mx3", "12345", "4"):
            kept, issues = self.clean([alias(text=text)])
            expected = ["ALIAS_EMPTY"] if len("".join(ch for ch in text if ch.isalnum())) < 2 else ["ALIAS_TOO_GENERIC"]
            self.assertEqual((kept, codes(issues)), ([], expected), text)

    def test_짧은_이름도_브랜드_조건을_걸면_허용한다(self) -> None:
        kept, issues = self.clean([alias(text="3s", brand_required_yn="Y")])

        self.assertEqual(len(kept), 1)
        self.assertEqual(issues, [])

    def test_네_글자는_안전한_길이다(self) -> None:
        self.assertEqual(len(self.clean([alias(text="마스터3s")])[0]), 1)  # 마스터3s = 5자
        self.assertEqual(len(self.clean([alias(text="ab12")])[0]), 1)  # 정확히 4자
        self.assertEqual(self.clean([alias(text="ab1")])[0], [])  # 3자

    def test_거절한_별칭은_너무_짧아도_기록으로_남긴다(self) -> None:
        kept, issues = self.clean([alias(text="3s", status="rejected")])

        self.assertEqual(len(kept), 1)
        self.assertEqual(issues, [])

    def test_같은_상품의_같은_이름은_중복으로_본다(self) -> None:
        kept, issues = self.clean([alias(text="마스터 3S 마우스"), alias(text="마스터-3s 마우스")])

        self.assertEqual(len(kept), 1)
        self.assertEqual(codes(issues), ["ALIAS_DUPLICATE"])

    def test_같은_이름을_두_상품이_정확한_이름으로_주장하면_둘_다_뺀다(self) -> None:
        kept, issues = self.clean([alias("logi:a", "마스터 삼"), alias("logi:b", "마스터-삼")])

        self.assertEqual(kept, [])
        self.assertEqual(codes(issues), ["ALIAS_CONFLICT", "ALIAS_CONFLICT"])

    def test_제품군_이름은_여러_상품에_걸쳐도_충돌이_아니다(self) -> None:
        rows = [alias("logi:a", "엠엑스 마스터", alias_kind="line"), alias("logi:b", "엠엑스 마스터", alias_kind="line")]

        kept, issues = self.clean(rows)

        self.assertEqual(len(kept), 2)
        self.assertEqual(issues, [])

    def test_다른_상품의_모델_코드와_같은_이름은_충돌이다(self) -> None:
        kept, issues = self.clean([alias("logi:a", "MX Master 4")], reserved={"mxmaster4": "logi:b"})

        self.assertEqual((kept, codes(issues)), ([], ["ALIAS_CONFLICT"]))

    def test_자기_상품의_모델_코드와_같은_이름은_경고만_하고_뺀다(self) -> None:
        kept, issues = clean_aliases(
            [alias("logi:a", "MX Master 3S")], known_ids=self.IDS, reserved_codes={"mxmaster3s": "logi:a"}, model_codes={"mxmaster3s": "logi:a"},
        )

        self.assertEqual(kept, [])
        self.assertEqual([(i.level, i.code) for i in issues], [("warning", "ALIAS_SAME_AS_MODEL")])

    def test_이미_같은_상품의_별칭으로_있는_이름은_경고하지_않고_통과한다(self) -> None:
        """다시 가져오기나 갱신: 이미 있는 별칭이 '자기 코드와 같다'는 이유로 버려지면 갱신이 적용되지 않는다."""
        kept, issues = self.clean([alias("logi:a", "마스터 삼")], reserved={"마스터삼": "logi:a"})

        self.assertEqual(len(kept), 1)
        self.assertEqual(issues, [])

    def test_승인_전_별칭이_충돌하면_경고만_하고_남긴다(self) -> None:
        rows = [alias("logi:a", "마스터 삼", status="approved"), alias("logi:b", "마스터 삼", status="pending")]

        kept, issues = self.clean(rows)

        self.assertEqual(len(kept), 2)
        self.assertEqual([(i.level, i.code) for i in issues], [("warning", "PENDING_ALIAS_WOULD_CONFLICT")])

    def test_거절한_별칭은_충돌_검사에서_빠진다(self) -> None:
        rows = [alias("logi:a", "마스터 삼", status="approved"), alias("logi:b", "마스터 삼", status="rejected")]

        kept, issues = self.clean(rows)

        self.assertEqual(len(kept), 2)
        self.assertEqual(issues, [])


class SourcingValidationTest(unittest.TestCase):
    CATS = [SourcingCategoryRow("DIRECT", "직구", "N", "N"), SourcingCategoryRow("OFFICIAL", "정식", "Y", "Y")]

    def clean(self, signals, categories=None):
        return clean_sourcing(self.CATS if categories is None else categories, signals)

    def test_정상_신호는_통과한다(self) -> None:
        _, kept, issues = self.clean([
            SourcingSignalRow("DIRECT", "keyword", "직구"), SourcingSignalRow("DIRECT", "domain", "aliexpress.com"),
            SourcingSignalRow("DIRECT", "token", "ebay"),
        ])

        self.assertEqual(len(kept), 3)
        self.assertEqual(issues, [])

    def test_경로_행의_값을_검사한다(self) -> None:
        cats, _, issues = clean_sourcing([
            SourcingCategoryRow("A", "가", "X", "N"), SourcingCategoryRow("B", "나", "Y", "U"),
            SourcingCategoryRow("C", "다", "U", "N"), SourcingCategoryRow("", "라", "Y", "Y"), SourcingCategoryRow("D", " ", "Y", "Y"),
        ], [])

        self.assertEqual([c.category_code for c in cats], ["C"])  # price_pool 은 Y/N 만, kc_record_expected 는 Y/N/U
        self.assertEqual(codes(issues), ["CATEGORY_BAD_VALUE", "CATEGORY_BAD_VALUE", "CATEGORY_EMPTY_FIELD", "CATEGORY_EMPTY_FIELD"])

    def test_경로_코드_중복은_뒤의_행을_뺀다(self) -> None:
        cats, _, issues = clean_sourcing([SourcingCategoryRow("A", "가", "Y", "Y"), SourcingCategoryRow("A", "나", "N", "N")], [])

        self.assertEqual([c.label_ko for c in cats], ["가"])
        self.assertEqual(codes(issues), ["CATEGORY_DUPLICATE"])

    def test_없는_경로를_가리키는_신호는_거부한다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("NOPE", "keyword", "직구")])

        self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_UNKNOWN_CATEGORY"]))

    def test_허용되지_않는_신호_값을_거부한다(self) -> None:
        _, kept, issues = self.clean([
            SourcingSignalRow("DIRECT", "regex", "직구"), SourcingSignalRow("DIRECT", "keyword", "직구", enabled_yn="X"),
        ])

        self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_BAD_VALUE", "SIGNAL_BAD_VALUE"]))

    def test_도메인은_호스트_이름만_허용한다(self) -> None:
        for bad in ("https://aliexpress.com", "aliexpress.com/item", "aliexpress", "ali express.com", "-bad.com"):
            _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "domain", bad)])
            self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_BAD_DOMAIN"]), bad)

    def test_한_글자_신호는_거부한다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "keyword", "직"), SourcingSignalRow("DIRECT", "token", "a")])

        self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_PATTERN_TOO_SHORT", "SIGNAL_PATTERN_TOO_SHORT"]))

    def test_비교할_글자가_없는_신호는_거부한다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "keyword", "!!!")])

        self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_EMPTY_PATTERN"]))

    def test_같은_신호가_서로_다른_경로를_가리키면_모두_뺀다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "keyword", "정발"), SourcingSignalRow("OFFICIAL", "keyword", "정 발")])

        self.assertEqual((kept, codes(issues)), ([], ["SIGNAL_CONFLICT"]))

    def test_같은_신호가_같은_경로로_중복이면_하나만_남긴다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "keyword", "직구"), SourcingSignalRow("DIRECT", "keyword", "직구 ")])

        self.assertEqual(len(kept), 1)
        self.assertEqual([(i.level, i.code) for i in issues], [("warning", "SIGNAL_DUPLICATE")])

    def test_종류가_다르면_같은_패턴도_다른_신호다(self) -> None:
        _, kept, issues = self.clean([SourcingSignalRow("DIRECT", "keyword", "ebay"), SourcingSignalRow("OFFICIAL", "token", "ebay")])

        self.assertEqual(len(kept), 2)
        self.assertEqual(issues, [])


class CleanTablesTest(unittest.TestCase):
    def test_표_사이의_참조를_함께_검사한다(self) -> None:
        tables = ProductTables(
            [cat("logi:a")], [alias("logi:a"), alias("ghost")],
            [SourcingCategoryRow("DIRECT", "직구", "N", "N")], [SourcingSignalRow("DIRECT", "keyword", "직구")],
        )

        clean, issues = clean_tables(tables)

        self.assertEqual(len(clean.aliases), 1)
        self.assertEqual(codes(issues), ["ALIAS_ORPHAN"])

    def test_밖에_있는_상품과_표기를_알려_줄_수_있다(self) -> None:
        tables = ProductTables([], [alias("file:x", "마스터 삼"), alias("file:y", "마스터 사"), alias("file:x", "엠엑스 사")])

        clean, issues = clean_tables(tables, known_ids={"file:x", "file:y"}, reserved_codes={"마스터사": "file:z"})

        self.assertEqual([a.alias_text for a in clean.aliases], ["마스터 삼", "엠엑스 사"])
        self.assertEqual(codes(issues), ["ALIAS_CONFLICT"])


class CsvRoundTripTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = Path(self.dir.name)

    def sample(self) -> ProductTables:
        return ProductTables(
            [cat("kc:logi:ymr0087", "YR0087", display_name="Logitech MX Master 3S", product_line="MX Master", category="mouse",
                 manufacturer="Logitech Europe S.A.", kc_certified_yn="Y", kc_info={"management_numbers": ["R-R-LGE-1", "R-R-LGE-2"], "countries": ["CN"]},
                 source="kc", verified_yn="Y", requires_brand_yn="Y", compatible_brands=("asus", "msi"), benign_suffixes=("black", "블랙")),
             cat("seed:b", "Only Seed")],
            [alias("kc:logi:ymr0087", "MX Master S3", alias_type="misspelling", note="쉼표, 따옴표 \" 와\n줄바꿈", reviewed_by="kim"),
             alias("kc:logi:ymr0087", "마스터 3S", alias_kind="line", brand_required_yn="Y", status="pending", source="crawl_suggested")],
            [SourcingCategoryRow("DIRECT", "해외직구", "N", "N", "N", 30, "메모")],
            [SourcingSignalRow("DIRECT", "domain", "aliexpress.com", 10, "Y", "알리"), SourcingSignalRow("DIRECT", "keyword", "직구", 50, "N")],
        )

    def test_쓰고_읽으면_같다(self) -> None:
        original = self.sample()

        write_tables(self.path, original)
        loaded, issues = read_tables(self.path)

        self.assertEqual(issues, [])
        self.assertEqual(loaded, original)

    def test_파일_이름과_열_이름이_DB_테이블과_같다(self) -> None:
        write_tables(self.path, ProductTables())

        self.assertEqual(sorted(p.name for p in self.path.iterdir()), sorted(FILES.values()))
        for kind, name in FILES.items():
            header = (self.path / name).read_text(encoding="utf-8-sig").splitlines()[0]
            self.assertEqual(header.split(","), COLUMNS[kind])

    def test_빈_값은_기본값으로_읽는다(self) -> None:
        (self.path / FILES["aliases"]).write_text("catalog_id,alias_text\nlogi:a,마스터 삼\n", encoding="utf-8")
        (self.path / FILES["catalog"]).write_text("catalog_id,brand,model_code\nlogi:a,Logitech,MX\n", encoding="utf-8")

        loaded, issues = read_tables(self.path)

        self.assertEqual(issues, [])
        a = loaded.aliases[0]
        self.assertEqual((a.alias_kind, a.alias_type, a.brand_required_yn, a.status, a.source), ("model", "other", "N", "pending", "curated"))
        c = loaded.catalog[0]
        self.assertEqual((c.brand, c.kc_certified_yn, c.source, c.verified_yn, c.kc_info), ("logitech", "U", "curated", "N", {}))

    def test_Y_N은_소문자로_써도_읽는다(self) -> None:
        (self.path / FILES["categories"]).write_text("category_code,label_ko,kc_record_expected_yn,price_pool_yn\nD,직구,n,y\n", encoding="utf-8")

        loaded, _ = read_tables(self.path)

        self.assertEqual((loaded.categories[0].kc_record_expected_yn, loaded.categories[0].price_pool_yn), ("N", "Y"))

    def test_없는_파일은_빈_표로_읽는다(self) -> None:
        loaded, issues = read_tables(self.path)

        self.assertEqual(loaded.counts(), {"product_catalog": 0, "product_aliases": 0, "sourcing_categories": 0, "sourcing_signals": 0})
        self.assertEqual(issues, [])

    def test_형식이_깨진_행은_건너뛰고_알린다(self) -> None:
        (self.path / FILES["signals"]).write_text(
            "category_code,match_type,pattern,priority\nD,keyword,직구,abc\nD,keyword,알리,50\n", encoding="utf-8",
        )
        (self.path / FILES["catalog"]).write_text(
            "catalog_id,brand,model_code,kc_info\nx,b,m,{깨짐\ny,b,n,[1]\nz,b,o,\"{\"\"a\"\": 1}\"\n", encoding="utf-8",
        )

        loaded, issues = read_tables(self.path)

        self.assertEqual([s.pattern for s in loaded.signals], ["알리"])
        self.assertEqual([c.catalog_id for c in loaded.catalog], ["z"])
        self.assertEqual(sorted((i.table, i.code) for i in issues), [("product_catalog", "CSV_BAD_ROW")] * 2 + [("sourcing_signals", "CSV_BAD_ROW")])
        self.assertTrue(all(":" in i.key for i in issues))  # 파일:줄 번호

    def test_필수_열이_없으면_그_파일은_읽지_않는다(self) -> None:
        (self.path / FILES["aliases"]).write_text("alias_text\n마스터\n", encoding="utf-8")

        loaded, issues = read_tables(self.path)

        self.assertEqual(loaded.aliases, [])
        self.assertEqual(codes(issues), ["CSV_MISSING_COLUMN"])

    def test_BOM과_CRLF를_읽는다(self) -> None:
        (self.path / FILES["aliases"]).write_bytes("﻿catalog_id,alias_text\r\nlogi:a,마스터 삼\r\n".encode("utf-8"))

        loaded, _ = read_tables(self.path)

        self.assertEqual([a.alias_text for a in loaded.aliases], ["마스터 삼"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
