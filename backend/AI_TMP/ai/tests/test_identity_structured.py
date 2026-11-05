"""상품 페이지 구조화 데이터 추출과 LLM 환각 방어 테스트."""

from __future__ import annotations

from pathlib import Path
import unittest
import unittest.mock

from ..crawler.identity import (
    BrandLexicon,
    GeminiExtractor,
    IdentityStatus,
    ProductResolver,
    extract_structured_product,
    verify_llm_candidate,
)

FIX = Path(__file__).parent / "fixtures" / "crawler"
R = IdentityStatus


def read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class StructuredExtractionTest(unittest.TestCase):
    def test_JSON_LD의_graph와_배열_type에서_Product를_찾는다(self) -> None:
        product = extract_structured_product(read("merchant_jsonld.html"))

        self.assertTrue(product.found)
        self.assertEqual(product.gtin, "04006381333931")
        self.assertEqual(product.brand, "Logitech")  # {"name": ...} 객체에서
        self.assertEqual(product.mpn, "910-006556")
        self.assertIn("json-ld", product.sources)

    def test_체크_숫자가_틀린_GTIN은_버리고_이유를_남긴다(self) -> None:
        product = extract_structured_product(read("merchant_bad_gtin.html"))

        self.assertIsNone(product.gtin)
        self.assertEqual(product.mpn, "910-006556")
        self.assertTrue(any("gtin13" in r for r in product.rejected))

    def test_microdata도_읽는다(self) -> None:
        product = extract_structured_product(read("merchant_microdata.html"))

        self.assertEqual(product.gtin, "04006381333931")
        self.assertEqual(product.brand, "Razer")
        self.assertEqual(product.mpn, "RZ01-04630100-R3A1")
        self.assertIn("microdata", product.sources)

    def test_깨진_JSON_LD는_죽지_않고_기록한다(self) -> None:
        product = extract_structured_product('<script type="application/ld+json">{not json</script>')

        self.assertFalse(product.found)
        self.assertTrue(product.rejected)

    def test_빈_입력과_구조화_데이터가_없는_페이지(self) -> None:
        for html in ("", "<html><body>그냥 글</body></html>", None):
            with self.subTest(html=html):
                self.assertFalse(extract_structured_product(html).found)  # type: ignore[arg-type]

    def test_Product가_아닌_JSON_LD는_무시한다(self) -> None:
        html = '<script type="application/ld+json">{"@type": "Organization", "name": "X", "gtin13": "4006381333931"}</script>'

        self.assertFalse(extract_structured_product(html).found)


class ResolverWithPageTest(unittest.TestCase):
    def test_유효한_GTIN이_있으면_제목보다_우선한다(self) -> None:
        identity = ProductResolver().resolve("로지텍 MX Master 3S", page_html=read("merchant_jsonld.html"))

        self.assertEqual(identity.status, R.RESOLVED_GTIN)
        self.assertEqual(identity.canonical_id, "gtin:04006381333931")
        self.assertGreaterEqual(identity.confidence, 0.99)
        self.assertEqual(identity.brand, "logitech")

    def test_제목이_모호해도_페이지의_GTIN으로_식별된다(self) -> None:
        identity = ProductResolver().resolve("로지텍 MX Master 마우스 특가", page_html=read("merchant_jsonld.html"))

        self.assertEqual(identity.status, R.RESOLVED_GTIN)

    def test_GTIN이_틀리면_브랜드와_MPN으로_식별하고_경고한다(self) -> None:
        identity = ProductResolver().resolve("어떤 마우스", page_html=read("merchant_bad_gtin.html"))

        self.assertEqual(identity.status, R.RESOLVED_MPN)
        self.assertEqual(identity.canonical_id, "mpn:logitech:910006556")
        self.assertTrue(any(w.startswith("STRUCTURED_REJECTED") for w in identity.warnings))

    def test_MPN만_있고_브랜드가_없으면_식별하지_않는다(self) -> None:
        html = '<script type="application/ld+json">{"@type": "Product", "mpn": "910-006556"}</script>'

        identity = ProductResolver().resolve("어떤 마우스", page_html=html)

        self.assertNotEqual(identity.status, R.RESOLVED_MPN)  # 부품번호만으로는 제조사 간 충돌 가능

    def test_페이지가_없으면_제목만으로_식별한다(self) -> None:
        self.assertEqual(ProductResolver().resolve("로지텍 MX Master 3S").status, R.RESOLVED_CATALOG)


class FakeLlm:
    def __init__(self, result):
        self.result, self.calls = result, []

    def extract(self, title):
        self.calls.append(title)
        return self.result


class LlmGuardTest(unittest.TestCase):
    lex = BrandLexicon.load()

    def test_제목에_그대로_있는_모델은_통과한다(self) -> None:
        ok, _ = verify_llm_candidate("로지텍 M590 무선 마우스", "logitech", "M590", self.lex)

        self.assertTrue(ok)

    def test_LLM이_비슷한_다른_모델로_바꾸면_거부한다(self) -> None:
        """MX Master 3S 를 MX Master 4 로 바꿔 쓰는 환각."""
        ok, reason = verify_llm_candidate("로지텍 MX Master 3S", "logitech", "MX Master 4", self.lex)

        self.assertFalse(ok)
        self.assertEqual(reason, "model_not_in_title")

    def test_제목에_없는_모델을_지어내면_거부한다(self) -> None:
        self.assertFalse(verify_llm_candidate("로지텍 마우스 할인", "logitech", "G502", self.lex)[0])

    def test_브랜드가_근거_없으면_거부한다(self) -> None:
        self.assertFalse(verify_llm_candidate("M590 무선 마우스", "아무개전자", "M590", self.lex)[0])

    def test_모델이_비었거나_문자열이_아니면_거부한다(self) -> None:
        for model in (None, "", "   ", 590):
            with self.subTest(model=model):
                self.assertFalse(verify_llm_candidate("로지텍 M590", "logitech", model, self.lex)[0])

    def test_모델이_다른_토큰의_앞부분이면_거부한다(self) -> None:
        self.assertFalse(verify_llm_candidate("로지텍 G3040 마우스", "logitech", "G304", self.lex)[0])


class ResolverWithLlmTest(unittest.TestCase):
    def test_규칙이_못_푼_제목을_LLM이_추출하면_검증_후_미검증_상태로_받는다(self) -> None:
        llm = FakeLlm({"brand": "Xyz", "model": "Foo-77"})
        identity = ProductResolver(llm=llm).resolve("신상 Xyz Foo-77 무선 이어폰 입고")

        self.assertEqual(identity.status, R.UNVERIFIED_MODEL)
        self.assertEqual(identity.source, "llm")
        self.assertFalse(identity.trusted)
        self.assertIsNone(identity.canonical_id)  # LLM 은 신뢰 식별로 올리지 않는다
        self.assertLessEqual(identity.confidence, 0.6)

    def test_환각이면_거부하고_이유를_남긴다(self) -> None:
        llm = FakeLlm({"brand": "logitech", "model": "G999"})
        identity = ProductResolver(llm=llm).resolve("로지텍 이어폰 신상 입고")

        self.assertEqual(identity.status, R.BRAND_ONLY)
        self.assertNotEqual(identity.source, "llm")
        self.assertTrue(any(w.startswith("LLM_REJECTED") for w in identity.warnings), identity.warnings)

    def test_규칙이_풀면_LLM을_부르지_않는다(self) -> None:
        llm = FakeLlm({"brand": "logitech", "model": "G304"})
        ProductResolver(llm=llm).resolve("로지텍 MX Master 3S")

        self.assertEqual(llm.calls, [])

    def test_카탈로그에_있는데_LLM이_다르게_말해도_카탈로그가_이긴다(self) -> None:
        llm = FakeLlm({"brand": "logitech", "model": "MX Master 4"})
        identity = ProductResolver(llm=llm).resolve("로지텍 MX Master 3S")

        self.assertEqual(identity.canonical_id, "logitech:mx-master-3s")

    def test_LLM이_None이나_이상한_값을_돌려줘도_죽지_않는다(self) -> None:
        for result in (None, "text", 5, {}, {"brand": None, "model": None}):
            with self.subTest(result=result):
                identity = ProductResolver(llm=FakeLlm(result)).resolve("로지텍 마우스")
                self.assertEqual(identity.status, R.BRAND_ONLY)


class GeminiExtractorTest(unittest.TestCase):
    """실제 API 는 호출하지 못했다. 요청 구성과 응답 해석만 가짜 HTTP 로 확인한다."""

    def test_키가_없으면_호출하지_않는다(self) -> None:
        calls = []
        extractor = GeminiExtractor(api_key="", post=lambda *a: calls.append(a) or {})

        with unittest.mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            self.assertIsNone(extractor.extract("제목"))
        self.assertEqual(calls, [])

    def test_요청에_제목과_온도_0과_JSON_응답을_담고_응답을_해석한다(self) -> None:
        seen = {}

        def post(url, body, timeout):
            seen.update(url=url, body=body, timeout=timeout)
            return {"candidates": [{"content": {"parts": [{"text": '{"brand": "Razer", "model": "DeathAdder V3"}'}]}}]}

        result = GeminiExtractor(api_key="k", post=post).extract("레이저 DeathAdder V3 마우스")

        self.assertEqual(result, {"brand": "Razer", "model": "DeathAdder V3"})
        self.assertIn("gemini-2.5-flash:generateContent", seen["url"])
        self.assertEqual(seen["body"]["generationConfig"]["temperature"], 0)
        self.assertEqual(seen["body"]["generationConfig"]["responseMimeType"], "application/json")
        self.assertIn("레이저 DeathAdder V3 마우스", seen["body"]["contents"][0]["parts"][0]["text"])

    def test_네트워크_오류와_깨진_응답은_모름으로_처리한다(self) -> None:
        def boom(*a):
            raise OSError("down")

        self.assertIsNone(GeminiExtractor(api_key="k", post=boom).extract("x"))
        self.assertIsNone(GeminiExtractor(api_key="k", post=lambda *a: {"unexpected": 1}).extract("x"))
        bad_json = {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
        self.assertIsNone(GeminiExtractor(api_key="k", post=lambda *a: bad_json).extract("x"))
        listy = {"candidates": [{"content": {"parts": [{"text": "[1,2]"}]}}]}
        self.assertIsNone(GeminiExtractor(api_key="k", post=lambda *a: listy).extract("x"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
