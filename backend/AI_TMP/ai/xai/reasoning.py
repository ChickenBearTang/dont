from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .purchase_core import reasons as canonical_reasons


@dataclass(frozen=True)
class _ReasonTemplate:
    code: str
    text: str
    source_type: str


class ReasoningEngine:
    _UNKNOWN_REASON_TEMPLATE = _ReasonTemplate(
        code="DECISION_FEATURE_SIGNAL",
        text="핵심 특징 신호가 최종 판단에 반영되었습니다.",
        source_type="feature_score",
    )

    _FALLBACK_REASON: dict[str, Any] = {
        "reason_code": "NO_VALID_FEATURE_SCORES",
        "reason_text": "유효한 특징 점수가 부족하여 기본 판단 근거를 사용했습니다.",
        "feature": None,
        "score": 0.0,
        "source_type": "fallback",
    }

    def analyze(
        self, feature_scores: dict[str, Any], top_k: int
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        if not isinstance(feature_scores, dict) or len(feature_scores) == 0:
            return [self._FALLBACK_REASON.copy()]

        ranked_pairs = canonical_reasons.rank_reason_features(
            feature_scores, top_k=top_k
        )
        if len(ranked_pairs) == 0:
            return [self._FALLBACK_REASON.copy()]

        return [self._build_reason(feature, score) for feature, score in ranked_pairs]

    def _build_reason(self, feature: str, score: float) -> dict[str, Any]:
        reason_item = canonical_reasons.build_reason_item(feature, score)
        template = (
            _ReasonTemplate(
                code=reason_item.reason_code,
                text=reason_item.reason_text,
                source_type=reason_item.source_type,
            )
            if reason_item is not None
            else self._UNKNOWN_REASON_TEMPLATE
        )
        return {
            "reason_code": template.code,
            "reason_text": template.text,
            "feature": feature,
            "score": float(score),
            "abs_score": abs(float(score)),
            "impact_direction": "positive" if score >= 0 else "negative",
            "shap_like_value": float(score),
            "source_type": template.source_type,
        }
