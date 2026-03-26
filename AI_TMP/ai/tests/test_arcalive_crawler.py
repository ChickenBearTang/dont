from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ai.crawler.arcalive_hotdeal_crawler import ArcaLiveHotDealCrawler
from ai.data.arcalive_hotdeal_parser import parse_arcalive_hot_deals


class ArcaLiveHotDealCrawlerTest(unittest.TestCase):
    def test_parse_arcalive_hot_deals_extracts_expected_items(self) -> None:
        html = """
        <div class="vrow hybrid">
          <div class="vrow-inner">
            <div class="vrow-top deal">
              <span class="badges">
                <span class="deal-store">쿠팡</span>
              </span>
              <a class="title hybrid-title" href="/b/hotdeal/123?p=1">
                오뚜기3분 쇠고기 간짜장, 200g, 4개
                <span class="info">[7]</span>
              </a>
            </div>
            <a class="title hybrid-bottom" href="/b/hotdeal/123?p=1">
              <div class="vrow-bottom deal">
                <span class="deal-price">3,960원</span>
                <span class="deal-delivery">무료</span>
                <time datetime="2026-03-26T00:56:18.000Z">5분전</time>
              </div>
            </a>
          </div>
        </div>
        """

        items = parse_arcalive_hot_deals(html)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "[쿠팡] 오뚜기3분 쇠고기 간짜장, 200g, 4개")
        self.assertEqual(items[0].price, "3,960원")
        self.assertEqual(items[0].posted_at, "2026-03-26T00:56:18.000Z")
        self.assertEqual(items[0].url, "https://arca.live/b/hotdeal/123?p=1")

    def test_build_page_url_uses_p_query(self) -> None:
        crawler = ArcaLiveHotDealCrawler()

        url = crawler.build_page_url(page=3)

        self.assertIn("p=3", url)

    def test_build_search_url_creates_expected_query(self) -> None:
        crawler = ArcaLiveHotDealCrawler()

        url = crawler.build_search_url(keyword="그램", page=2)

        self.assertIn("target=all", url)
        self.assertIn("keyword=%EA%B7%B8%EB%9E%A8", url)
        self.assertIn("p=2", url)

    def test_crawl_uses_injected_fetcher(self) -> None:
        requested_urls: list[str] = []

        def fake_fetch(url: str) -> str:
            requested_urls.append(url)
            return (
                '<div class="vrow hybrid">'
                '  <a class="title hybrid-title" href="/b/hotdeal/456?p=1">Lossless Scaling</a>'
                '  <a class="title hybrid-bottom" href="/b/hotdeal/456?p=1">'
                '    <span class="deal-price">4,680원</span>'
                '    <time datetime="2026-03-20T00:00:00.000Z">03-20</time>'
                "  </a>"
                "</div>"
            )

        crawler = ArcaLiveHotDealCrawler(fetch=fake_fetch)

        result = crawler.crawl()

        self.assertEqual(requested_urls, ["https://arca.live/b/hotdeal"])
        self.assertEqual(result.source, "https://arca.live/b/hotdeal")
        self.assertEqual(result.items[0].title, "Lossless Scaling")
        self.assertEqual(result.items[0].url, "https://arca.live/b/hotdeal/456?p=1")
        self.assertIsInstance(result.fetched_at, datetime)
        self.assertEqual(result.fetched_at.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
