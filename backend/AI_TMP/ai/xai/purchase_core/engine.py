from __future__ import annotations

from .contracts import PurchaseCoreInput, PurchaseCoreResult
from .policy import apply_decision_rule, normalize_decision_label
from .reasons import extract_top_reasons


def evaluate_purchase(input: PurchaseCoreInput) -> PurchaseCoreResult:
    raw_decision = apply_decision_rule(
        price_bucket=input.price_bucket,
        expected_drop_prob=float(input.expected_drop_prob),
        finance_risk_bucket=input.finance_risk_bucket,
        affordability_score=float(input.affordability_score),
    )
    normalized_decision = normalize_decision_label(raw_decision)
    reasons = extract_top_reasons(
        input.feature_scores,
        top_k=input.top_k_reasons,
    )

    return PurchaseCoreResult(
        decision=normalized_decision,
        raw_decision=raw_decision,
        reasons=reasons,
    )
