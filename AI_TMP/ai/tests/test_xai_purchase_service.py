from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
from domain.xai_purchase.service import _derive_title_keywords
from domain.xai_purchase.service import evaluate_pr_purchase_xai


def _request() -> PurchaseXaiEvaluationRequest:
    return PurchaseXaiEvaluationRequest.model_validate(
        {
            "requestId": "req-456",
            "schemaVersion": "v1",
            "contextVersion": "v1",
            "purchase": {
                "postId": 91,
                "title": "키보드 구매 요청",
                "itemName": "기계식 키보드",
                "content": "개발 생산성 향상을 위해 필요합니다.",
                "category": "IT",
                "purchaseUrl": "https://example.com/keyboard",
                "priceAmount": {
                    "value": 189000,
                    "source": "spring.pr_post",
                    "snapshotId": "pr-91",
                },
            },
            "financeProfile": {
                "currentBalance": {
                    "value": 1200000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "emergencyFundBalance": {
                    "value": 700000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "expectedCardPaymentAmount": {
                    "value": 150000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "daysUntilCardDue": {
                    "value": 12,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
            },
            "recentTransactions": [],
        }
    )


class XaiPurchaseServiceTest(unittest.TestCase):
    def test_derive_title_keywords_prefers_model_phrase(self) -> None:
        keywords = _derive_title_keywords("로지텍 MX Master 4 무선 마우스")

        self.assertIn("로지텍 mx master 4 무선 마우스", keywords)
        self.assertIn("mx master 4", keywords)
        self.assertNotIn("로지텍", keywords)
        self.assertNotIn("마우스", keywords)

    def test_derive_title_keywords_prefers_model_codes_for_gram(self) -> None:
        keywords = _derive_title_keywords("LG gram PRO 360 16T95TP-KD79K OLED")

        self.assertIn("16t95tp kd79k", keywords)
        self.assertIn("16t95tp", keywords)
        self.assertIn("kd79k", keywords)
        self.assertIn("lg gram", keywords)
        self.assertIn("lg gram 16t95tp kd79k", keywords)

    def test_derive_title_keywords_supports_phrase_style_models(self) -> None:
        keywords = _derive_title_keywords(
            "Thermalright Peerless Assassin 120 SE V2"
        )

        self.assertIn("thermalright peerless assassin 120 se v2", keywords)
        self.assertIn("thermalright peerless assassin", keywords)

    def test_item_specific_price_history_is_preferred_when_available(self) -> None:
        fake_store = MagicMock()
        fake_store.read_window_stats.side_effect = [
            {
                "30d": {
                    "count": 1,
                    "avg_price": 120345.0,
                    "min_price": 120345.0,
                    "max_price": 120345.0,
                },
                "90d": {
                    "count": 1,
                    "avg_price": 120345.0,
                    "min_price": 120345.0,
                    "max_price": 120345.0,
                },
            },
            {
                "30d": {
                    "count": 4,
                    "avg_price": 2500000.0,
                    "min_price": 2400000.0,
                    "max_price": 2600000.0,
                },
                "90d": {
                    "count": 5,
                    "avg_price": 2480000.0,
                    "min_price": 2390000.0,
                    "max_price": 2610000.0,
                },
            }
        ]
        with patch("domain.xai_purchase.service.PostgresCrawlStore", return_value=fake_store):
            with patch("config.get_env", return_value="postgresql://test"):
                response = evaluate_pr_purchase_xai(_request())

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertIn("2,500,000", str(price_metrics.get("avg_price_30d")))
        self.assertEqual(fake_store.read_window_stats.call_count, 2)
        first_call = fake_store.read_window_stats.call_args_list[0].kwargs
        second_call = fake_store.read_window_stats.call_args_list[1].kwargs
        self.assertEqual(len(first_call.get("title_keywords", [])), 1)
        self.assertEqual(len(second_call.get("title_keywords", [])), 0)

    def test_evaluate_pr_purchase_xai_returns_normalized_response(self) -> None:
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(_request())

        self.assertEqual(response.request_id, "req-456")
        self.assertEqual(response.purchase_request_id, 91)
        self.assertIn(
            response.decision, {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"}
        )
        self.assertTrue(len(response.top_factors) >= 1)
        self.assertTrue(len(response.supporting_evidence) >= 1)
        self.assertIn("runtime_engines", response.model_dump())

    def test_request_price_takes_priority_over_noisy_crawled_value(self) -> None:
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=("배송비 1,796원 / 특가 2,500,000원 아님", None),
        ):
            response = evaluate_pr_purchase_xai(_request())

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertEqual(price_metrics.get("current_effective_price"), "189,000원")
        self.assertNotIn("requested_price_amount", price_metrics)
        self.assertNotIn("crawled_price_candidate", price_metrics)
        self.assertNotIn("CRAWL_FETCH_FAILED", response.warnings)
        self.assertNotIn("PRICE_ESTIMATED_FROM_REQUEST", response.warnings)
        self.assertNotIn("CRAWLED_PRICE_DIVERGES_FROM_REQUEST", response.warnings)

    def test_summary_and_top_factors_are_localized_in_korean(self) -> None:
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(_request())

        self.assertRegex(response.summary, r"[가-힣]")
        self.assertGreaterEqual(len(response.top_factors), 1)
        for factor in response.top_factors:
            self.assertRegex(factor.label, r"[가-힣]")

    def test_missing_crawl_price_defaults_to_zero_without_divergence_warning(
        self,
    ) -> None:
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(_request())

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertNotIn("requested_price_amount", price_metrics)
        self.assertNotIn("crawled_price_candidate", price_metrics)
        self.assertNotIn("CRAWLED_PRICE_DIVERGES_FROM_REQUEST", response.warnings)
        self.assertNotIn("CRAWL_FETCH_FAILED", response.warnings)
        self.assertNotIn("PRICE_ESTIMATED_FROM_REQUEST", response.warnings)

    def test_tag_based_price_is_preferred_over_noisy_large_numbers(self) -> None:
        request = _request()
        request.purchase.price_amount.value = 1000
        tagged_html = """
        <html>
          <body>
            <div class="purchase-card">
              <span class="final-price">1,000원</span>
            </div>
            <script>
              const analyticsTotal = 534000000;
            </script>
          </body>
        </html>
        """
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(tagged_html, None),
        ):
            response = evaluate_pr_purchase_xai(request)

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertEqual(price_metrics.get("current_effective_price"), "1,000원")
        self.assertNotIn("requested_price_amount", price_metrics)
        self.assertNotIn("crawled_price_candidate", price_metrics)
        self.assertNotIn("CRAWLED_PRICE_DIVERGES_FROM_REQUEST", response.warnings)

    def test_total_price_is_divided_by_quantity_for_per_item_candidate(self) -> None:
        request = _request()
        request.purchase.price_amount.value = None
        tagged_html = """
        <html>
          <body>
            <div class="price-summary">총 금액 893,000,000원 / 1000개</div>
          </body>
        </html>
        """
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(tagged_html, None),
        ):
            response = evaluate_pr_purchase_xai(request)

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertNotIn("requested_price_amount", price_metrics)
        self.assertNotIn("crawled_price_candidate", price_metrics)
        self.assertEqual(price_metrics.get("current_effective_price"), "-")

    def test_financial_status_uses_savebox_and_fixed_cashflow_fields(self) -> None:
        payload = _request().model_dump(by_alias=True)
        payload["financeProfile"]["currentBalance"]["value"] = 12_912_010
        payload["financeProfile"]["daysUntilCardDue"]["value"] = 10
        payload["financeProfile"]["saveboxBalance"] = {
            "value": 0,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        payload["financeProfile"]["availableFixedExpense"] = {
            "value": 400000,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        payload["financeProfile"]["availableFixedIncome"] = {
            "value": 300000,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        request = PurchaseXaiEvaluationRequest.model_validate(payload)

        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(request)

        self.assertEqual(response.financial_evaluation.status, "critical")
        financial_metrics = {
            metric.code: metric.value
            for metric in response.financial_evaluation.key_metrics
        }
        self.assertEqual(financial_metrics.get("savebox_balance"), "0원")
        self.assertEqual(financial_metrics.get("available_fixed_expense"), "400,000원")
        self.assertEqual(financial_metrics.get("available_fixed_income"), "300,000원")
        self.assertEqual(financial_metrics.get("days_until_card_due"), "10일")

    def test_jsonl_audit_store_persists_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JsonlXaiAuditLogStore(Path(tmp_dir) / "audit.jsonl")
            store.save(
                request_id="req-1",
                purchase_request_id=10,
                warnings=["NO_PRICE_HISTORY"],
                runtime_engines={"decision": "rule_engine_v1"},
                audit_logs=[
                    {"final_decision": "REVIEW", "item_id": "https://example.com"}
                ],
            )

            saved = (Path(tmp_dir) / "audit.jsonl").read_text(encoding="utf-8")
            self.assertIn("req-1", saved)
            self.assertIn("NO_PRICE_HISTORY", saved)
            self.assertIn("REVIEW", saved)


if __name__ == "__main__":
    unittest.main()
