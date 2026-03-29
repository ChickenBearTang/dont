from __future__ import annotations


def apply_decision_rule(
    price_bucket: str,
    expected_drop_prob: float,
    finance_risk_bucket: str,
    affordability_score: float,
) -> str:
    if finance_risk_bucket == "high":
        return "HOLD"
    if (
        price_bucket == "cheap"
        and finance_risk_bucket == "low"
        and affordability_score >= 0.55
    ):
        return "BUY_NOW"

    wait_threshold = 0.45 if affordability_score < 0.4 else 0.6
    if expected_drop_prob >= wait_threshold:
        return "WAIT"
    return "REVIEW"


def normalize_decision_label(label: str) -> str:
    if label == "HOLD":
        return "NOT_RECOMMENDED"
    return label
