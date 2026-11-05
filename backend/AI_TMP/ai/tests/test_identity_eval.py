"""상품 식별 평가 세트와 평가 스크립트 테스트."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from ..crawler.identity import Catalog, ProductResolver
from ..scripts.eval_product_identity import DEFAULT_LABELED, evaluate, summarize

DATA = json.loads(DEFAULT_LABELED.read_text(encoding="utf-8"))
ROWS = DATA["rows"]


class LabeledSetIntegrityTest(unittest.TestCase):
    def test_정답_id는_모두_카탈로그에_있다(self) -> None:
        catalog = Catalog.load()
        for row in ROWS:
            if row["id"] is not None:
                self.assertIsNotNone(catalog.get(row["id"]), row)

    def test_제목이_중복되지_않는다(self) -> None:
        titles = [r["title"] for r in ROWS]
        self.assertEqual(len(titles), len(set(titles)))

    def test_적대적_사례는_정답이_null이고_이유가_있다(self) -> None:
        adversarial = [r for r in ROWS if r["kind"] == "adversarial"]

        self.assertGreaterEqual(len(adversarial), 20)
        for row in adversarial:
            self.assertIsNone(row["id"])
            self.assertTrue(row.get("note"), row["title"])

    def test_합성_세트임을_파일이_밝힌다(self) -> None:
        self.assertIn("합성", DATA["_comment"])
        self.assertIn("실전 정확도가 아니다", DATA["_comment"])


class EvaluateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = evaluate(ROWS)

    def test_오병합이_없다(self) -> None:
        """이 프로젝트가 지키려는 단 하나의 성질: 다른 상품을 같은 상품으로 합치지 않는다."""
        self.assertEqual(self.result["false_merge"], 0, self.result["false_merges"])

    def test_적대적_사례에서_신뢰_식별이_하나도_나오지_않는다(self) -> None:
        resolver = ProductResolver()
        for row in ROWS:
            if row["kind"] == "adversarial":
                with self.subTest(title=row["title"]):
                    self.assertFalse(resolver.resolve(row["title"]).trusted, row["note"])

    def test_정밀도가_1이다(self) -> None:
        self.assertEqual(self.result["precision"], 1.0)

    def test_재현율_한계가_사례로_드러난다(self) -> None:
        """정밀도를 위해 확정을 포기한 사례를 숨기지 않고 보고한다."""
        missed_titles = [m["title"] for m in self.result["missed"]]

        self.assertTrue(any("1세대" in t for t in missed_titles))

    def test_같은_입력은_같은_결과다(self) -> None:
        self.assertEqual(evaluate(ROWS), self.result)

    def test_평가_함수는_오병합을_실제로_센다(self) -> None:
        """평가기가 항상 0을 내는 고장 난 척도가 아닌지: 일부러 틀린 정답을 주면 오병합으로 잡혀야 한다."""
        wrong = [{"kind": "easy", "title": "로지텍 MX Master 3S 무선 마우스", "id": "logitech:mx-master-4"}]

        result = evaluate(wrong)

        self.assertEqual(result["false_merge"], 1)
        self.assertEqual(result["false_merges"][0]["got"], "logitech:mx-master-3s")

    def test_정답이_null인데_신뢰_식별이_나오면_오병합이다(self) -> None:
        result = evaluate([{"kind": "adversarial", "title": "로지텍 MX Master 3S", "id": None}])

        self.assertEqual(result["false_merge"], 1)

    def test_놓침과_올바른_거부를_구분한다(self) -> None:
        result = evaluate([
            {"kind": "easy", "title": "로지텍 마우스 할인", "id": "logitech:g304"},
            {"kind": "adversarial", "title": "오늘의 핫딜 모음", "id": None},
        ])

        self.assertEqual(result["counts"], {"missed": 1, "correct_refusal": 1})

    def test_요약에_합성_경고가_들어간다(self) -> None:
        text = summarize(self.result, synthetic=True)

        self.assertIn("낙관적", text)
        self.assertIn("오병합 0", text)
        self.assertNotIn("낙관적", summarize(self.result, synthetic=False))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class ExportTemplateTest(unittest.TestCase):
    def test_신뢰_식별이_된_제목은_빼고_모호한_제목만_많이_나온_순으로_낸다(self) -> None:
        from ..scripts.export_unresolved_titles import build_template

        titles = (
            ["로지텍 MX Master 3S"] * 5                      # 신뢰 식별 -> 빠진다
            + ["로지텍 M590 무선 마우스"] * 3                  # 카탈로그에 없음 -> 나온다
            + ["로지텍 MX Master 마우스"] * 1                  # 버전 모호 -> 나온다
            + ["로지텍  m590   무선 마우스"] * 2               # 같은 제목(공백/대소문자 차이) -> 합쳐진다
        )

        template = build_template(titles)

        self.assertEqual(template["summary"], {"unique_titles": 3, "trusted": 1, "to_label": 2})
        self.assertEqual([r["seen"] for r in template["rows"]], [5, 1])
        self.assertEqual(template["rows"][0]["resolver_status"], "unverified_model")
        self.assertEqual(template["rows"][1]["resolver_status"], "ambiguous_variant")
        self.assertIsNone(template["rows"][0]["id"])

    def test_JSONL과_CSV를_읽는다(self) -> None:
        import csv
        import tempfile

        from ..scripts.export_unresolved_titles import read_titles

        with tempfile.TemporaryDirectory() as tmp:
            jsonl = Path(tmp) / "t.jsonl"
            jsonl.write_text('{"title": "A"}\n\n{"title": "B"}\n{"x": 1}\n', encoding="utf-8")
            csv_path = Path(tmp) / "t.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "title"])
                writer.writerow([1, "C"])

            self.assertEqual(read_titles(jsonl), ["A", "B"])
            self.assertEqual(read_titles(csv_path), ["C"])


class PriceEngineIntegrationTest(unittest.TestCase):
    """price_engine 의 상품 ID: 신뢰하는 식별만 쓰고, 아니면 예전 방식 그대로."""

    def _observe(self, title, resolver=None):
        from datetime import datetime, timezone

        from ..price_engine.normalizer import merge_to_price_observation
        from ..price_engine.schema_models import RawListing

        listing = RawListing(
            source_site="quasarzone", post_url="https://quasarzone.com/bbs/qb_saleinfo/views/1", post_id_raw="1",
            title_raw=title, merchant_raw_hint=None, category_raw="mouse", price_raw="109,000원", shipping_raw="무료배송",
            created_at_raw=None, crawled_at=datetime(2025, 3, 4, tzinfo=timezone.utc), html_hash="h",
        )
        return merge_to_price_observation(
            listing, None, None, observed_at=datetime(2025, 3, 4, tzinfo=timezone.utc), identity_resolver=resolver
        )

    def test_resolver를_주지_않으면_예전과_같다(self) -> None:
        obs = self._observe("로지텍 MX Master 3S 무선 마우스")

        self.assertTrue(obs.canonical_product_id_candidate.startswith("title-hash:"))
        self.assertIsNone(obs.brand)

    def test_신뢰하는_식별은_상품_ID와_브랜드로_쓴다(self) -> None:
        obs = self._observe("로지텍 MX Master 3S 무선 마우스", ProductResolver())

        self.assertEqual(obs.canonical_product_id_candidate, "logitech:mx-master-3s")
        self.assertEqual(obs.brand, "logitech")

    def test_표기가_달라도_같은_상품이면_같은_ID다(self) -> None:
        """제목 해시는 표기가 다르면 다른 상품이 된다. 식별은 같은 상품으로 묶는다."""
        a = self._observe("[쿠팡] 로지텍 MX Master 3S (109,000원)", ProductResolver())
        b = self._observe("Logitech MX-Master-3S 블랙", ProductResolver())

        self.assertEqual(a.canonical_product_id_candidate, b.canonical_product_id_candidate)
        self.assertNotEqual(self._observe("[쿠팡] 로지텍 MX Master 3S (109,000원)").canonical_product_id_candidate,
                            self._observe("Logitech MX-Master-3S 블랙").canonical_product_id_candidate)

    def test_다른_모델은_다른_ID다(self) -> None:
        a = self._observe("로지텍 MX Master 3S", ProductResolver())
        b = self._observe("로지텍 MX Master 4", ProductResolver())

        self.assertNotEqual(a.canonical_product_id_candidate, b.canonical_product_id_candidate)

    def test_신뢰하지_못하는_식별은_예전_방식으로_돌아간다(self) -> None:
        obs = self._observe("로지텍 MX Keys Mini 키보드", ProductResolver())  # 변형어 때문에 확정 안 됨

        self.assertTrue(obs.canonical_product_id_candidate.startswith("title-hash:"))
        self.assertIsNone(obs.brand)
