from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from ..models import CrawlResult
from .audit_log import XAIAuditLogEntry, build_model_input_vector_hash
from .decision_engine import DecisionEngine
from .explanation_engine import ExplanationEngine
from .types import (
    AnalysisError,
    CrawlExplanation,
    ExplainabilityResult,
    ItemExplanation,
)


class ExplainabilityAnalyzer:
    """Builds Explainable AI (XAI) analysis payloads for crawled items.

    This analyzer coordinates feature extraction, reasoning, decision logic,
    counterfactual generation, and summary polishing, then returns a structured
    payload used by the CLI and tests.
    """

    ANALYZER_ID = "xai-explainability"
    MODEL_VERSION = "financial-purchase-copilot-xai-model-v1"

    def __init__(
        self,
        *,
        feature_extractor: Any | None = None,
        reasoning_engine: Any | None = None,
        counterfactual_engine: Any | None = None,
        dice_counterfactual_engine: Any | None = None,
        shap_contribution_engine: Any | None = None,
        summary_polisher: Any | None = None,
        finance_profile: dict[str, float | int] | None = None,
        price_model_signal: dict[str, float] | None = None,
        finance_model_signal: dict[str, float | str] | None = None,
    ) -> None:
        features_module = import_module("ai.xai.features")
        reasoning_module = import_module("ai.xai.reasoning")
        counterfactuals_module = import_module("ai.xai.counterfactuals")
        polisher_module = import_module("ai.xai.polisher")
        shap_module: Any | None = None
        dice_module: Any | None = None
        try:
            shap_module = import_module("ai.xai.shap_engine")
        except Exception:
            shap_module = None
        try:
            dice_module = import_module("ai.xai.dice_engine")
        except Exception:
            dice_module = None
        self._feature_extractor = (
            feature_extractor or features_module.FeatureExtractor()
        )
        self._reasoning_engine = reasoning_engine or reasoning_module.ReasoningEngine()
        self._rule_counterfactual_engine = (
            counterfactual_engine or counterfactuals_module.CounterfactualEngine()
        )
        self._dice_counterfactual_engine = dice_counterfactual_engine or (
            dice_module.DiceCounterfactualEngine(
                fallback_engine=self._rule_counterfactual_engine
            )
            if dice_module is not None
            else self._rule_counterfactual_engine
        )
        self._shap_contribution_engine = shap_contribution_engine or (
            shap_module.ShapContributionEngine() if shap_module is not None else None
        )
        self._summary_polisher = (
            summary_polisher or polisher_module.LLMSummaryPolisher()
        )
        self._decision_engine = DecisionEngine()
        self._explanation_engine = ExplanationEngine()
        self._finance_profile = finance_profile or {}
        self._price_model_signal = price_model_signal or {}
        self._finance_model_signal = finance_model_signal or {}

    def analyze_crawl_result(
        self,
        result: CrawlResult,
        top_k: int = 3,
        window_stats: dict[str, dict[str, float | int | None]] | None = None,
    ) -> dict[str, Any]:
        sorted_items = sorted(result.items, key=lambda deal: (deal.url, deal.title))

        item_explanations: list[ItemExplanation] = []
        errors: list[AnalysisError] = []
        audit_logs: list[XAIAuditLogEntry] = []
        shap_engine_state: dict[str, Any] = {
            "enabled": False,
            "backend": "fallback",
            "reason": "not_computed",
        }
        dice_engine_state: dict[str, Any] = {
            "enabled": False,
            "backend": "fallback",
            "reason": "not_computed",
        }

        requested_top_k = max(1, min(int(top_k), 4))

        for deal in sorted_items:
            item_error: AnalysisError | None = None

            try:
                features = self._feature_extractor.extract_features(deal)
                feature_scores = self._build_feature_scores(
                    features, window_stats=window_stats
                )
                shap_scores = dict(feature_scores)
                if self._shap_contribution_engine is not None and hasattr(
                    self._shap_contribution_engine, "compute"
                ):
                    computed, shap_meta = self._shap_contribution_engine.compute(
                        feature_scores=shap_scores
                    )
                    if isinstance(computed, dict):
                        shap_scores = {
                            str(name): float(value)
                            for name, value in computed.items()
                            if isinstance(name, str)
                        }
                    if isinstance(shap_meta, dict):
                        shap_engine_state = {
                            "enabled": bool(shap_meta.get("enabled", False)),
                            "backend": str(shap_meta.get("backend", "fallback")),
                        }
                        if "reason" in shap_meta:
                            shap_engine_state["reason"] = str(shap_meta.get("reason"))
                        if "feature_count" in shap_meta:
                            shap_engine_state["feature_count"] = int(
                                shap_meta.get("feature_count", len(shap_scores))
                            )
                reasons = self._reasoning_engine.analyze(
                    shap_scores, top_k=requested_top_k
                )
                decision_outcome = self._decision_engine.decide(feature_scores)
                price_int = features.get("price_int")
                price_value = price_int if isinstance(price_int, int) else None
                monthly_spending_30d = self._monthly_spending_30d(window_stats)
                current_balance = float(
                    self._finance_profile.get("current_balance", 1_500_000)
                )
                emergency_fund_balance = float(
                    self._finance_profile.get("emergency_fund_balance", 600_000)
                )
                savebox_balance = float(
                    self._finance_profile.get(
                        "savebox_balance",
                        emergency_fund_balance,
                    )
                )
                days_until_card_due = int(
                    self._finance_profile.get("days_until_card_due", 14)
                )
                expected_card_payment_amount = float(
                    self._finance_profile.get("expected_card_payment_amount", 200_000)
                )

                counterfactuals: list[dict[str, Any]] = []
                if hasattr(self._dice_counterfactual_engine, "suggest"):
                    suggested = self._dice_counterfactual_engine.suggest(
                        price_int=price_value,
                        monthly_spending_30d=monthly_spending_30d,
                        emergency_fund_balance=savebox_balance,
                        current_balance=savebox_balance,
                        days_until_card_due=days_until_card_due,
                        expected_card_payment_amount=expected_card_payment_amount,
                    )
                    if isinstance(suggested, tuple) and len(suggested) == 2:
                        counterfactuals, dice_meta = suggested
                        if isinstance(dice_meta, dict):
                            dice_engine_state = dice_meta
                    elif isinstance(suggested, list):
                        counterfactuals = suggested

                counterfactuals = self._stabilize_counterfactual_suggestions(
                    counterfactuals,
                    price_value=price_value,
                    monthly_spending_30d=monthly_spending_30d,
                    savebox_balance=savebox_balance,
                    window_stats=window_stats,
                )
                counterfactuals = self._normalize_counterfactual_messages(
                    counterfactuals
                )

                top_reason_text = (
                    str(reasons[0].get("reason_text", "기여도 신호 분석 결과"))
                    if len(reasons) > 0
                    else "기여도 신호 분석 결과"
                )
                suggestion_text = str(
                    counterfactuals[0].get("message", "가격/재무 상태 재평가")
                )
                polished_summary = self._summary_polisher.polish(
                    decision=decision_outcome.final_decision,
                    top_reason_text=top_reason_text,
                    suggestion_text=suggestion_text,
                )

                observed_features = {
                    "current_price": features.get("price_int"),
                    "avg_price_30d": ((window_stats or {}).get("30d", {}) or {}).get(
                        "avg_price"
                    ),
                    "product_price_vs_monthly_spending": (
                        (float(features.get("price_int", 0)) / monthly_spending_30d)
                        if monthly_spending_30d > 0
                        else None
                    ),
                    "emergency_fund_balance": emergency_fund_balance,
                    "projected_balance_after_purchase": (
                        savebox_balance - float(features.get("price_int", 0))
                    ),
                    "days_until_card_due": days_until_card_due,
                    "price_model_gap_score": self._price_model_signal.get(
                        "price_model_gap_score"
                    ),
                    "finance_model_risk_score": self._finance_model_signal.get(
                        "finance_model_risk_score"
                    ),
                    "finance_model_affordability_score": self._finance_model_signal.get(
                        "finance_model_affordability_score"
                    ),
                }

                item = self._explanation_engine.build_item_explanation(
                    item_id=deal.url,
                    reasons=reasons,
                    feature_scores=shap_scores,
                    observed_features=observed_features,
                    decision_outcome=decision_outcome,
                    counterfactuals=counterfactuals,
                    polished_summary=polished_summary,
                )

                audit_logs.append(
                    XAIAuditLogEntry(
                        deal.url,
                        [{"source": result.source, "item_url": deal.url}],
                        ["feature_extractor", "score_builder", "reasoning_engine"],
                        item.data_snapshot_id,
                        item.data_snapshot_id,
                        build_model_input_vector_hash(shap_scores),
                        decision_outcome.fired_rule_ids,
                        [
                            {
                                "feature": reason.get("feature"),
                                "score": reason.get("score"),
                                "reason_code": reason.get("reason_code"),
                            }
                            for reason in item.reasons
                        ],
                        item.decision,
                        item.polished_summary,
                        self.MODEL_VERSION,
                        item.rule_version,
                        "financial-purchase-copilot-xai-v1",
                    )
                )
            except Exception as exc:
                item_error = self._build_error(exc=exc, item_id=deal.url)
                errors.append(item_error)
                item = ItemExplanation(
                    item_id=deal.url,
                    decision="REVIEW",
                    decision_confidence=0.0,
                    reasons=[],
                    supporting_evidence=[],
                    reason_codes=[],
                    reason_texts=[],
                    counterfactual_conditions=[],
                    counterfactuals=[],
                    user_options=["수동 검토 요청"],
                    rule_version=self._decision_engine.RULE_VERSION,
                    data_snapshot_id="snapshot:error",
                    polished_summary="분석 오류로 요약을 생성하지 못했습니다.",
                    errors=[item_error] if item_error is not None else [],
                )

            item_explanations.append(item)

        explainability_result = ExplainabilityResult(
            analyzer_id=self.ANALYZER_ID,
            generated_at=datetime.now(timezone.utc),
            model_version=self.MODEL_VERSION,
            crawl=CrawlExplanation(source=result.source, items=item_explanations),
            errors=errors,
        )
        payload = explainability_result.to_dict()
        payload["statistics"] = window_stats or {}
        payload["rule_version"] = self._decision_engine.RULE_VERSION
        payload["audit_logs"] = [entry.to_dict() for entry in audit_logs]
        payload["runtime_engines"] = {
            "shap": shap_engine_state,
            "dice": dice_engine_state,
        }
        payload["finance_profile"] = {
            "current_balance": float(
                self._finance_profile.get("current_balance", 1_500_000)
            ),
            "emergency_fund_balance": float(
                self._finance_profile.get("emergency_fund_balance", 600_000)
            ),
            "savebox_balance": float(
                self._finance_profile.get(
                    "savebox_balance",
                    self._finance_profile.get("emergency_fund_balance", 600_000),
                )
            ),
            "expected_card_payment_amount": float(
                self._finance_profile.get("expected_card_payment_amount", 200_000)
            ),
            "days_until_card_due": int(
                self._finance_profile.get("days_until_card_due", 14)
            ),
        }
        return payload

    def _normalize_counterfactual_messages(
        self, counterfactuals: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for counterfactual in counterfactuals:
            if not isinstance(counterfactual, dict):
                continue
            item = dict(counterfactual)
            item["message"] = self._korean_counterfactual_message(item)
            normalized.append(item)
        return normalized

    @staticmethod
    def _stabilize_counterfactual_suggestions(
        counterfactuals: list[dict[str, Any]],
        *,
        price_value: int | None,
        monthly_spending_30d: float,
        savebox_balance: float,
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> list[dict[str, Any]]:
        avg_price_raw = ((window_stats or {}).get("30d", {}) or {}).get("avg_price")
        avg_price_30d = (
            float(avg_price_raw)
            if isinstance(avg_price_raw, (int, float)) and float(avg_price_raw) > 0
            else 0.0
        )
        if avg_price_30d > 0:
            target_after_purchase = max(avg_price_30d * 15.0, 0.0)
        else:
            target_after_purchase = max(float(monthly_spending_30d) * 0.5, 0.0)
        projected_after_purchase = float(savebox_balance) - float(price_value or 0)
        stable_required_delta_raw = max(target_after_purchase - projected_after_purchase, 0.0)
        stable_required_delta = int(
            round(stable_required_delta_raw / 10_000.0) * 10_000
        )
        stable_required_delta = max(stable_required_delta, 0)
        stable_threshold = float(max(float(savebox_balance) + stable_required_delta, 0.0))

        normalized: list[dict[str, Any]] = []
        emergency_template: dict[str, Any] | None = None
        for counterfactual in counterfactuals:
            if not isinstance(counterfactual, dict):
                continue
            item = dict(counterfactual)
            raw_change = item.get("suggested_change", 0)
            try:
                quantized_change = int(round(max(float(raw_change), 0.0) / 10_000.0) * 10_000)
            except (TypeError, ValueError):
                quantized_change = 0
            item["suggested_change"] = quantized_change
            if (
                str(item.get("variable", "")) == "emergency_buffer"
                and str(item.get("action", "")) == "increase"
            ):
                emergency_template = item if emergency_template is None else emergency_template
                continue
            normalized.append(item)

        if stable_required_delta > 0:
            emergency_item = (
                dict(emergency_template)
                if emergency_template is not None
                else {
                    "type": "dice",
                    "variable": "emergency_buffer",
                    "action": "increase",
                }
            )
            emergency_item["suggested_change"] = stable_required_delta
            emergency_item["threshold"] = stable_threshold
            emergency_item["stabilized_by"] = "savebox_avg30d_rule_v2"
            normalized.append(emergency_item)

        def _priority(item: dict[str, Any]) -> tuple[int, int, str, str]:
            variable = str(item.get("variable", ""))
            action = str(item.get("action", ""))
            if variable == "emergency_buffer" and action == "increase":
                base = 0
            elif variable == "available_budget" and action == "increase":
                base = 1
            elif variable == "current_effective_price" and action == "decrease":
                base = 2
            else:
                base = 9
            try:
                delta = max(int(float(item.get("suggested_change", 0))), 0)
            except (TypeError, ValueError):
                delta = 0
            return (base, delta, variable, action)

        normalized.sort(key=_priority)
        if len(normalized) == 0:
            return [
                {
                    "type": "dice",
                    "variable": "current_effective_price",
                    "action": "wait_for_better_price",
                    "suggested_change": 0,
                    "threshold": float(price_value or 0),
                    "stabilized_by": "savebox_avg30d_rule_v2",
                }
            ]
        return normalized[:3]

    @staticmethod
    def _korean_counterfactual_message(counterfactual: dict[str, Any]) -> str:
        action = str(counterfactual.get("action", ""))
        variable = str(counterfactual.get("variable", ""))
        suggested_change = counterfactual.get("suggested_change", 0)

        delta: int
        try:
            delta = max(int(float(suggested_change)), 0)
        except (TypeError, ValueError):
            delta = 0

        if action == "decrease" and variable == "current_effective_price":
            return (
                f"가격을 약 {delta:,}원 낮추면 구매 판단이 개선될 수 있습니다."
                if delta > 0
                else "가격 조건이 개선되면 구매 판단이 나아질 수 있습니다."
            )

        if action == "increase" and variable == "available_budget":
            return (
                f"가용예산을 약 {delta:,}원 늘리면 구매 판단이 개선될 수 있습니다."
                if delta > 0
                else "가용예산이 늘어나면 구매 판단이 나아질 수 있습니다."
            )

        if action == "increase" and variable == "emergency_buffer":
            return (
                f"비상자금을 약 {delta:,}원 늘리면 리스크가 완화될 수 있습니다."
                if delta > 0
                else "비상자금이 늘어나면 구매 리스크가 완화될 수 있습니다."
            )

        if action == "wait_for_better_price":
            return (
                "현재 조건에서는 큰 변화가 없어 가격/예산 변동 후 재평가를 권장합니다."
            )

        return "구매 조건을 조정한 뒤 다시 평가하면 더 안정적인 판단이 가능합니다."

    def _build_feature_scores(
        self,
        features: dict[str, Any],
        *,
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> dict[str, float]:
        missing_fields = features.get("missing_fields", [])
        if not isinstance(missing_fields, list):
            raise ValueError("missing_fields must be a list")
        blocking_fields = {"price", "url_domain"}
        unresolved = sorted(
            field for field in missing_fields if str(field) in blocking_fields
        )
        if len(unresolved) > 0:
            missing = ",".join(str(field) for field in unresolved)
            raise ValueError(f"deal missing required fields: {missing}")

        price_raw = features.get("price_int")
        price_int = int(price_raw) if isinstance(price_raw, int) else 0
        if price_int <= 0:
            raise ValueError("deal missing required fields: price")
        current_price_score = (
            1.0 / (1.0 + (price_int / 100_000.0)) if price_int > 0 else 0.0
        )

        monthly_spending_30d = self._monthly_spending_30d(window_stats)
        current_balance = float(self._finance_profile.get("current_balance", 1_500_000))
        emergency_fund_balance = float(
            self._finance_profile.get("emergency_fund_balance", 600_000)
        )
        savebox_balance = float(
            self._finance_profile.get("savebox_balance", emergency_fund_balance)
        )
        days_until_card_due = int(self._finance_profile.get("days_until_card_due", 14))

        avg_price_30d = ((window_stats or {}).get("30d", {}) or {}).get("avg_price")
        relative_price_score = 0.0
        if isinstance(avg_price_30d, (int, float)) and float(avg_price_30d) > 0:
            ratio = float(price_int) / float(avg_price_30d)
            relative_price_score = max(min(1.5 - ratio, 1.0), -1.0)
        price_model_gap_score_raw = self._price_model_signal.get(
            "price_model_gap_score", 0.0
        )
        try:
            price_model_gap_score = float(price_model_gap_score_raw)
        except (TypeError, ValueError):
            price_model_gap_score = 0.0
        price_model_gap_score = max(min(price_model_gap_score, 1.0), -1.0)
        relative_price_score = (relative_price_score * 0.7) + (
            price_model_gap_score * 0.3
        )
        finance_model_risk_raw = self._finance_model_signal.get(
            "finance_model_risk_score", 0.0
        )
        finance_model_affordability_raw = self._finance_model_signal.get(
            "finance_model_affordability_score",
            0.0,
        )
        try:
            finance_model_risk_score = float(finance_model_risk_raw)
        except (TypeError, ValueError):
            finance_model_risk_score = 0.0
        try:
            finance_model_affordability_score = float(finance_model_affordability_raw)
        except (TypeError, ValueError):
            finance_model_affordability_score = 0.0
        finance_model_risk_score = max(min(finance_model_risk_score, 1.0), -1.0)
        finance_model_affordability_score = max(
            min(finance_model_affordability_score, 1.0),
            -1.0,
        )

        return {
            "current_price": current_price_score,
            "avg_price_30d": relative_price_score,
            "price_model_gap_score": price_model_gap_score,
            "finance_model_risk_score": finance_model_risk_score,
            "finance_model_affordability_score": finance_model_affordability_score,
            "product_price_vs_monthly_spending": (
                (price_int / monthly_spending_30d) if monthly_spending_30d > 0 else 1.0
            ),
            "emergency_fund_balance": emergency_fund_balance
            / max(monthly_spending_30d, 1.0),
            "projected_balance_after_purchase": (savebox_balance - price_int)
            / max(monthly_spending_30d, 1.0),
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

    def _build_error(self, *, exc: Exception, item_id: str) -> AnalysisError:
        if isinstance(exc, ValueError):
            code = "XAI_ITEM_VALIDATION_FAILED"
            message = "항목 검증에 실패했습니다"
        else:
            code = "XAI_ANALYSIS_FAILED"
            message = "분석 처리에 실패했습니다"
        return AnalysisError(code=code, message=message, item_id=item_id)
