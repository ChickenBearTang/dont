from __future__ import annotations

from hashlib import sha256
from typing import Any

from .decision_engine import DecisionOutcome
from .types import ItemExplanation, XAIContracts


class ExplanationEngine:
    def build_item_explanation(
        self,
        *,
        item_id: str,
        reasons: list[dict[str, Any]],
        feature_scores: dict[str, float],
        observed_features: dict[str, Any],
        decision_outcome: DecisionOutcome,
        counterfactuals: list[dict[str, Any]],
        polished_summary: str,
    ) -> ItemExplanation:
        filtered_reasons: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for reason in reasons:
            feature_name = str(reason.get("feature", ""))
            reason_code = str(reason.get("reason_code", ""))
            if feature_name not in feature_scores:
                continue
            if reason_code == "" or reason_code in seen_codes:
                continue
            seen_codes.add(reason_code)
            filtered_reasons.append(reason)
            if len(filtered_reasons) >= XAIContracts.MAX_CONSUMER_REASONS:
                break

        reason_codes = [
            str(reason.get("reason_code", "")) for reason in filtered_reasons
        ]
        reason_texts = [
            str(reason.get("reason_text", "")) for reason in filtered_reasons
        ]

        supporting_evidence = [
            {
                "feature": feature_name,
                "score": float(feature_scores[feature_name]),
                "observed_value": observed_features.get(feature_name),
            }
            for feature_name in feature_scores.keys()
            if feature_name
            in {str(reason.get("feature", "")) for reason in filtered_reasons}
        ]

        return ItemExplanation(
            item_id=item_id,
            decision=decision_outcome.final_decision,
            decision_confidence=decision_outcome.decision_confidence,
            reasons=filtered_reasons,
            reason_codes=reason_codes,
            reason_texts=reason_texts,
            supporting_evidence=supporting_evidence,
            counterfactual_conditions=counterfactuals,
            counterfactuals=counterfactuals,
            user_options=self._user_options(decision_outcome.final_decision),
            rule_version="financial-purchase-copilot-xai-rules-v1",
            data_snapshot_id=self._snapshot_id(
                item_id=item_id, feature_scores=feature_scores
            ),
            polished_summary=polished_summary,
        )

    @staticmethod
    def _snapshot_id(*, item_id: str, feature_scores: dict[str, float]) -> str:
        joined = "|".join(
            f"{key}:{feature_scores[key]:.6f}" for key in sorted(feature_scores.keys())
        )
        digest = sha256(f"{item_id}|{joined}".encode("utf-8")).hexdigest()[:16]
        return f"snapshot:{digest}"

    @staticmethod
    def _user_options(decision: str) -> list[str]:
        if decision == "BUY_NOW":
            return ["바로 구매", "가격 알림 설정", "예산 재확인"]
        if decision == "WAIT":
            return ["가격 하락 알림", "7일 후 재평가", "대체 상품 비교"]
        if decision == "NOT_RECOMMENDED":
            return ["구매 보류", "예산 상향 후 재검토", "필수 지출 우선"]
        return ["세부 근거 확인", "재무 입력값 수정", "수동 검토 요청"]
