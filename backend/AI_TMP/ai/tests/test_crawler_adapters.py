"""사이트 어댑터 / 정규화 / 레지스트리 / 품질 점검 테스트.

픽스처(fixtures/crawler/quasarzone_listing.html)는 파서가 읽는 마크업을 따라 만든 합성본이다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from ..crawler.adapters import QuasarzoneAdapter
from ..crawler.dates import KST, parse_posted_at
from ..crawler.price import PriceStatus
from ..crawler.quality import assess_batch
from ..crawler.registry import AdapterRegistry, UnknownSiteError, default_registry
from ..crawler.schema import FieldStatus, SiteCapabilities

FIXTURE = Path(__file__).parent / "fixtures" / "crawler" / "quasarzone_listing.html"
# 2025-03-04 14:00 KST
NOW = datetime(2025, 3, 4, 14, 0, tzinfo=KST).astimezone(timezone.utc)


def _normalized():
    adapter = QuasarzoneAdapter()
    deals = adapter.parse_listing(FIXTURE.read_text(encoding="utf-8"))
    return adapter, deals, [adapter.normalize(d, fetched_at=NOW) for d in deals]


class ParseListingTest(unittest.TestCase):
    def test_중복_URL과_링크_없는_블록은_걸러진다(self) -> None:
        _, deals, _ = _normalized()

        self.assertEqual(len(deals), 6)
        self.assertEqual(len({d.url for d in deals}), 6)
        self.assertEqual(deals[0].url, "https://quasarzone.com/bbs/qb_saleinfo/views/1001")
        self.assertEqual(deals[0].title, "[마우스] 로지텍 G304")  # 먼저 나온 글이 남는다


class NormalizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter, cls.deals, cls.normalized = _normalized()
        cls.by_id = {n.url.rsplit("/", 1)[-1]: n for n in cls.normalized}

    def test_전각_원화_표기를_읽는다(self) -> None:
        n = self.by_id["1001"]
        self.assertEqual((n.price_krw, n.price_field), (21_200, FieldStatus.PARSED))

    def test_수량이_붙은_가격에서_수량을_빼고_읽는다(self) -> None:
        self.assertEqual(self.by_id["1002"].price_krw, 39_000)

    def test_범위_가격은_값을_만들지_않고_이유를_남긴다(self) -> None:
        n = self.by_id["1003"]
        self.assertIsNone(n.price_krw)
        self.assertEqual(n.price_status, PriceStatus.AMBIGUOUS)
        self.assertEqual(n.price_field, FieldStatus.UNPARSEABLE)
        self.assertEqual(n.price_raw, "10,000원 ~ 12,000원")

    def test_외화는_원화로_추측하지_않는다(self) -> None:
        n = self.by_id["1004"]
        self.assertIsNone(n.price_krw)
        self.assertEqual(n.price_status, PriceStatus.FOREIGN_CURRENCY)

    def test_가격이_아예_없으면_누락이다(self) -> None:
        n = self.by_id["1005"]
        self.assertEqual((n.price_krw, n.price_field), (None, FieldStatus.MISSING))

    def test_할인율과_만원_단위가_섞여도_읽는다(self) -> None:
        self.assertEqual(self.by_id["1006"].price_krw, 210_000)

    def test_날짜_형식별로_UTC로_바뀐다(self) -> None:
        self.assertEqual(
            self.by_id["1001"].posted_at, datetime(2025, 3, 4, 13, 45, tzinfo=KST).astimezone(timezone.utc)
        )
        self.assertEqual(self.by_id["1002"].posted_at, datetime(2025, 3, 3, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(self.by_id["1003"].posted_at, datetime(2025, 3, 2, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(self.by_id["1004"].posted_at, datetime(2025, 3, 1, 15, 0, tzinfo=timezone.utc))

    def test_읽을_수_없는_날짜는_값을_만들지_않는다(self) -> None:
        n = self.by_id["1005"]
        self.assertIsNone(n.posted_at)
        self.assertEqual(n.posted_at_field, FieldStatus.UNPARSEABLE)

    def test_날짜가_없으면_누락이다(self) -> None:
        self.assertEqual(self.by_id["1006"].posted_at_field, FieldStatus.MISSING)

    def test_수집_시각과_사이트_ID가_붙는다(self) -> None:
        n = self.by_id["1001"]
        self.assertEqual(n.site_id, "quasarzone")
        self.assertEqual(n.fetched_at, NOW)


class NotProvidedTest(unittest.TestCase):
    """가격을 주지 않는 사이트: '비어 있음'과 '누락'을 구분해야 한다."""

    def test_사이트가_주지_않는_필드는_NOT_PROVIDED다(self) -> None:
        class NoPriceSite(QuasarzoneAdapter):
            site_id = "nopricesite"
            capabilities = SiteCapabilities(provides_price=False, provides_posted_at=False)

        adapter = NoPriceSite()
        deal = adapter.parse_listing(FIXTURE.read_text(encoding="utf-8"))[0]

        n = adapter.normalize(deal, fetched_at=NOW)

        self.assertIsNone(n.price_krw)
        self.assertEqual(n.price_field, FieldStatus.NOT_PROVIDED)
        self.assertEqual(n.posted_at_field, FieldStatus.NOT_PROVIDED)


class PostedAtTest(unittest.TestCase):
    def test_연도_없는_날짜가_미래면_작년이다(self) -> None:
        result = parse_posted_at("12-31", now=NOW)  # 오늘이 3월 4일이므로 12월 31일은 작년

        self.assertEqual(result.value, datetime(2024, 12, 31, tzinfo=KST).astimezone(timezone.utc))

    def test_시각만_있고_지금보다_늦으면_어제다(self) -> None:
        result = parse_posted_at("23:30", now=NOW)  # 지금 14:00 KST

        self.assertEqual(result.value, datetime(2025, 3, 3, 23, 30, tzinfo=KST).astimezone(timezone.utc))

    def test_존재하지_않는_날짜는_거부한다(self) -> None:
        for text in ("13-40", "2025-02-30", "25:00", "어제", "방금 전"):
            with self.subTest(text=text):
                self.assertEqual(parse_posted_at(text, now=NOW).field, FieldStatus.UNPARSEABLE)

    def test_시간대_없는_now는_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            parse_posted_at("03-04", now=datetime(2025, 3, 4, 14, 0))


class RegistryTest(unittest.TestCase):
    def test_도메인으로_어댑터를_찾는다(self) -> None:
        registry = default_registry()

        self.assertEqual(registry.adapter_for_url("https://quasarzone.com/bbs/qb_saleinfo/views/1").site_id, "quasarzone")
        self.assertEqual(registry.adapter_for_url("https://m.quasarzone.com/x").site_id, "quasarzone")  # 하위 도메인

    def test_비슷한_이름의_다른_도메인은_찾지_않는다(self) -> None:
        with self.assertRaises(UnknownSiteError):
            default_registry().adapter_for_url("https://notquasarzone.com/x")

    def test_모르는_사이트는_다른_사이트_파서로_읽지_않는다(self) -> None:
        with self.assertRaises(UnknownSiteError):
            default_registry().adapter_for_url("https://example.com/list")

    def test_같은_도메인_중복_등록은_거부한다(self) -> None:
        registry = AdapterRegistry()
        registry.register("a.com", QuasarzoneAdapter())

        with self.assertRaises(ValueError):
            registry.register("A.com", QuasarzoneAdapter())


class QualityTest(unittest.TestCase):
    def test_정상_수집은_통과한다(self) -> None:
        adapter, _, normalized = _normalized()

        report = assess_batch(normalized, adapter.capabilities)

        self.assertTrue(report.ok, report)
        self.assertEqual(report.stats["items"], 6)

    def test_0건이면_이상이다(self) -> None:
        adapter = QuasarzoneAdapter()

        report = assess_batch([], adapter.capabilities)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues, ["EMPTY_RESULT"])

    def test_마크업이_바뀌어_가격이_안_읽히면_잡는다(self) -> None:
        """text-orange 클래스가 바뀌면 파서는 에러 없이 price=None 만 돌려준다."""
        adapter = QuasarzoneAdapter()
        html = FIXTURE.read_text(encoding="utf-8").replace("text-orange", "price-new")
        normalized = [adapter.normalize(d, fetched_at=NOW) for d in adapter.parse_listing(html)]

        report = assess_batch(normalized, adapter.capabilities, min_items_for_rates=5)

        self.assertFalse(report.ok)
        self.assertIn("LOW_PRICE_RATE", report.issues)
        self.assertEqual(report.stats["price_parsed_rate"], 0.0)

    def test_날짜_형식이_바뀌어도_잡는다(self) -> None:
        adapter = QuasarzoneAdapter()
        html = FIXTURE.read_text(encoding="utf-8").replace('class="date"', 'class="when"')
        normalized = [adapter.normalize(d, fetched_at=NOW) for d in adapter.parse_listing(html)]

        report = assess_batch(normalized, adapter.capabilities)

        self.assertIn("LOW_POSTED_AT_RATE", report.issues)

    def test_사이트가_주지_않는_필드는_점검하지_않는다(self) -> None:
        class NoPriceSite(QuasarzoneAdapter):
            site_id = "nopricesite"
            capabilities = SiteCapabilities(provides_price=False, provides_posted_at=False)

        adapter = NoPriceSite()
        normalized = [adapter.normalize(d, fetched_at=NOW) for d in adapter.parse_listing(FIXTURE.read_text(encoding="utf-8"))]

        report = assess_batch(normalized, adapter.capabilities)

        self.assertTrue(report.ok, report)
        self.assertNotIn("price_parsed_rate", report.stats)

    def test_건수가_적으면_비율은_보지_않는다(self) -> None:
        adapter, _, normalized = _normalized()

        report = assess_batch(normalized[:2], adapter.capabilities, min_items_for_rates=5)

        self.assertNotIn("price_parsed_rate", report.stats)

    def test_중복_URL을_잡는다(self) -> None:
        adapter, _, normalized = _normalized()

        report = assess_batch(normalized + normalized[:1], adapter.capabilities)

        self.assertIn("DUPLICATE_URLS", report.issues)
        self.assertEqual(report.stats["duplicate_urls"], 1)

    def test_빈_제목을_잡는다(self) -> None:
        from dataclasses import replace

        adapter, _, normalized = _normalized()
        broken = [replace(normalized[0], title="  ")] + normalized[1:]

        self.assertIn("EMPTY_TITLES", assess_batch(broken, adapter.capabilities).issues)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
