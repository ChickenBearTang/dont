from __future__ import annotations

SCHEMA_VERSION = "finance-engine-mvp-v1"
TARGET_NAME = "finance_risk_bucket"
CLASS_LABELS: tuple[str, ...] = ("low", "medium", "high")

FEATURE_ALLOWLIST_PHASE1: dict[str, tuple[str, ...]] = {
    "numeric": (
        "current_balance",
        "emergency_fund_balance",
        "expected_card_payment_amount",
        "days_until_card_due",
        "savebox_balance",
        "available_fixed_expense",
        "available_fixed_income",
        "monthly_spending_30d_estimate",
        "product_price",
        "product_price_vs_monthly_spending",
        "projected_balance_after_purchase",
        "product_price_vs_emergency_fund",
    )
}


def training_feature_names() -> tuple[str, ...]:
    return FEATURE_ALLOWLIST_PHASE1["numeric"]
