"""KC(공공 인증 DB) 가져오기 테스트.

픽스처(fixtures/crawler/kc_records_sample.csv)는 합성이다. 실제 인증 데이터가 아니며 모델 코드도
가상이다. 열 이름은 국립전파연구원 '자기적합확인 DB정보' API 의 응답 항목(업체명, 기자재명칭,
기본모델, 파생모델, 관리번호, 제조자, 제조국가, 공개년월일)을 따랐다. 실제 응답 스키마는
활용가이드로 확인해야 하고, 열 이름이 다르면 mapping 으로 바꾼다.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from ..crawler.identity import BrandLexicon, Catalog, ProductResolver
from ..crawler.identity.kc_import import (
    build_entries,
    merge_with_curated,
    read_kc_records,
    write_catalog,
)

FIX = Path(__file__).parent / "fixtures" / "crawler"
SAMPLE = FIX / "kc_records_sample.csv"
LEX = BrandLexicon.load()


def entries_by_id(result):
    return {e["id"]: e for e in result.entries}


class ReadRecordsTest(unittest.TestCase):
    def test_CSV를_읽는다(self) -> None:
        records, report = read_kc_records(SAMPLE)

        self.assertEqual(len(records), 10)
        self.assertEqual(records[0]["model"], "SM-T510")
        self.assertEqual(records[0]["manufacturer"], "삼성전자(주)")
        self.assertEqual(records[0]["derived"], ["SM-T510NZKAKOO", "SM-T510NZAAKOO"])
        self.assertEqual(report["format"], "csv")

    def test_CP949_인코딩도_읽는다(self) -> None:
        """공공데이터 CSV 는 CP949 인 경우가 많다."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.csv"
            path.write_bytes("기본모델,제조자\nSM-T510,삼성전자(주)\n".encode("cp949"))

            records, report = read_kc_records(path)

        self.assertEqual(records[0]["manufacturer"], "삼성전자(주)")
        self.assertEqual(report["encoding"], "cp949")

    def test_JSON_data_go_kr_형태를_읽는다(self) -> None:
        body = {"response": {"body": {"items": {"item": [{"기본모델": "ZZ-1", "제조자": "Logitech"}]}}}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.json"
            path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")

            records, report = read_kc_records(path)

        self.assertEqual(records[0]["model"], "ZZ-1")
        self.assertEqual(report["format"], "json")

    def test_XML을_읽는다(self) -> None:
        xml = "<response><body><items><item><기본모델>ZZ-2</기본모델><제조자>Sony</제조자></item></items></body></response>"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.xml"
            path.write_text(xml, encoding="utf-8")

            records, _ = read_kc_records(path)

        self.assertEqual(records[0]["model"], "ZZ-2")

    def test_열_이름이_다르면_mapping으로_바꾼다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.csv"
            path.write_text("model_no,maker\nQQ-1,Sony\n", encoding="utf-8")

            records, _ = read_kc_records(path, mapping={"model": ["model_no"], "manufacturer": ["maker"]})

        self.assertEqual(records[0]["model"], "QQ-1")

    def test_모델_열을_못_찾으면_알려준다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.csv"
            path.write_text("foo,bar\n1,2\n", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                read_kc_records(path)

        self.assertIn("모델", str(ctx.exception))

    def test_지원하지_않는_형식(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kc.xlsx"
            path.write_bytes(b"x")

            with self.assertRaises(ValueError):
                read_kc_records(path)


class BuildEntriesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        records, _ = read_kc_records(SAMPLE)
        cls.result = build_entries(records, LEX)
        cls.by_id = entries_by_id(cls.result)

    def test_같은_기본모델의_여러_인증은_한_상품으로_합친다(self) -> None:
        entry = self.by_id["kc:samsung:smt510"]

        self.assertEqual(entry["model"], "SM-T510")
        self.assertEqual(sorted(entry["kc"]["management_numbers"]), ["TEST-0001", "TEST-0002"])
        self.assertEqual(sorted(entry["aliases"]), ["SM-T510NZAAKOO", "SM-T510NZKAKOO", "SM-T510NZVAKOO"])  # 파생모델은 별칭

    def test_제조자를_브랜드로_바꾼다(self) -> None:
        self.assertEqual(self.by_id["kc:logitech:zz1000"]["brand"], "logitech")  # 'Logitech Europe S.A.'
        self.assertEqual(self.by_id["kc:samsung:smt510"]["brand"], "samsung")  # '삼성전자(주)'

    def test_사전에_없는_제조자는_보고하고_그대로_브랜드로_쓴다(self) -> None:
        self.assertIn("에이비씨전자", self.result.report["unmapped_manufacturers"])
        self.assertTrue(any(e["brand"] != "samsung" and "abc5000" in e["id"] for e in self.result.entries))

    def test_짧거나_흔한_코드는_브랜드_필수로_표시한다(self) -> None:
        self.assertTrue(self.by_id["kc:keychron:k2"]["requires_brand"])
        self.assertFalse(self.by_id["kc:samsung:smt510"]["requires_brand"])  # 영문+숫자 6자 이상

    def test_서로_다른_제조사가_같은_코드를_주장하면_둘_다_제외하고_보고한다(self) -> None:
        self.assertNotIn("kc:samsung:dup7000", self.by_id)
        self.assertNotIn("kc:lg:dup7000", self.by_id)
        conflicts = self.result.report["conflicts"]
        self.assertTrue(any(c["code"] == "dup7000" for c in conflicts))

    def test_다른_상품의_기본모델과_겹치는_파생모델_별칭은_버리고_보고한다(self) -> None:
        sony = next(e for e in self.result.entries if e["brand"] == "sony" and "sn2200" in e["id"])

        self.assertNotIn("ZZ-1000", sony["aliases"])
        self.assertTrue(any(d["alias"] == "ZZ-1000" for d in self.result.report["dropped_aliases"]))

    def test_모델이_없거나_너무_짧은_행은_건너뛰고_센다(self) -> None:
        self.assertEqual(self.result.report["skipped_empty_model"], 1)
        self.assertEqual(self.result.report["skipped_too_short"], 1)

    def test_모든_항목은_공공_인증_출처이고_카탈로그가_받아들인다(self) -> None:
        for entry in self.result.entries:
            self.assertEqual(entry["source"], "kc")
            self.assertTrue(entry["verified"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog_kc.json"
            write_catalog(path, self.result.entries)
            catalog = Catalog.load(path)

        self.assertEqual(len(catalog), len(self.result.entries))

    def test_보고서에_집계가_들어_있다(self) -> None:
        report = self.result.report

        self.assertEqual(report["records"], 10)
        self.assertEqual(report["entries"], len(self.result.entries))


class ResolveWithKcCatalogTest(unittest.TestCase):
    def _resolver(self):
        records, _ = read_kc_records(SAMPLE)
        result = build_entries(records, LEX)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            write_catalog(path, result.entries)
            return ProductResolver(catalog=Catalog.load(path))

    def test_제목의_모델_코드로_식별한다(self) -> None:
        identity = self._resolver().resolve("[쿠팡] 삼성 무선 이어폰 SM-T510 (129,000원)")

        self.assertEqual(identity.canonical_id, "kc:samsung:smt510")
        self.assertTrue(identity.trusted)

    def test_파생모델_코드로도_같은_상품이다(self) -> None:
        identity = self._resolver().resolve("삼성 SM-T510NZKAKOO 정품")

        self.assertEqual(identity.canonical_id, "kc:samsung:smt510")

    def test_짧은_코드는_브랜드가_없으면_맞추지_않는다(self) -> None:
        resolver = self._resolver()

        self.assertNotEqual(resolver.resolve("K2 키보드 특가").canonical_id, "kc:keychron:k2")
        self.assertEqual(resolver.resolve("키크론 K2 키보드").canonical_id, "kc:keychron:k2")

    def test_충돌로_제외된_코드는_식별하지_않는다(self) -> None:
        self.assertFalse(self._resolver().resolve("삼성 DUP-7000 스피커").trusted)


class MergeWithCuratedTest(unittest.TestCase):
    CURATED = [
        {"id": "curated:testbuds", "brand": "samsung", "line": "Test Buds", "model": "Test Buds Pro", "category": "earbuds",
         "aliases": [], "verified": True, "source": "curated"},
    ]

    def _merged(self):
        records, _ = read_kc_records(SAMPLE)
        built = build_entries(records, LEX)
        rows = list(csv.DictReader((FIX / "kc_aliases_sample.csv").open(encoding="utf-8")))
        return merge_with_curated(built.entries, [dict(c) for c in self.CURATED], [(r["catalog_id"], r["alias"]) for r in rows])

    def test_별칭_파일이_모델_코드와_마케팅_이름을_잇는다(self) -> None:
        merged = self._merged()
        curated = next(e for e in merged.entries if e["id"] == "curated:testbuds")

        self.assertIn("SM-T510", curated["aliases"])
        self.assertIn("테스트 버즈 프로", curated["aliases"])
        self.assertIn("SM-T510NZKAKOO", curated["aliases"])  # KC 파생모델도 따라온다
        self.assertEqual(curated["kc"]["management_numbers"], ["TEST-0001", "TEST-0002"])

    def test_흡수된_KC_항목은_따로_남지_않는다(self) -> None:
        merged = self._merged()

        self.assertNotIn("kc:samsung:smt510", [e["id"] for e in merged.entries])

    def test_카탈로그에_없는_별칭_대상과_KC에_없는_코드를_보고한다(self) -> None:
        merged = self._merged()

        self.assertIn("curated:ghost", [m["catalog_id"] for m in merged.report["alias_unknown_catalog_id"]])

    def test_검수_항목이_우선하고_합친_결과를_카탈로그가_받아들인다(self) -> None:
        merged = self._merged()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            write_catalog(path, merged.entries)
            catalog = Catalog.load(path)

        result = ProductResolver(catalog=catalog).resolve("삼성 SM-T510 테스트 버즈")
        self.assertEqual(result.canonical_id, "curated:testbuds")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class AliasCollisionTest(unittest.TestCase):
    def test_두_상품이_같은_파생모델을_별칭으로_주장하면_둘_다_버리고_보고한다(self) -> None:
        """그대로 두면 카탈로그를 읽을 때 코드 충돌로 멈춘다."""
        records = [
            {"model": "AA-1111", "derived": ["SHARED-1"], "manufacturer": "Sony", "company": None, "equipment": "x",
             "management_no": "1", "date": None, "country": None},
            {"model": "BB-2222", "derived": ["SHARED-1"], "manufacturer": "Sony", "company": None, "equipment": "x",
             "management_no": "2", "date": None, "country": None},
        ]

        result = build_entries(records, LEX)

        for entry in result.entries:
            self.assertNotIn("SHARED-1", entry["aliases"])
        self.assertEqual(sum(1 for d in result.report["dropped_aliases"] if d["alias"] == "SHARED-1"), 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            write_catalog(path, result.entries)
            Catalog.load(path)  # 충돌 없이 읽혀야 한다


class LoadManyTest(unittest.TestCase):
    def _write(self, tmp, name, entries):
        path = Path(tmp) / name
        write_catalog(path, entries)
        return path

    def _entry(self, id_, model, **kw):
        return {"id": id_, "brand": "sony", "line": "", "model": model, "category": "x", "aliases": [], "verified": True,
                "source": kw.pop("source", "curated"), **kw}

    def test_앞선_파일이_우선하고_뒤의_중복은_건너뛰고_기록한다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self._write(tmp, "a.json", [self._entry("curated:x", "XX-1000")])
            second = self._write(tmp, "b.json", [
                self._entry("kc:sony:xx1000", "XX-1000", source="kc"),   # 같은 코드, 다른 id -> 건너뜀
                self._entry("kc:sony:yy2000", "YY-2000", source="kc"),   # 새 항목 -> 들어옴
                self._entry("curated:x", "ZZ-3000", source="kc"),         # 같은 id -> 건너뜀
            ])

            catalog = Catalog.load_many([first, second])

        self.assertEqual(sorted(e.id for e in catalog._entries), ["curated:x", "kc:sony:yy2000"])
        self.assertEqual(len(catalog.skipped), 2)
        self.assertTrue(any("same code" in reason for _, reason in catalog.skipped))
        self.assertTrue(any("duplicate id" in reason for _, reason in catalog.skipped))

    def test_기본_카탈로그는_환경변수로_추가_파일을_받는다(self) -> None:
        import os
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            extra = self._write(tmp, "kc.json", [self._entry("kc:sony:qq9000", "QQ-9000", source="kc")])

            with patch.dict(os.environ, {"AI_PRODUCT_CATALOG_PATHS": str(extra)}):
                catalog = Catalog.load_default()

        ids = {e.id for e in catalog._entries}
        self.assertIn("kc:sony:qq9000", ids)
        self.assertIn("logitech:mx-master-3s", ids)  # 시드도 그대로

    def test_환경변수가_없으면_시드만_쓴다(self) -> None:
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"AI_PRODUCT_CATALOG_PATHS": ""}):
            catalog = Catalog.load_default()

        self.assertTrue(all(e.source == "seed" for e in catalog._entries))


class CliRunTest(unittest.TestCase):
    def test_입력부터_카탈로그_파일까지_한_번에_만들고_다시_읽는다(self) -> None:
        from ..scripts.import_kc_catalog import run

        curated = FIX.parent.parent.parent / "crawler" / "identity" / "data" / "catalog_seed.json"
        with tempfile.TemporaryDirectory() as tmp:
            curated_copy = Path(tmp) / "curated.json"
            curated_copy.write_text(json.dumps({"products": MergeWithCuratedTest.CURATED}, ensure_ascii=False), encoding="utf-8")

            entries, report = run([SAMPLE], curated_path=curated_copy, aliases_path=FIX / "kc_aliases_sample.csv")
            out = Path(tmp) / "catalog_kc.json"
            write_catalog(out, entries)
            catalog = Catalog.load(out)

            self.assertTrue(curated.exists())
            self.assertEqual(report["records"], 10)
            self.assertIn("curated:testbuds", {e.id for e in catalog._entries})
            self.assertGreater(report["output_entries"], 3)
            # 시드 전체를 복사하지 않는다: 시드 항목 중 이어지지 않은 것은 출력에 없다
            self.assertNotIn("logitech:mx-master-3s", {e.id for e in catalog._entries})

    def test_검수본_없이도_KC_항목만_만든다(self) -> None:
        from ..scripts.import_kc_catalog import run

        entries, report = run([SAMPLE])

        self.assertTrue(all(e["source"] == "kc" for e in entries))
        self.assertEqual(report["output_entries"], len(entries))


class ExportCsvTest(unittest.TestCase):
    def test_라벨링용_CSV는_id_열이_비어_있고_평가_파일_형식과_같다(self) -> None:
        from ..scripts.eval_product_identity import load_labeled
        from ..scripts.export_unresolved_titles import build_template, write_csv

        template = build_template(["로지텍 M590 무선 마우스"] * 2 + ["로지텍 MX Master 마우스"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "to_label.csv"
            write_csv(path, template)

            header = path.read_text(encoding="utf-8-sig").splitlines()[0]
            rows = load_labeled(path)

        self.assertEqual(header.split(",")[:4], ["title", "id", "kind", "note"])
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["id"] is None for r in rows))


class DoubleAbsorbTest(unittest.TestCase):
    def test_별칭_두_줄이_같은_KC_항목을_가리켜도_한_번만_흡수한다(self) -> None:
        records, _ = read_kc_records(SAMPLE)
        built = build_entries(records, LEX)
        curated = [dict(MergeWithCuratedTest.CURATED[0])]

        merged = merge_with_curated(
            built.entries, curated,
            [("curated:testbuds", "SM-T510"), ("curated:testbuds", "SM-T510NZKAKOO")],  # 같은 KC 항목의 기본모델과 파생모델
        )

        self.assertEqual(len(merged.report["absorbed"]), 1)
        self.assertEqual(merged.entries[0]["aliases"].count("SM-T510"), 1)
