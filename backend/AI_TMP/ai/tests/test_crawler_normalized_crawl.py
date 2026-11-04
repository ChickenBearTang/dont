"""HotDealCrawler.crawl_normalized 와 가격 파서 단일화 테스트."""

from __future__ import annotations

from pathlib import Path
import unittest

from ..crawler import HotDealCrawler, UnknownSiteError
from ..crawler.adapters import QuasarzoneAdapter
from ..crawler.schema import FieldStatus
from ..price_engine.normalizer import _to_int
from ..xai.features import FeatureExtractor

FIXTURE = Path(__file__).parent / "fixtures" / "crawler" / "quasarzone_listing.html"


def _fetch_fixture(url: str) -> str:
    return FIXTURE.read_text(encoding="utf-8")


class CrawlNormalizedTest(unittest.TestCase):
    def test_도메인으로_어댑터를_찾아_정규화하고_품질을_점검한다(self) -> None:
        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=_fetch_fixture)

        result = crawler.crawl_normalized()

        self.assertEqual(result.site_id, "quasarzone")
        self.assertEqual(len(result.deals), 6)
        self.assertTrue(result.quality.ok, result.quality)
        prices = {d.url.rsplit("/", 1)[-1]: d.price_krw for d in result.deals}
        self.assertEqual(prices["1001"], 21_200)
        self.assertEqual(prices["1006"], 210_000)
        self.assertIsNone(prices["1003"])

    def test_마크업이_바뀌면_품질_이상으로_드러난다(self) -> None:
        drifted = FIXTURE.read_text(encoding="utf-8").replace("text-orange", "price-new")
        crawler = HotDealCrawler(
            source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=lambda url: drifted
        )

        result = crawler.crawl_normalized()

        self.assertFalse(result.quality.ok)
        self.assertIn("LOW_PRICE_RATE", result.quality.issues)

    def test_등록되지_않은_사이트는_다른_파서로_읽지_않는다(self) -> None:
        crawler = HotDealCrawler(source_url="https://example.com/list", fetch=_fetch_fixture)

        with self.assertRaises(UnknownSiteError):
            crawler.crawl_normalized()

    def test_어댑터를_직접_줄_수_있다(self) -> None:
        crawler = HotDealCrawler(source_url="https://source.test/list", fetch=_fetch_fixture)

        result = crawler.crawl_normalized(adapter=QuasarzoneAdapter())

        self.assertEqual(result.site_id, "quasarzone")

    def test_가격이_없는_글은_누락으로_남는다(self) -> None:
        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=_fetch_fixture)

        result = crawler.crawl_normalized()

        missing = [d for d in result.deals if d.price_field == FieldStatus.MISSING]
        self.assertEqual(len(missing), 1)

    def test_기존_crawl은_바뀌지_않았다(self) -> None:
        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=_fetch_fixture)

        result = crawler.crawl()

        self.assertEqual(len(result.items), 6)
        self.assertEqual(result.items[0].price, "￦ 21,200 (KRW)")  # 원문 그대로


class SinglePriceParserTest(unittest.TestCase):
    """예전에는 두 곳에 복사돼 있었다. 이제 두 진입점이 같은 값을 내야 한다."""

    CASES = [
        "￦ 1,000 (KRW)", "21,200", "5% 할인 21,200원", "10,000원 ~ 12,000원", "$12.99",
        "2개 39,000원", "무료배송", "1.5만원", "21만원", "가격 미정", None, "",
    ]

    def test_두_진입점이_같은_값을_낸다(self) -> None:
        extractor = FeatureExtractor()
        for text in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(extractor.normalize_price_to_int(text), _to_int(text))

    def test_예전에_조용히_틀리던_값을_이제_맞게_읽거나_거부한다(self) -> None:
        extractor = FeatureExtractor()

        self.assertEqual(extractor.normalize_price_to_int("5% 할인 21,200원"), 21_200)  # 이전: 521200
        self.assertEqual(extractor.normalize_price_to_int("2개 39,000원"), 39_000)  # 이전: 239000
        self.assertEqual(extractor.normalize_price_to_int("21만원"), 210_000)  # 이전: 21
        self.assertIsNone(extractor.normalize_price_to_int("10,000원 ~ 12,000원"))  # 이전: 1000012000
        self.assertIsNone(extractor.normalize_price_to_int("$12.99"))  # 이전: 1299

    def test_무료배송은_배송비_0으로_읽힌다(self) -> None:
        """예전에는 None 이라 배송비가 무료인 글의 실질 가격(listed+shipping)이 통째로 비었다."""
        self.assertEqual(_to_int("무료배송"), 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
