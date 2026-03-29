from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..xai import CrawlExplanation, ExplainabilityResult, ItemExplanation


class XAISchemaTest(unittest.TestCase):
    def test_to_dict_includes_required_keys_and_default_errors(self) -> None:
        result = ExplainabilityResult(
            analyzer_id="xai-analyzer",
            generated_at=datetime.now(timezone.utc),
            model_version="v1",
            crawl=CrawlExplanation(
                source="test-source",
                items=[
                    ItemExplanation(
                        item_id="item-1",
                    )
                ],
            ),
        )

        payload = result.to_dict()

        self.assertIn("schema_version", payload)
        self.assertIn("analyzer_id", payload)
        self.assertIn("generated_at", payload)
        self.assertIn("model_version", payload)
        self.assertIn("crawl", payload)
        self.assertIn("errors", payload)
        self.assertEqual(payload["errors"], [])
        item_payload = payload["crawl"]["items"][0]
        self.assertIn("item_id", item_payload)
        self.assertIn("reasons", item_payload)
        self.assertIn("errors", item_payload)
        self.assertIn("generated_at", item_payload)
        self.assertIn("model_version", item_payload)
        self.assertIsInstance(item_payload["reasons"], list)
        self.assertIsInstance(item_payload["errors"], list)
        self.assertEqual(item_payload["reasons"], [])
        self.assertEqual(item_payload["errors"], [])
        self.assertEqual(item_payload["generated_at"], payload["generated_at"])
        self.assertEqual(item_payload["model_version"], payload["model_version"])
        self.assertEqual(payload["generated_at"], result.generated_at.isoformat())

    def test_invalid_generated_at_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            ExplainabilityResult(
                analyzer_id="xai-analyzer",
                generated_at=None,  # type: ignore[arg-type]
                model_version="v1",
                crawl=CrawlExplanation(source="test-source", items=[]),
            )

    def test_invalid_decision_label_is_rejected(self) -> None:
        item = ItemExplanation(item_id="item-1", decision="BUY")
        with self.assertRaises(ValueError):
            item.to_dict(
                model_version="v1", generated_at=datetime.now(timezone.utc).isoformat()
            )


if __name__ == "__main__":
    unittest.main()
