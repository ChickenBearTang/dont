from __future__ import annotations

import copy
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Callable, Mapping

from ..models import CrawlResult
from .audit_log import XAIAuditLogEntry, build_model_input_vector_hash
from .decision_engine import DecisionEngine
from .explanation_engine import ExplanationEngine
from .counterfactual_text import polish_counterfactuals
from .budget_rule import BudgetAssessment, BudgetStatus, assess_budget, explanation_score
from .input_contract import Origin, RawField, ResolvedFinanceProfile, resolve_finance_profile
from .model_counterfactual import ModelCounterfactualEngine, Outcome
from .types import (
    AnalysisError,
    CrawlExplanation,
    ExplainabilityResult,
    ItemExplanation,
)

_BUDGET_INPUT_PREFIX = "budget_ratio_"
# 이 필드가 기본값(앞단이 안 보냄)이면 예산을 판단하지 않는다. (필드, 사유 코드)
_BUDGET_REQUIRED_FIELDS = (
    ("available_fixed_income", "income_not_provided_by_upstream"),
    ("available_fixed_expense", "fixed_expense_not_provided_by_upstream"),
    ("monthly_spending_30d", "spending_not_provided_by_upstream"),
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
        finance_profile: dict[str, float | int] | ResolvedFinanceProfile | None = None,
        price_model_signal: dict[str, float] | None = None,
        finance_model_signal: dict[str, float | str] | None = None,
        finance_explanation: Mapping[str, float] | None = None,
        finance_explanation_state: Mapping[str, Any] | None = None,
        scenario_signals: Callable[
            [int | None, Mapping[str, float]], tuple[dict[str, Any], dict[str, Any]]
        ]
        | None = None,
    ) -> None:
        """finance_explanation 이 주어지면(빈 dict 포함) '부호 있는 설명' 모드다.

        - 값: 재무 요인별 '구매에 유리한 정도'(finance_engine.explain.explain_finance_signal).
          양수 = 유리, 음수 = 불리. 문구도 부호에 맞춰 나간다.
        - 빈 dict 는 '설명을 만들지 못했다'는 뜻이다. 가짜 점수로 채우지 않고 재무
          요인을 설명에서 뺀다.
        - 없으면(None) 예전 방식이다. 판단 규칙용 점수에 가짜 SHAP 을 씌워 설명한다.
          부호가 의미 없어서 CLI/진단용으로만 남겨 둔다.

        scenario_signals 가 주어지면 '무엇을 바꾸면 되나'를 모델 기반 탐색으로 만든다.
        (가격, 재무 프로필) -> (가격 모델 신호, 재무 모델 신호) 를 돌려주는 함수로, 모델을
        다시 돌려 바꾼 조건에서의 판단을 실제로 확인하는 데 쓴다. 없으면 예전
        규칙/DiCE 방식이다.
        """
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
        self._resolved_profile = self._resolve_profile(finance_profile)
        # 계약을 통과해 모든 키가 채워진 상태다. 아래의 읽기는 .get(키, 기본값)이
        # 아니라 직접 인덱싱이며, 기본값 표는 input_contract 에만 존재한다.
        self._finance_profile = self._resolved_profile.as_dict()
        self._price_model_signal = price_model_signal or {}
        self._finance_model_signal = finance_model_signal or {}
        self._finance_explanation: dict[str, float] | None = (
            None
            if finance_explanation is None
            else {str(k): float(v) for k, v in finance_explanation.items()}
        )
        self._finance_explanation_state = dict(finance_explanation_state or {})
        self._scenario_signals = scenario_signals

    @staticmethod
    def _resolve_profile(
        finance_profile: dict[str, float | int] | ResolvedFinanceProfile | None,
    ) -> ResolvedFinanceProfile:
        """생성자 인자를 계약을 통과한 프로필로 확정한다.

        ResolvedFinanceProfile 은 출처 정보를 보존한 채 그대로 쓴다(운영 경로).
        dict / None 은 기존 호출부(CLI, 진단 스크립트, 단위 테스트) 호환용이라
        lenient 모드로 처리한다: 없는 필드는 예전과 같은 값으로 채우되 이제는
        origin=default 로 기록된다. 깨진 값과 모르는 필드는 여전히 거부한다.
        """
        if isinstance(finance_profile, ResolvedFinanceProfile):
            return finance_profile
        raw = {
            name: RawField(value) for name, value in (finance_profile or {}).items()
        }
        return resolve_finance_profile(raw, strict=False)

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
        budgets: dict[str, dict[str, Any]] = {}
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
                budget = self._assess_budget(features.get("price_int"))
                budgets[deal.url] = budget.to_dict()
                if self._finance_explanation is not None:
                    shap_scores, reasons, shap_engine_state = self._signed_explanation(
                        features,
                        window_stats=window_stats,
                        top_k=requested_top_k,
                    )
                else:
                    # budget_ratio_* 는 규칙 엔진 입력일 뿐 요인이 아니다. 요인은 아래에서 따로 넣는다.
                    shap_scores = {
                        name: value
                        for name, value in feature_scores.items()
                        if not name.startswith(_BUDGET_INPUT_PREFIX)
                    }
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
                shap_scores, reasons = self._with_budget_reason(
                    budget, shap_scores, reasons
                )
                decision_outcome = self._decision_engine.decide(feature_scores)
                price_int = features.get("price_int")
                price_value = price_int if isinstance(price_int, int) else None
                monthly_spending_30d = self._monthly_spending_30d()
                emergency_fund_balance = float(
                    self._finance_profile["emergency_fund_balance"]
                )
                savebox_balance = float(self._finance_profile["savebox_balance"])
                days_until_card_due = int(self._finance_profile["days_until_card_due"])
                expected_card_payment_amount = float(
                    self._finance_profile["expected_card_payment_amount"]
                )

                counterfactuals: list[dict[str, Any]] = []
                if self._scenario_signals is not None:
                    counterfactuals, dice_engine_state = self._model_counterfactuals(
                        current_decision=decision_outcome.final_decision,
                        price_value=price_value,
                        window_stats=window_stats,
                    )
                else:
                    if hasattr(self._dice_counterfactual_engine, "suggest"):
                        suggested = self._dice_counterfactual_engine.suggest(
                            price_int=price_value,
                            monthly_spending_30d=monthly_spending_30d,
                            emergency_fund_balance=emergency_fund_balance,
                            current_balance=float(self._finance_profile["current_balance"]),
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
                suggestion_text = (
                    str(counterfactuals[0].get("message", "가격/재무 상태 재평가"))
                    if len(counterfactuals) > 0
                    else "가격/재무 상태 재평가"
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
                    "budget_zone_usage": (
                        round(budget.ratio_after, 4)
                        if budget.ratio_after is not None
                        else None
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
        # 5·3·2 예산 평가. 항목(가격)마다 다르므로 item_id 로 찾는다.
        payload["budgets"] = budgets
        payload["runtime_engines"] = {
            "shap": shap_engine_state,
            "dice": dice_engine_state,
        }
        payload["finance_profile"] = {
            "current_balance": float(self._finance_profile["current_balance"]),
            "emergency_fund_balance": float(
                self._finance_profile["emergency_fund_balance"]
            ),
            "savebox_balance": float(self._finance_profile["savebox_balance"]),
            "expected_card_payment_amount": float(
                self._finance_profile["expected_card_payment_amount"]
            ),
            "days_until_card_due": int(self._finance_profile["days_until_card_due"]),
        }
        # 위 값이 실제 입력인지 기본값인지. default_fallback_rate 는 운영에서
        # 필수 필드 기준 0 이어야 하는 지표다.
        payload["input_contract"] = self._resolved_profile.to_report()
        return payload

    def _assess_budget(self, price: object) -> BudgetAssessment:
        """5·3·2 예산 적합도. 소득/고정지출/월 지출 중 하나라도 기본값이면 판단하지 않는다.

        기본값(예: 소득 100만 원)으로 사용률을 만들면 근거 없는 '한도 초과'나 '여유'가
        나온다. 앞단이 실제 값을 보내기 전까지는 판단 불가로 두고 사유를 알린다.
        """
        origins = self._resolved_profile.origins
        for field, reason in _BUDGET_REQUIRED_FIELDS:
            if origins.get(field) == Origin.DEFAULT:
                return BudgetAssessment(status=BudgetStatus.UNAVAILABLE, reason=reason)
        return assess_budget(
            monthly_income=self._finance_profile["available_fixed_income"],
            fixed_expense=self._finance_profile["available_fixed_expense"],
            variable_spending_30d=self._finance_profile["monthly_spending_30d"],
            price=price,
            emergency_fund_balance=self._finance_profile["emergency_fund_balance"],
        )

    def _with_budget_reason(
        self,
        budget: BudgetAssessment,
        scores: dict[str, float],
        reasons: list[dict[str, Any]],
    ) -> tuple[dict[str, float], list[dict[str, Any]]]:
        """예산 사유를 요인 목록에 하나 더한다 (top_k 와 별개로 추가).

        한도를 넘거나 빠듯하면 판단의 이유이므로 맨 앞에, 여유가 있으면 맨 뒤에 둔다.
        문구는 점수 부호가 아니라 상태로 정한다.
        """
        from ai.xai.purchase_core.reasons import BUDGET_STATUS_REASON_TEXT

        score = explanation_score(budget)
        if score is None:
            return scores, reasons
        reason = self._reasoning_engine.analyze(
            {"budget_zone_usage": score}, top_k=1, signed=True
        )[0]
        reason["reason_text"] = BUDGET_STATUS_REASON_TEXT[budget.status.value]
        merged_scores = {**scores, "budget_zone_usage": score}
        if budget.status is BudgetStatus.WITHIN:
            return merged_scores, [*reasons, reason]
        return merged_scores, [reason, *reasons]

    def _signed_explanation(
        self,
        features: dict[str, Any],
        *,
        window_stats: dict[str, dict[str, float | int | None]] | None,
        top_k: int,
    ) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, Any]]:
        """부호 있는 설명 점수와 이유. 점수는 모두 '구매에 유리한 정도'다.

        - 재무 요인: 학습된 재무 모델의 실제 SHAP (service 가 계산해 넘겨준다).
        - 가격 요인: 30일 평균가 대비 위치, 가격 모델이 본 적정가와의 차이. 둘 다
          0 을 기준으로 양수가 '싸다'(유리)가 되도록 중심을 맞춘 값이다.
        두 묶음은 단위가 달라(SHAP 은 로짓, 가격은 -1~1) 한 줄로 순위를 매기지 않는다.
        가격 요인에 최대 (top_k - 2)개 자리를 주고 나머지는 재무 요인이 채운다.
        """
        from ai.xai.purchase_core.reasons import SIGNED_NEUTRAL_BAND

        finance_scores = dict(self._finance_explanation or {})

        price_scores: dict[str, float] = {}
        price_int = features.get("price_int")
        avg_price = ((window_stats or {}).get("30d", {}) or {}).get("avg_price")
        if (
            isinstance(price_int, int)
            and price_int > 0
            and isinstance(avg_price, (int, float))
            and float(avg_price) > 0
        ):
            ratio = float(price_int) / float(avg_price)
            price_scores["avg_price_30d"] = max(min(1.0 - ratio, 1.0), -1.0)
        gap_raw = self._price_model_signal.get("price_model_gap_score")
        if isinstance(gap_raw, (int, float)):
            price_scores["price_model_gap_score"] = max(min(float(gap_raw), 1.0), -1.0)
        # 영향이 없는 가격 요인은 자리를 차지하지 않게 뺀다.
        price_scores = {
            name: value
            for name, value in price_scores.items()
            if abs(value) > SIGNED_NEUTRAL_BAND
        }

        if finance_scores:
            price_slots = min(len(price_scores), max(0, top_k - 2))
        else:
            price_slots = min(len(price_scores), top_k)
        finance_slots = min(len(finance_scores), top_k - price_slots)

        reasons: list[dict[str, Any]] = []
        if finance_slots > 0:
            reasons += self._reasoning_engine.analyze(
                finance_scores, top_k=finance_slots, signed=True
            )
        if price_slots > 0:
            reasons += self._reasoning_engine.analyze(
                price_scores, top_k=price_slots, signed=True
            )

        explanation_scores = {**finance_scores, **price_scores}
        state_src = self._finance_explanation_state
        state: dict[str, Any] = {
            "enabled": bool(finance_scores) and bool(state_src.get("enabled", True)),
            "backend": str(state_src.get("backend", "shap_tree" if finance_scores else "fallback")),
        }
        if "reason" in state_src:
            state["reason"] = str(state_src["reason"])
        if finance_scores:
            state["feature_count"] = int(state_src.get("feature_count", len(finance_scores)))
        elif "reason" not in state:
            state["reason"] = "finance_explanation_unavailable"
        return explanation_scores, reasons, state

    def decide_scenario(
        self,
        *,
        price_value: int | None,
        overrides: Mapping[str, float],
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> Outcome:
        """바꾼 조건에서 구매 판단이 어떻게 되는지 실제 파이프라인으로 다시 계산한다.

        모델(가격/재무)을 다시 돌리고, 같은 점수 계산과 같은 규칙 엔진을 쓴다.
        overrides 의 키: product_price, current_balance, emergency_fund_balance,
        savebox_balance.
        """
        if self._scenario_signals is None:
            raise RuntimeError("scenario_signals is not configured")
        scenario_price = int(overrides.get("product_price", price_value or 0))
        profile = dict(self._finance_profile)
        for name in ("current_balance", "emergency_fund_balance", "savebox_balance"):
            if name in overrides:
                profile[name] = float(overrides[name])

        price_signal, finance_signal = self._scenario_signals(scenario_price, profile)
        scenario = copy.copy(self)  # 모델 신호와 프로필만 바꾼 얕은 복사본
        scenario._finance_profile = profile
        scenario._price_model_signal = price_signal or {}
        scenario._finance_model_signal = finance_signal or {}
        scores = scenario._build_feature_scores(
            {"price_int": scenario_price, "missing_fields": []},
            window_stats=window_stats,
        )
        decision = self._decision_engine.decide(scores)
        risk = scores.get("finance_model_risk_score")
        return Outcome(
            decision=decision.final_decision,
            finance_risk_score=float(risk) if isinstance(risk, (int, float)) else None,
        )

    def _model_counterfactuals(
        self,
        *,
        current_decision: str,
        price_value: int | None,
        window_stats: dict[str, dict[str, float | int | None]] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        engine = ModelCounterfactualEngine(
            lambda overrides: self.decide_scenario(
                price_value=price_value, overrides=overrides, window_stats=window_stats
            )
        )
        monthly_spending = self._monthly_spending_30d()
        suggestions, state = engine.suggest(
            current_decision=current_decision,
            price=float(price_value or 0),
            monthly_spending=monthly_spending,
            current_values={
                "current_balance": float(self._finance_profile["current_balance"]),
                "emergency_fund_balance": float(self._finance_profile["emergency_fund_balance"]),
                "savebox_balance": float(self._finance_profile["savebox_balance"]),
            },
        )
        # 제안의 사실(금액, 판단 변화)은 그대로 두고 문장만 읽기 좋게 다듬는다.
        polished = polish_counterfactuals(
            suggestions,
            current_decision=current_decision,
            monthly_spending=monthly_spending,
            days_until_card_due=int(self._finance_profile["days_until_card_due"]),
            price=float(price_value or 0),
        )
        return polished, state

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

        monthly_spending_30d = self._monthly_spending_30d()
        emergency_fund_balance = float(self._finance_profile["emergency_fund_balance"])
        savebox_balance = float(self._finance_profile["savebox_balance"])
        days_until_card_due = int(self._finance_profile["days_until_card_due"])

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
        # 재무 모델 신호가 '있을 때만' 점수표에 넣는다. 규칙 엔진은 이 키가 있는지로
        # 분기한다(없으면 프로필 기반 휴리스틱). 예전에는 신호가 없어도 0.0 으로 채워서
        # 모델이 죽으면 항상 '위험 없음'으로 판단했다.
        model_scores: dict[str, float] = {}
        for score_name in ("finance_model_risk_score", "finance_model_affordability_score"):
            raw_value = self._finance_model_signal.get(score_name)
            try:
                numeric = float(raw_value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            model_scores[score_name] = max(min(numeric, 1.0), -1.0)

        # 예산 판단이 가능할 때만 점수표에 넣는다. 규칙 엔진은 이 키가 있는지로 분기한다.
        budget = self._assess_budget(price_int)
        budget_scores: dict[str, float] = {}
        if budget.status is not BudgetStatus.UNAVAILABLE:
            budget_scores = {
                "budget_ratio_before": float(budget.ratio_before),  # type: ignore[arg-type]
                "budget_ratio_after": float(budget.ratio_after),  # type: ignore[arg-type]
            }

        return {
            "current_price": current_price_score,
            "avg_price_30d": relative_price_score,
            "price_model_gap_score": price_model_gap_score,
            **model_scores,
            **budget_scores,
            "product_price_vs_monthly_spending": (
                (price_int / monthly_spending_30d) if monthly_spending_30d > 0 else 1.0
            ),
            "emergency_fund_balance": emergency_fund_balance
            / max(monthly_spending_30d, 1.0),
            "projected_balance_after_purchase": (savebox_balance - price_int)
            / max(monthly_spending_30d, 1.0),
            "days_until_card_due": float(days_until_card_due) / 30.0,
        }

    def _monthly_spending_30d(self) -> float:
        """사용자의 최근 30일 지출. 입력 계약을 통과한 값을 그대로 쓴다.

        예전에는 크롤링한 상품의 `평균가 x 건수`로 계산해서 사용자의 실제 소비와
        무관했다. 이제 값의 출처(거래에서 계산 / 기본값)는 input_contract 리포트에
        남는다.
        """
        return max(float(self._finance_profile["monthly_spending_30d"]), 1.0)

    def _build_error(self, *, exc: Exception, item_id: str) -> AnalysisError:
        if isinstance(exc, ValueError):
            code = "XAI_ITEM_VALIDATION_FAILED"
            message = "항목 검증에 실패했습니다"
        else:
            code = "XAI_ANALYSIS_FAILED"
            message = "분석 처리에 실패했습니다"
        return AnalysisError(code=code, message=message, item_id=item_id)
