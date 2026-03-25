from __future__ import annotations

import json
from importlib import import_module
import unittest

from ..models import HotDeal


class FeatureExtractorTest(unittest.TestCase):
    def setUp(self) -> None:
        features_module = import_module("ai.xai.features")
        self.extractor = features_module.FeatureExtractor()

    def test_extract_features_happy_path_with_numeric_price(self) -> None:
        deal = HotDeal(
            title="Gaming Mouse Deal",
            url="https://quasarzone.com/bbs/qb_saleinfo/views/1",
            price="￦ 1,000 (KRW)",
        )

        features = self.extractor.extract_features(deal)

        self.assertEqual(features["title_len"], len("Gaming Mouse Deal"))
        self.assertTrue(features["has_title"])
        self.assertTrue(features["has_price"])
        self.assertEqual(features["price_int"], 1000)
        self.assertEqual(features["url_domain"], "quasarzone.com")
        self.assertEqual(features["missing_fields"], [])
        json.dumps(features)

    def test_extract_features_non_numeric_price_marks_missing(self) -> None:
        deal = HotDeal(
            title="No Price Deal",
            url="https://quasarzone.com/bbs/qb_saleinfo/views/2",
            price="문의",
        )

        features = self.extractor.extract_features(deal)

        self.assertIsNone(self.extractor.normalize_price_to_int("문의"))
        self.assertFalse(features["has_price"])
        self.assertIsNone(features["price_int"])
        self.assertIn("price", features["missing_fields"])

    def test_extract_features_handles_extremely_long_title(self) -> None:
        long_title = "A" * 10000
        deal = HotDeal(
            title=long_title,
            url="https://quasarzone.com/bbs/qb_saleinfo/views/3",
            price=None,
        )

        features = self.extractor.extract_features(deal)

        self.assertEqual(features["title_len"], 10000)
        self.assertTrue(features["has_title"])
        self.assertFalse(features["has_price"])
        self.assertIn("price", features["missing_fields"])


if __name__ == "__main__":
    unittest.main()
