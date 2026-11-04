from __future__ import annotations

# v2: 모델 입력을 Spring 이 실제로 보내는 원본 값 7개로 줄였다.
#   - 제거: available_fixed_income / available_fixed_expense
#       Spring 이 보내지 않아 운영에서 항상 기본값이었다.
#   - 제거: product_price_vs_monthly_spending, projected_balance_after_purchase,
#       product_price_vs_emergency_fund
#       다른 입력의 조합(파생 비율)이라 앞단/뒷단이 각자 계산하면 어긋나고,
#       상관된 피처가 SHAP 기여도를 나눠 설명을 흔든다.
#   - 이름 변경: monthly_spending_30d_estimate -> monthly_spending_30d
#       이제 추정이 아니라 recentTransactions 에서 계산한 값이다.
# 입력이 바뀌었으므로 버전을 올려 옛 아티팩트가 schema_version_mismatch 로
# 거부되게 한다.
SCHEMA_VERSION = "finance-engine-mvp-v2"
TARGET_NAME = "finance_risk_bucket"
CLASS_LABELS: tuple[str, ...] = ("low", "medium", "high")

FEATURE_ALLOWLIST_PHASE1: dict[str, tuple[str, ...]] = {
    "numeric": (
        "current_balance",
        "emergency_fund_balance",
        "savebox_balance",
        "expected_card_payment_amount",
        "days_until_card_due",
        "monthly_spending_30d",
        "product_price",
    )
}


def training_feature_names() -> tuple[str, ...]:
    return FEATURE_ALLOWLIST_PHASE1["numeric"]
