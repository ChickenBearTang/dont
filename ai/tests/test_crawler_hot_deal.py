from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.data.hot_deal_parser import parse_hot_deals


class HotDealCrawlerTest(unittest.TestCase):
    def test_parse_hot_deals_extracts_expected_items(self) -> None:
        html = """
        <div class="market-info-list">
          <p class="tit">
            <a href="/bbs/qb_saleinfo/views/1" class="subject-link ">
              <span class="ellipsis-with-reply-cnt">First deal</span>
            </a>
          </p>
          <div class="market-info-sub">
            <p>가격 <span class="text-orange">￦ 1,000 (KRW)</span></p>
          </div>
        </div>
        <div class="market-info-list">
          <p class="tit">
            <a href="/bbs/qb_saleinfo/views/2" class="subject-link ">
              <span class="ellipsis-with-reply-cnt">Second deal</span>
            </a>
          </p>
        </div>
        """

        items = parse_hot_deals(html)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "First deal")
        self.assertEqual(items[0].price, "￦ 1,000 (KRW)")
        self.assertEqual(items[1].url, "https://quasarzone.com/bbs/qb_saleinfo/views/2")

    def test_crawl_uses_injected_fetcher(self) -> None:
        requested_urls: list[str] = []

        def fake_fetch(url: str) -> str:
            requested_urls.append(url)
            return (
                '<div class="market-info-list">'
                '<a href="/bbs/qb_saleinfo/views/3" class="subject-link ">Third deal</a>'
                '</div>'
            )

        crawler = HotDealCrawler(source_url="https://source.test", fetch=fake_fetch)

        result = crawler.crawl()

        self.assertEqual(requested_urls, ["https://source.test"])
        self.assertEqual(result.source, "https://source.test")
        self.assertEqual(result.items[0].title, "Third deal")
        self.assertEqual(result.items[0].url, "https://quasarzone.com/bbs/qb_saleinfo/views/3")
        self.assertIsInstance(result.fetched_at, datetime)
        self.assertEqual(result.fetched_at.tzinfo, timezone.utc)

    def test_build_search_url_creates_expected_query(self) -> None:
        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo")

        url = crawler.build_search_url(keyword="마우스", page=2)

        self.assertIn("page=2", url)
        self.assertIn("kind=subject", url)
        self.assertIn("keyword=%EB%A7%88%EC%9A%B0%EC%8A%A4", url)
        self.assertIn("sort=num%2Creply", url)
        self.assertIn("direction=DESC", url)

    def test_build_search_url_merges_existing_query_string(self) -> None:
        crawler = HotDealCrawler(source_url="https://example.com/list?type=hot")

        url = crawler.build_search_url(keyword="키보드", page=1)

        self.assertIn("type=hot", url)
        self.assertIn("keyword=%ED%82%A4%EB%B3%B4%EB%93%9C", url)

    def test_build_search_url_rejects_empty_keyword(self) -> None:
        crawler = HotDealCrawler()

        with self.assertRaises(ValueError):
            crawler.build_search_url(keyword="   ", page=1)

    def test_build_search_url_rejects_invalid_page(self) -> None:
        crawler = HotDealCrawler()

        with self.assertRaises(ValueError):
            crawler.build_search_url(keyword="마우스", page=0)

    def test_search_uses_keyword_url_and_parses_items(self) -> None:
        requested_urls: list[str] = []

        def fake_fetch(url: str) -> str:
            requested_urls.append(url)
            return (
                '<div class="market-info-list">'
                '<a href="/bbs/qb_saleinfo/views/7" class="subject-link ">Mouse deal</a>'
                '</div>'
            )

        crawler = HotDealCrawler(source_url="https://quasarzone.com/bbs/qb_saleinfo", fetch=fake_fetch)

        result = crawler.search(keyword="마우스", page=1)

        self.assertEqual(len(requested_urls), 1)
        self.assertIn("keyword=%EB%A7%88%EC%9A%B0%EC%8A%A4", requested_urls[0])
        self.assertEqual(result.items[0].title, "Mouse deal")
        self.assertEqual(result.source, requested_urls[0])


if __name__ == "__main__":
    unittest.main()
