from __future__ import annotations

import unittest

from ai.crawler.hot_deal_crawler import HotDealCrawler


class LegacyImportTest(unittest.TestCase):
    def test_hot_deal_crawler_import_path_is_ai_crawler(self) -> None:
        self.assertEqual(HotDealCrawler.__module__, "ai.crawler.hot_deal_crawler")


if __name__ == "__main__":
    unittest.main()
