from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
from domain.xai_purchase.service import evaluate_pr_purchase_xai


def _request() -> PurchaseXaiEvaluationRequest:
    return PurchaseXaiEvaluationRequest.model_validate(
        {
            "requestId": "req-price-model",
            "schemaVersion": "v1",
            "contextVersion": "v1",
            "purchase": {
                "postId": 7,
                "title": "mock request",
                "itemName": "headset",
                "content": "mock content",
                "category": "IT",
                "purchaseUrl": "https://example.com/item",
                "priceAmount": {
                    "value": 199000,
                    "source": "spring.pr_post",
                    "snapshotId": "pr-7",
                },
            },
            "financeProfile": {
                "currentBalance": {"value": 1000000, "source": "spring.finance"},
                "emergencyFundBalance": {"value": 700000, "source": "spring.finance"},
                "expectedCardPaymentAmount": {"value": 150000, "source": "spring.finance"},
                "daysUntilCardDue": {"value": 10, "source": "spring.finance"},
            },
            "recentTransactions": [],
        }
    )


class XaiPurchaseServicePriceModelTest(unittest.TestCase):
    def test_runtime_engines_exposes_price_model_backend(self) -> None:
        with patch(
            "domain.xai_purchase.service.predict_price_signal",
            return_value=(
                {"price_model_gap_score": 0.5},
                {"enabled": True, "backend": "lightgbm_regressor", "reason": "ok"},
            ),
        ), patch(
            "domain.xai_purchase.service.predict_finance_signal",
            return_value=(
                {
                    "finance_model_risk_bucket": "medium",
                    "finance_model_risk_score": 0.2,
                    "finance_model_affordability_score": -0.2,
                },
                {"enabled": True, "backend": "lightgbm_classifier", "reason": "ok"},
            ),
        ):
            response = evaluate_pr_purchase_xai(_request())
        self.assertEqual(response.runtime_engines.price_model, "lightgbm_regressor")
        self.assertEqual(response.runtime_engines.finance_model, "lightgbm_classifier")

    def test_price_model_disabled_reason_is_not_added_to_warnings(self) -> None:
        with patch(
            "domain.xai_purchase.service.predict_price_signal",
            return_value=(
                {},
                {"enabled": False, "backend": "disabled", "reason": "price_model_disabled"},
            ),
        ), patch(
            "domain.xai_purchase.service.predict_finance_signal",
            return_value=(
                {},
                {"enabled": False, "backend": "disabled", "reason": "finance_model_disabled"},
            ),
        ):
            response = evaluate_pr_purchase_xai(_request())
        self.assertNotIn("PRICE_MODEL_DISABLED", response.warnings)
        self.assertNotIn("FINANCE_MODEL_DISABLED", response.warnings)


if __name__ == "__main__":
    unittest.main()
