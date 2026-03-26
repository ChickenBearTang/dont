from __future__ import annotations

import os
import unittest

from ..crawler.arcalive_hotdeal_crawler import ArcaLiveHotDealCrawler
from ..crawler.hot_deal_crawler import HotDealCrawler
from ..crawler.run_to_postgres import _build_crawler, _default_dsn


class RunToPostgresTest(unittest.TestCase):
    def test_build_crawler_returns_quasarzone_crawler(self) -> None:
        crawler = _build_crawler("quasarzone")
        self.assertIsInstance(crawler, HotDealCrawler)

    def test_build_crawler_returns_arcalive_crawler(self) -> None:
        crawler = _build_crawler("arcalive")
        self.assertIsInstance(crawler, ArcaLiveHotDealCrawler)

    def test_default_dsn_prefers_ai_postgres_dsn(self) -> None:
        original = dict(os.environ)
        try:
            os.environ["AI_POSTGRES_DSN"] = "postgresql://custom"
            self.assertEqual(_default_dsn(), "postgresql://custom")
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_default_dsn_builds_from_ai_postgres_parts(self) -> None:
        original = dict(os.environ)
        try:
            os.environ.pop("AI_POSTGRES_DSN", None)
            os.environ["AI_POSTGRES_HOST"] = "db-host"
            os.environ["AI_POSTGRES_PORT"] = "6000"
            os.environ["AI_POSTGRES_DB"] = "crawl"
            os.environ["AI_POSTGRES_USER"] = "ai"
            os.environ["AI_POSTGRES_PASSWORD"] = "secret"

            self.assertEqual(
                _default_dsn(),
                "postgresql://ai:secret@db-host:6000/crawl",
            )
        finally:
            os.environ.clear()
            os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
