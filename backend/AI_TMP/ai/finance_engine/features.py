"""원본 입력 7개에서 모델 열 10개를 만든다. 파생 비율 정의의 단일 출처.

학습(train), 추론(inference), 합성 데이터(synthetic), 평가(eval) 모두 여기를
거친다. 정의를 바꾸면 한 곳만 고치면 되고, 바꾸면 SCHEMA_VERSION 도 올려야 한다.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .allowlist import RAW_INPUT_NAMES, training_feature_names


def derive_model_features(raw: Mapping[str, Any]) -> dict[str, float]:
    """원본 7개 -> 모델 열 10개(training_feature_names 순서).

    raw 에 파생 열이 이미 들어 있어도 무시하고 다시 계산한다. 낡은 파생 값이
    몰래 학습에 쓰이는 일을 막는다.
    """
    missing = [name for name in RAW_INPUT_NAMES if name not in raw]
    if missing:
        raise ValueError(f"raw input is missing keys required by the model: {missing}")

    values = {name: float(raw[name]) for name in RAW_INPUT_NAMES}
    price = values["product_price"]
    values["product_price_vs_monthly_spending"] = price / max(values["monthly_spending_30d"], 1.0)
    values["projected_balance_after_purchase"] = values["savebox_balance"] - price
    values["product_price_vs_emergency_fund"] = price / max(values["emergency_fund_balance"], 1.0)

    # 정의(위)와 허용목록(allowlist)이 어긋나면 KeyError 로 즉시 드러난다.
    return {name: values[name] for name in training_feature_names()}


def build_feature_frame(rows: Iterable[Mapping[str, Any]]):
    """행들(원본 7개 열을 가진 dict)을 모델 입력 DataFrame 으로 만든다."""
    import pandas as pd

    return pd.DataFrame(
        [derive_model_features(row) for row in rows],
        columns=list(training_feature_names()),
    )
