from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import unittest
from unittest.mock import patch

from ai.models import CrawlResult, HotDeal
import ai.__main__ as main_module


class MainXAITest(unittest.TestCase):
    @patch("ai.__main__.AIPipelineManager")
    def test_main_without_xai_preserves_legacy_payload_shape(self, manager_cls) -> None:
        manager_cls.return_value.run.return_value = CrawlResult(
            source="legacy-source",
            fetched_at=datetime.now(timezone.utc),
            items=[HotDeal(title="Deal", url="https://example.com/1", price="1000")],
        )

        stdout = io.StringIO()
        with patch("sys.argv", ["ai"]):
            with redirect_stdout(stdout):
                main_module.main()

        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(set(payload.keys()), {"source", "item_count"})
        self.assertEqual(payload["source"], "legacy-source")
        self.assertEqual(payload["item_count"], 1)

    @patch("ai.__main__.AIPipelineManager")
    def test_main_with_xai_prints_xai_payload(self, manager_cls) -> None:
        manager_cls.return_value.run.return_value = {
            "schema_version": "financial-purchase-copilot-xai-v1",
            "crawl": {"source": "xai-source", "items": []},
            "errors": [],
        }

        stdout = io.StringIO()
        with patch("sys.argv", ["ai", "--xai"]):
            with redirect_stdout(stdout):
                main_module.main()

        payload = json.loads(stdout.getvalue().strip())
        self.assertIn("schema_version", payload)
        self.assertIn("crawl", payload)
        self.assertEqual(payload["crawl"]["source"], "xai-source")


if __name__ == "__main__":
    unittest.main()
