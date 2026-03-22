from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from ai.models import CrawlResult
from .types import AnalysisError, CrawlExplanation, ExplainabilityResult, ItemExplanation


class ExplainabilityAnalyzer:
    ANALYZER_ID = "xai-explainability"
    MODEL_VERSION = "rules-v2"

    def __init__(
        self,
        *,
        feature_extractor: Any | None = None,
        reasoning_engine: Any | None = None,
        counterfactual_engine: Any | None = None,
        summary_polisher: Any | None = None,
        finance_profile: dict[str, float | int] | None = None,
    ) -> None:
        features_module = import_module("ai.xai.features")
        reasoning_module = import_module("ai.xai.reasoning")
        counterfactuals_module = import_module("ai.xai.counterfactuals")
        polisher_module = import_module("ai.xai.polisher")
        self._feature_extractor = feature_extractor or features_module.FeatureExtractor()
        self._reasoning_engine = reasoning_engine or reasoning_module.ReasoningEngine()
        self._counterfactual_engine = (
            counterfactual_engine or counterfactuals_module.CounterfactualEngine()
        )
        self._summary_polisher = summary_polisher or polisher_module.LLMSummaryPolisher()
        self._finance_profile = finance_profile or {}

    def analyze_crawl_result(
        self,
        result: CrawlResult,
        top_k: int = 3,
        window_stats: dict[str, dict[str, float | int | None]] | None = None,
    ) -> dict[str, Any]:
        sorted_items = sorted(result.items, key=lambda deal: (deal.url, deal.title))

        item_explanations: list[ItemExplanation] = []
        errors: list[AnalysisError] = []

        for deal in sorted_items:
            item_error: AnalysisError | None = None
            reasons: list[dict[str, Any]] = []

            try:
                features = self._feature_extractor.extract_features(deal)
                feature_scores = self._build_feature_scores(features, window_stats=window_stats)
                reasons = self._reasoning_engine.analyze(feature_scores, top_k=top_k)
                decision = self._decide(reasons)
                price_int = features.get("price_int")
                price_value = price_int if isinstance(price_int, int) else None
                monthly_spending_30d = self._monthly_spending_30d(window_stats)
                current_balance = float(self._finance_profile.get("current_balance", 1_500_000))
                emergency_fund_balance = float(
                    self._finance_profile.get("emergency_fund_balance", 600_000)
                )
                days_until_card_due = int(self._finance_profile.get("days_until_card_due", 14))
                expected_card_payment_amount = float(
                    self._finance_profile.get("expected_card_payment_amount", 200_000)
                )

                counterfactuals = self._counterfactual_engine.suggest(
                    price_int=price_value,
                    monthly_spending_30d=monthly_spending_30d,
                    emergency_fund_balance=emergency_fund_balance,
                    current_balance=current_balance,
                    days_until_card_due=days_until_card_due,
                    expected_card_payment_amount=expected_card_payment_amount,
                )
                top_reason_text = (
                    str(reasons[0].get("reason_text", "기여도 신호 분석 결과"))
                    if len(reasons) > 0
                    else "기여도 신호 분석 결과"
                )
                suggestion_text = str(counterfactuals[0].get("message", "가격/재무 상태 재평가"))
                polished_summary = self._summary_polisher.polish(
                    decision=decision,
                    top_reason_text=top_reason_text,
                    suggestion_text=suggestion_text,
                )
            except Exception as exc:
                item_error = self._build_error(exc=exc, item_id=deal.url)
                errors.append(item_error)
                decision = "REVIEW"
                counterfactuals = []
                polished_summary = "분석 오류로 요약을 생성하지 못했습니다."

            item_explanations.append(
                ItemExplanation(
                    item_id=deal.url,
                    decision=decision,
                    reasons=reasons,
                    counterfactuals=counterfactuals,
                    polished_summary=polished_summary,
                    errors=[item_error] if item_error is not None else [],
                )
            )

        explainability_result = ExplainabilityResult(
            analyzer_id=self.ANALYZER_ID,
            generated_at=datetime.now(timezone.utc),
            model_version=self.MODEL_VERSION,
            crawl=CrawlExplanation(source=result.source, items=item_explanations),
            errors=errors,
        )
        payload = explainability_result.to_dict()
        payload["statistics"] = window_stats or {}
        payload["finance_profile"] = {
            "current_balance": float(self._finance_profile.get("current_balance", 1_500_000)),
            "emergency_fund_balance": float(
                self._finance_profile.get("emergency_fund_balance", 600_000)
            ),
            "expected_card_payment_amount": float(
                self._finance_profile.get("expected_card_payment_amount", 200_000)
            ),
            "days_until_card_due": int(self._finance_profile.get("days_until_card_due", 14)),
        }
        return payload

    def _build_feature_scores(
        self,
        features: dict[str, Any],
        *,
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> dict[str, float]:
        missing_fields = features.get("missing_fields", [])
        if not isinstance(missing_fields, list):
            raise ValueError("missing_fields must be a list")
        if len(missing_fields) > 0:
            missing = ",".join(str(field) for field in sorted(missing_fields))
            raise ValueError(f"deal missing required fields: {missing}")

        title_len_raw = features.get("title_len", 0)
        title_len = int(title_len_raw) if isinstance(title_len_raw, int) else 0
        title_len_score = min(title_len / 100.0, 1.0)

        has_price = bool(features.get("has_price", False))
        has_title = bool(features.get("has_title", False))

        price_raw = features.get("price_int")
        price_int = int(price_raw) if isinstance(price_raw, int) else 0
        current_price_score = 1.0 / (1.0 + (price_int / 100_000.0)) if price_int > 0 else 0.0

        monthly_spending_30d = self._monthly_spending_30d(window_stats)
        current_balance = float(self._finance_profile.get("current_balance", 1_500_000))
        emergency_fund_balance = float(self._finance_profile.get("emergency_fund_balance", 600_000))
        days_until_card_due = int(self._finance_profile.get("days_until_card_due", 14))

        return {
            "current_price": current_price_score,
            "coupon_applied": 1.0 if has_price else -1.0,
            "avg_price_30d": title_len_score,
            "shipping_fee": -float(len(missing_fields)),
            "product_price_vs_monthly_spending": (
                (price_int / monthly_spending_30d) if monthly_spending_30d > 0 else 1.0
            ),
            "emergency_fund_balance": emergency_fund_balance / max(monthly_spending_30d, 1.0),
            "projected_balance_after_purchase": (current_balance - price_int) / max(monthly_spending_30d, 1.0),
            "days_until_card_due": float(days_until_card_due) / 30.0,
        }

    def _monthly_spending_30d(
        self,
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> float:
        if window_stats is None:
            return 800_000.0
        window_30d = window_stats.get("30d", {})
        avg_price = window_30d.get("avg_price")
        count = window_30d.get("count")
        if isinstance(avg_price, (int, float)) and isinstance(count, int) and count > 0:
            return max(float(avg_price) * min(count, 30), 1.0)
        return 800_000.0

    def _decide(self, reasons: list[dict[str, Any]]) -> str:
        if len(reasons) == 0:
            return "REVIEW"
        total = sum(float(reason.get("score", 0.0)) for reason in reasons)
        if total >= 0.8:
            return "BUY"
        if total >= -0.3:
            return "WAIT"
        return "SKIP"

    def _build_error(self, *, exc: Exception, item_id: str) -> AnalysisError:
        if isinstance(exc, ValueError):
            code = "XAI_ITEM_VALIDATION_FAILED"
            message = "항목 검증에 실패했습니다"
        else:
            code = "XAI_ANALYSIS_FAILED"
            message = "분석 처리에 실패했습니다"
        return AnalysisError(code=code, message=message, item_id=item_id)
