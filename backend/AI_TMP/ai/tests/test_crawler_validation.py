"""크롤 결과 한 건의 오염 검증 테스트.

가격 파서가 조용히 틀린 값을 만들었던 것처럼(5% 할인 21,200원 -> 521200), 수집 단계에서
값이 오염되면 뒤의 모델이 전부 오염된다. 의심스러운 값은 격리하고 이유를 남긴다.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from ..crawler import HotDealCrawler
from ..crawler.adapters import QuasarzoneAdapter
from ..crawler.identity import ProductResolver
from ..crawler.price import PriceStatus
from ..crawler.schema import FieldStatus, NormalizedDeal
from ..crawler.validation import Severity, validate_deal

NOW = datetime(2025, 3, 4, 5, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).parent / "fixtures" / "crawler" / "quasarzone_listing.html"


def deal(**override) -> NormalizedDeal:
    base = dict(
        site_id="quasarzone", title="로지텍 MX Master 3S", url="https://quasarzone.com/bbs/qb_saleinfo/views/1",
        price_krw=109_000, price_status=PriceStatus.PARSED, price_field=FieldStatus.PARSED, price_raw="109,000원",
        posted_at=NOW - timedelta(hours=3), posted_at_field=FieldStatus.PARSED, posted_at_raw="13:45", fetched_at=NOW,
    )
    base.update(override)
    return NormalizedDeal(**base)


def codes(d, severity=None):
    return {i.code for i in validate_deal(d, now=NOW) if severity is None or i.severity == severity}


class CleanDealTest(unittest.TestCase):
    def test_깨끗한_글은_이슈가_없다(self) -> None:
        self.assertEqual(validate_deal(deal(), now=NOW), [])


class TitleUrlTest(unittest.TestCase):
    def test_빈_제목_너무_짧은_제목_숫자뿐인_제목(self) -> None:
        self.assertIn("TITLE_EMPTY", codes(deal(title="  "), Severity.ERROR))
        self.assertIn("TITLE_TOO_SHORT", codes(deal(title="a"), Severity.WARNING))
        self.assertIn("TITLE_ONLY_DIGITS", codes(deal(title="12345"), Severity.WARNING))

    def test_URL이_http가_아니거나_호스트가_없다(self) -> None:
        for url in ("", "javascript:alert(1)", "/bbs/1", "ftp://x.com/a", "https:///nohost"):
            with self.subTest(url=url):
                self.assertIn("URL_INVALID", codes(deal(url=url), Severity.ERROR))


class PriceTest(unittest.TestCase):
    def test_가격이_의심스럽게_작다(self) -> None:
        self.assertIn("PRICE_SUSPICIOUSLY_LOW", codes(deal(price_krw=210), Severity.WARNING))

    def test_파서가_상한을_넘는다고_판정한_값은_오류다(self) -> None:
        d = deal(price_krw=None, price_status=PriceStatus.OUT_OF_RANGE, price_field=FieldStatus.UNPARSEABLE)

        self.assertIn("PRICE_OUT_OF_RANGE", codes(d, Severity.ERROR))

    def test_범위_외화는_경고다(self) -> None:
        for status, code in ((PriceStatus.AMBIGUOUS, "PRICE_AMBIGUOUS"), (PriceStatus.FOREIGN_CURRENCY, "PRICE_FOREIGN_CURRENCY")):
            with self.subTest(status=status):
                d = deal(price_krw=None, price_status=status, price_field=FieldStatus.UNPARSEABLE)
                self.assertIn(code, codes(d, Severity.WARNING))

    def test_무료는_0원으로_읽혀도_의심한다(self) -> None:
        d = deal(price_krw=0, price_status=PriceStatus.FREE)

        self.assertIn("PRICE_ZERO", codes(d, Severity.WARNING))

    def test_제목의_가격과_가격란이_크게_다르면_파싱_오류를_의심한다(self) -> None:
        """한쪽 파서가 틀렸을 때 서로 맞춰 보면 드러난다."""
        d = deal(title="로지텍 MX Master 3S (109,000원/무료배송)", price_krw=521_200)

        self.assertIn("PRICE_TITLE_MISMATCH", codes(d, Severity.WARNING))

    def test_제목의_가격과_가격란이_같으면_이슈가_없다(self) -> None:
        self.assertNotIn("PRICE_TITLE_MISMATCH", codes(deal(title="로지텍 MX Master 3S (109,000원)")))

    def test_제목에_금액이_여럿이면_비교하지_않는다(self) -> None:
        d = deal(title="정가 150,000원 -> 109,000원 로지텍 MX Master 3S", price_krw=109_000)

        self.assertNotIn("PRICE_TITLE_MISMATCH", codes(d))

    def test_작은_차이는_허용한다(self) -> None:
        self.assertNotIn("PRICE_TITLE_MISMATCH", codes(deal(title="로지텍 (109,500원)", price_krw=109_000)))


class DateTest(unittest.TestCase):
    def test_미래_날짜는_오류다(self) -> None:
        self.assertIn("POSTED_AT_FUTURE", codes(deal(posted_at=NOW + timedelta(days=3)), Severity.ERROR))

    def test_하루_이내의_미래는_시간대_오차로_본다(self) -> None:
        self.assertNotIn("POSTED_AT_FUTURE", codes(deal(posted_at=NOW + timedelta(hours=5))))

    def test_3년보다_오래된_글은_경고다(self) -> None:
        self.assertIn("POSTED_AT_TOO_OLD", codes(deal(posted_at=NOW - timedelta(days=365 * 4)), Severity.WARNING))

    def test_날짜가_없으면_이슈가_아니다(self) -> None:
        self.assertEqual(codes(deal(posted_at=None, posted_at_field=FieldStatus.MISSING)), set())


class CrawlIntegrationTest(unittest.TestCase):
    def _crawler(self, html=None):
        text = html if html is not None else FIXTURE.read_text(encoding="utf-8")
        return HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=lambda url: text)

    def test_이슈는_글마다_코드로_남는다(self) -> None:
        result = self._crawler().crawl_normalized()

        by_id = {d.url.rsplit("/", 1)[-1]: d for d in result.deals}
        self.assertIn("PRICE_AMBIGUOUS", by_id["1003"].issues)  # 범위 가격
        self.assertIn("PRICE_FOREIGN_CURRENCY", by_id["1004"].issues)
        self.assertEqual(by_id["1001"].issues, ())

    def test_오류_수준_글은_격리하고_나머지만_deals에_남긴다(self) -> None:
        html = FIXTURE.read_text(encoding="utf-8").replace("/bbs/qb_saleinfo/views/1002", "javascript:void(0)")
        result = self._crawler(html).crawl_normalized()

        self.assertEqual(len(result.quarantined), 1)
        self.assertIn("URL_INVALID", result.quarantined[0].issues)
        self.assertEqual(len(result.deals) + len(result.quarantined), 6)  # 글이 사라지지 않고 분리만 된다
        self.assertTrue(all(not any(i == "URL_INVALID" for i in d.issues) for d in result.deals))

    def test_품질_점검은_격리된_글까지_포함해_센다(self) -> None:
        result = self._crawler().crawl_normalized()

        self.assertEqual(result.quality.stats["items"], len(result.deals) + len(result.quarantined))


class IdentityIntegrationTest(unittest.TestCase):
    def test_resolver를_주면_글마다_식별_결과가_붙는다(self) -> None:
        html = (
            '<div class="market-info-list"><a href="/bbs/qb_saleinfo/views/9" class="subject-link ">'
            '로지텍 MX Master 3S 무선 마우스</a></div>'
        )
        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=lambda url: html)

        result = crawler.crawl_normalized(resolver=ProductResolver())

        self.assertEqual(result.deals[0].identity.canonical_id, "logitech:mx-master-3s")

    def test_resolver를_주지_않으면_식별하지_않는다(self) -> None:
        crawler = HotDealCrawler(
            source_url="https://quasarzone.com/bbs/qb_saleinfo",
            fetch=lambda url: FIXTURE.read_text(encoding="utf-8"),
        )

        self.assertIsNone(crawler.crawl_normalized().deals[0].identity)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
