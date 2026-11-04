"""카탈로그 색인: 수만 건이 되어도 제목 하나를 빠르게 매칭하고, 결과는 전수 탐색과 같아야 한다.

KC 인증 DB 를 가져오면 카탈로그가 수만~수십만 건이 된다. 제목마다 전체를 훑으면 수집량
(하루 300건 이상)에 비해 너무 느려진다. 색인은 속도만 바꾸고 결과는 바꾸지 않아야 한다.
"""

from __future__ import annotations

import time
import unittest

from ..crawler.identity import Catalog
from ..crawler.identity.catalog import CatalogEntry


def synthetic_entries(n: int) -> list[CatalogEntry]:
    return [
        CatalogEntry(
            id=f"kc:brand{i % 50}:ab{i:06d}", brand=f"brand{i % 50}", line="", model=f"AB-{i:06d}", category="x",
            requires_brand=False,
        )
        for i in range(n)
    ]


class IndexEquivalenceTest(unittest.TestCase):
    def test_시드_카탈로그의_결과가_전수_탐색과_같다(self) -> None:
        """색인 도입 전의 구현(모든 항목을 훑음)을 기준 구현으로 두고 비교한다."""
        from ..crawler.identity.text import compact, find_on_boundaries, tokenize

        catalog = Catalog.load()
        titles = [
            "로지텍 MX Master 3S 무선 마우스", "RTX 4070 SUPER 그래픽카드", "RTX 4070 Ti SUPER", "에어팟 프로 2 / 에어팟 4 세트",
            "갤럭시 버즈2 프로 SM-R510", "로지텍 MX Master 마우스", "오늘의 핫딜", "삼성 갤럭시 버즈2", "G304 G305 묶음",
        ]
        for title in titles:
            with self.subTest(title=title):
                haystack = compact(tokenize(title))
                expected_ids = set()
                for entry in catalog._entries:
                    if any(find_on_boundaries(haystack, code) for code in entry.codes):
                        expected_ids.add(entry.id)
                match = catalog.match(title)
                got = {e.id for e in match.candidates} if match.status in ("match", "multiple_products") else set()
                if match.status == "match":
                    self.assertIn(match.entry.id, expected_ids)
                if match.status == "multiple_products":
                    self.assertTrue(got <= expected_ids)


class PerformanceTest(unittest.TestCase):
    def test_5만_건_카탈로그에서_제목_500개를_수_초_안에_매칭한다(self) -> None:
        catalog = Catalog(synthetic_entries(50_000))
        titles = [f"브랜드 제품 AB-{i * 97 % 50_000:06d} 무선 마우스 (29,900원)" for i in range(500)]

        started = time.perf_counter()
        results = [catalog.match(t) for t in titles]
        elapsed = time.perf_counter() - started

        self.assertTrue(all(r.status == "match" for r in results))
        self.assertLess(elapsed, 3.0, f"{elapsed:.2f}s")

    def test_색인은_정확한_코드만_찾는다(self) -> None:
        catalog = Catalog(synthetic_entries(1000))

        self.assertEqual(catalog.match("AB-000007").entry.id, "kc:brand7:ab000007")
        self.assertEqual(catalog.match("AB-0000070").status, "none")  # 한 글자 더 붙은 코드는 다른 코드
        self.assertEqual(catalog.match("XAB-000007").status, "none")


class RequiresBrandTest(unittest.TestCase):
    def test_브랜드_필수_항목은_브랜드가_제목에_있을_때만_맞춘다(self) -> None:
        short = CatalogEntry("kc:acme:k2", "acme", "", "K2", "kb", requires_brand=True)
        catalog = Catalog([short])

        self.assertEqual(catalog.match("K2 키보드").status, "none")
        self.assertEqual(catalog.match("ACME K2 키보드", brands=["acme"]).status, "match")

    def test_브랜드_필수가_아니면_브랜드_없이도_맞춘다(self) -> None:
        entry = CatalogEntry("kc:acme:x9000", "acme", "", "X9000", "kb", requires_brand=False)

        self.assertEqual(Catalog([entry]).match("X9000 키보드").status, "match")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class TokenSpansTest(unittest.TestCase):
    def test_구간은_토큰_경계에서만_만들고_최대_길이를_넘기지_않는다(self) -> None:
        from ..crawler.identity.catalog import _token_spans

        spans = list(_token_spans(["mx", "master", "3s"], max_len=8))

        self.assertEqual(
            [(s, e, t) for s, e, t in spans],
            [(0, 2, "mx"), (0, 8, "mxmaster"), (2, 8, "master"), (2, 10, "master3s"), (8, 10, "3s")],
        )

    def test_최대_길이를_넘는_구간은_만들지_않는다(self) -> None:
        from ..crawler.identity.catalog import _token_spans

        texts = [t for _, _, t in _token_spans(["aaaa", "bbbb", "cccc", "dddd"], max_len=8)]

        self.assertNotIn("aaaabbbbcccc", texts)
        self.assertIn("aaaabbbb", texts)
        self.assertEqual(max(len(t) for t in texts), 8)
