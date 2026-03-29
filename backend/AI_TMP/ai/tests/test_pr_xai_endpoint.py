from __future__ import annotations

from fastapi.testclient import TestClient
import unittest

from consumption_poc.main import app


def _payload() -> dict[str, object]:
    return {
        "requestId": "req-123",
        "schemaVersion": "v1",
        "contextVersion": "v1",
        "purchase": {
            "postId": 67,
            "title": "맥북 구매 요청",
            "itemName": "맥북 프로",
            "content": "개발 업무용으로 필요합니다.",
            "category": "IT",
            "purchaseUrl": "https://example.com/macbook",
            "priceAmount": {
                "value": 2500000,
                "source": "spring.pr_post",
                "snapshotId": "pr-67",
                "isDefault": False,
                "isEstimated": False,
                "estimationMethod": None,
            },
        },
        "financeProfile": {
            "currentBalance": {
                "value": 3000000,
                "source": "spring.finance_profile",
                "snapshotId": "fin-10",
                "isDefault": False,
                "isEstimated": False,
                "estimationMethod": None,
            },
            "emergencyFundBalance": {
                "value": 800000,
                "source": "spring.finance_profile",
                "snapshotId": "fin-10",
                "isDefault": False,
                "isEstimated": False,
                "estimationMethod": None,
            },
            "expectedCardPaymentAmount": {
                "value": 250000,
                "source": "spring.finance_profile",
                "snapshotId": "fin-10",
                "isDefault": False,
                "isEstimated": False,
                "estimationMethod": None,
            },
            "daysUntilCardDue": {
                "value": 12,
                "source": "spring.finance_profile",
                "snapshotId": "fin-10",
                "isDefault": False,
                "isEstimated": False,
                "estimationMethod": None,
            },
        },
        "recentTransactions": [
            {
                "transactionDate": "20260320",
                "transactionTime": "101010",
                "merchantName": "테스트몰",
                "categoryName": "전자제품",
                "transactionAmount": 120000,
            }
        ],
    }


class PurchaseXaiEndpointTest(unittest.TestCase):
    def test_purchase_xai_endpoint_returns_normalized_contract(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/xai/purchase-evaluations", json=_payload())
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["requestId"], "req-123")
        self.assertEqual(payload["purchaseRequestId"], 67)
        self.assertIn(
            payload["decision"],
            {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"},
        )
        self.assertIn("summary", payload)
        self.assertIn("financialEvaluation", payload)
        self.assertIn("priceEvaluation", payload)
        self.assertIn("topFactors", payload)
        self.assertIn("supportingEvidence", payload)
        self.assertIn("counterfactuals", payload)
        self.assertIn("warnings", payload)
        self.assertIn("confidence", payload)
        self.assertIn("runtimeEngines", payload)
        self.assertEqual(payload["schemaVersion"], "v1")

    def test_purchase_xai_endpoint_rejects_missing_finance_profile(self) -> None:
        client = TestClient(app)
        invalid = _payload()
        invalid.pop("financeProfile")
        response = client.post("/api/v1/xai/purchase-evaluations", json=invalid)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
