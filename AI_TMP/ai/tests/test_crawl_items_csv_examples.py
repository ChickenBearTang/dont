from __future__ import annotations

import csv
from pathlib import Path
import unittest

from ..storage.postgres_store import PostgresCrawlStore


ROOT_DIR = Path(__file__).resolve().parents[3]
CSV_PATH = ROOT_DIR / "crawl_items.csv"


class CrawlItemsCsvExamplesTest(unittest.TestCase):
    def test_example_price_normalization_cases_from_export(self) -> None:
        examples = [
            ("6908", "6908"),
            ("15960", "15960"),
            ("22031/100개", "22031"),
            ("8000000", "8000000"),
            ("0원", None),
            ("1795054950", None),
        ]

        for raw_price, expected in examples:
            with self.subTest(raw_price=raw_price):
                self.assertEqual(
                    PostgresCrawlStore._normalize_krw_price(raw_price),
                    expected,
                )

    def test_export_has_expected_columns(self) -> None:
        self.assertTrue(CSV_PATH.exists(), f"missing csv export: {CSV_PATH}")

        with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertIsNotNone(reader.fieldnames)
            assert reader.fieldnames is not None
            self.assertEqual(
                reader.fieldnames,
                [
                    "source",
                    "post_id",
                    "title",
                    "price",
                    "url",
                    "posted_at",
                    "fetched_at",
                    "first_seen_at",
                    "last_seen_at",
                    "is_outlier",
                    "outlier_reason",
                ],
            )

    def test_export_contains_non_null_prices(self) -> None:
        self.assertTrue(CSV_PATH.exists(), f"missing csv export: {CSV_PATH}")

        with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        self.assertGreater(len(rows), 0)
        priced_rows = [row for row in rows if (row.get("price") or "").strip() != ""]
        self.assertGreater(len(priced_rows), 0)


if __name__ == "__main__":
    unittest.main()
