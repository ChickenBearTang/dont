from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
import unittest
from unittest.mock import patch

import ai.__main__ as main_module


class MainFinanceIntegrationTest(unittest.TestCase):
    @patch("ai.__main__.fetch_finance_profile")
    def test_resolve_finance_profile_uses_env_url(self, fetch_mock) -> None:
        fetch_mock.return_value = {"current_balance": 1000.0, "days_until_card_due": 7}

        with patch.dict(
            os.environ, {"AI_FINANCE_API_URL": "http://localhost:9000/api"}
        ):
            profile = main_module._resolve_finance_profile(
                finance_api_url=None,
                finance_api_timeout=5,
            )

        self.assertEqual(profile, {"current_balance": 1000.0, "days_until_card_due": 7})
        fetch_mock.assert_called_once_with("http://localhost:9000/api", timeout=5)

    @patch("ai.__main__.AIPipelineManager")
    @patch("ai.__main__.ExplainabilityAnalyzer")
    @patch("ai.__main__._resolve_finance_profile")
    def test_main_xai_uses_empty_profile_when_finance_fetch_fails(
        self,
        resolve_mock,
        analyzer_cls,
        manager_cls,
    ) -> None:
        resolve_mock.return_value = None
        manager_cls.return_value.run.return_value = {
            "schema_version": "financial-purchase-copilot-xai-v1"
        }

        stdout = io.StringIO()
        with patch("sys.argv", ["ai", "--xai"]):
            with redirect_stdout(stdout):
                main_module.main()

        analyzer_cls.assert_called_once()
        kwargs = analyzer_cls.call_args.kwargs
        self.assertEqual(kwargs.get("finance_profile"), {})
        self.assertIn("counterfactual_engine", kwargs)
        self.assertIn("dice_counterfactual_engine", kwargs)
        self.assertIn("shap_contribution_engine", kwargs)
        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(payload["schema_version"], "financial-purchase-copilot-xai-v1")


if __name__ == "__main__":
    unittest.main()
