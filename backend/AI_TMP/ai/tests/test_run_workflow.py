from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch
import unittest

from ..crawler import run_workflow


@dataclass
class _FakeSampleResult:
    total_count: int
    sample_items: list[dict[str, str | None]]


class _FakeStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def read_samples(self, sample_limit: int) -> _FakeSampleResult:
        del sample_limit
        return _FakeSampleResult(
            total_count=1,
            sample_items=[
                {
                    "post_id": "1",
                    "title": "sample",
                    "price": "1000",
                    "url": "https://example.com/1",
                }
            ],
        )


class RunWorkflowTest(unittest.TestCase):
    @patch("ai.crawler.run_workflow.subprocess.run")
    def test_run_crawl_defaults_to_postgres_runner(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "{}"
        run_mock.return_value.stderr = ""

        result = run_workflow.run_crawl(
            db_path="ai/data/crawl.db",
            keyword="cpu",
            start_page=1,
            max_pages=3,
            overlap_threshold=10,
        )

        command = str(result["command"])
        self.assertIn("ai.crawler.run_to_postgres", command)
        self.assertIn("--db-url", command)
        self.assertNotIn("ai.crawler.run_to_sqlite", command)

    def test_run_crawl_rejects_sqlite_backend(self) -> None:
        with self.assertRaises(ValueError):
            run_workflow.run_crawl(
                db_path="ai/data/crawl.db",
                backend="sqlite",
                keyword="cpu",
                start_page=1,
                max_pages=3,
                overlap_threshold=10,
            )

    @patch("ai.crawler.run_workflow.subprocess.run")
    def test_run_crawl_uses_postgres_when_explicitly_selected(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "{}"
        run_mock.return_value.stderr = ""

        result = run_workflow.run_crawl(
            db_path="ai/data/crawl.db",
            db_url="postgresql://ai:pw@localhost:55432/ai_crawl",
            backend="postgres",
            keyword="cpu",
            start_page=1,
            max_pages=3,
            overlap_threshold=10,
        )

        command = str(result["command"])
        self.assertIn("ai.crawler.run_to_postgres", command)
        self.assertIn("--db-url", command)
        self.assertNotIn("ai.crawler.run_to_sqlite", command)

    @patch("ai.crawler.run_workflow.PostgresCrawlStore", _FakeStore)
    def test_read_samples_uses_postgres_store_when_selected(self) -> None:
        payload = run_workflow.read_samples(
            db_path="ai/data/crawl.db",
            db_url="postgresql://example",
            sample_limit=5,
            backend="postgres",
        )
        self.assertEqual(payload["total_count"], 1)
        sample_items = payload["sample_items"]
        if not isinstance(sample_items, list):
            self.fail("sample_items must be a list")
        self.assertGreater(len(sample_items), 0)
        first_item = sample_items[0]
        if not isinstance(first_item, dict):
            self.fail("sample item must be a dict")
        self.assertEqual(first_item.get("post_id"), "1")


if __name__ == "__main__":
    unittest.main()
