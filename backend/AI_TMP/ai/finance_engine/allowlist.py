from __future__ import annotations

# 입력과 모델 열은 다르다.
#   입력(raw)  : Spring/요청에서 오는 원본 값 7개. 호출하는 쪽이 알아야 하는 계약이다.
#   모델 열    : 입력 7개 + 모델 '안쪽에서' 계산하는 파생 비율 3개 = 10개.
# 파생 비율을 호출하는 쪽이 아니라 모델 안쪽(features.py 한 곳)에서 계산하는 이유:
#   앞단과 뒷단이 각자 계산하면 정의가 어긋난다. 한 곳에서 계산하면 학습과 추론이
#   같은 정의를 쓰는 것이 구조적으로 보장된다.
#
# 이력
#   v2: 입력을 Spring 이 실제로 보내는 원본 7개로 줄였다. 고정 수입/지출은 Spring 이
#       보내지 않아 운영에서 항상 기본값이었으므로 제거.
#   v3: 파생 비율 3개를 모델 안쪽에서 계산해 모델 열에 다시 넣었다. 입력은 그대로 7개.
# 모델 열이 바뀌었으므로 버전을 올려 옛 아티팩트가 schema_version_mismatch 로
# 거부되게 한다.
SCHEMA_VERSION = "finance-engine-mvp-v3"
TARGET_NAME = "finance_risk_bucket"
CLASS_LABELS: tuple[str, ...] = ("low", "medium", "high")

RAW_INPUT_NAMES: tuple[str, ...] = (
    "current_balance",
    "emergency_fund_balance",
    "savebox_balance",
    "expected_card_payment_amount",
    "days_until_card_due",
    "monthly_spending_30d",
    "product_price",
)

DERIVED_FEATURE_NAMES: tuple[str, ...] = (
    "product_price_vs_monthly_spending",
    "projected_balance_after_purchase",
    "product_price_vs_emergency_fund",
)

FEATURE_ALLOWLIST_PHASE1: dict[str, tuple[str, ...]] = {
    "numeric": RAW_INPUT_NAMES + DERIVED_FEATURE_NAMES,
}


def raw_input_names() -> tuple[str, ...]:
    """호출하는 쪽이 채워야 하는 원본 입력."""
    return RAW_INPUT_NAMES


def training_feature_names() -> tuple[str, ...]:
    """모델이 실제로 보는 열(원본 + 파생). 학습과 추론의 열 순서."""
    return FEATURE_ALLOWLIST_PHASE1["numeric"]
