"""재무 모델의 실제 SHAP 설명.

예전 구현의 문제
    xai/shap_engine.py 는 손으로 만든 점수(비율 등)에 대해 `sum(x)` 라는 가짜 모델의
    SHAP 을 구했다. 기준선이 입력 자신에서 만들어져 결과가 항상 `입력 점수 x 0.25`
    였다. 모델이 무엇을 보고 위험하다고 했는지와는 무관했고, 부호(▲▼)도 의미가
    없었다.

지금 구현
    학습된 재무 모델(LightGBM/CatBoost)에 TreeExplainer 를 쓴다. 값은 모델이 'high'
    (위험) 구간이라고 판단하는 정도(raw margin)에 각 입력이 얼마나 기여했는가다.
      - 양수: 위험을 높인다 / 음수: 위험을 낮춘다.
      - 합 + 기준값 = 모델의 high raw margin (가산성, 테스트로 고정).
    '기준'은 20~30대 유형별 합성 인구(personas.py) 100명이다. 즉 "평범한 20~30대에
    비해 이 사람의 어떤 값이 위험을 높이나/낮추나"를 말한다. 기준 인구는 가정값이다.

묶음(그룹)
    모델 열 10개는 서로 겹친다(가격이 5개 열에 들어 있다). 열마다 따로 보여주면
    같은 원인이 쪼개져 보이므로, 사용자에게는 의미가 같은 열끼리 합쳐 4개 요인으로
    보여준다. Shapley 값은 합쳐도 성립한다.

부호 규칙 (explain_finance_signal 의 반환값)
    사용자에게 보이는 점수는 '구매에 유리한 정도'다. 위험 기여도의 부호를 뒤집는다.
      양수 = 구매에 유리 / 음수 = 구매에 불리.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

from .allowlist import training_feature_names
from .features import build_feature_frame
from .inference import build_finance_inference_payload, load_validated_artifact
from .personas import PERSONA_PARAMS_VERSION, generate_training_rows

# 묶음 이름 = 사용자 설명 카탈로그(xai/purchase_core/reasons.py)의 피처 키.
# 모델 열 10개를 빠짐없이, 겹치지 않게 나눈다 (테스트로 고정).
EXPLANATION_GROUPS: dict[str, tuple[str, ...]] = {
    # 가격이 월 지출에 비해 부담스러운가
    "product_price_vs_monthly_spending": (
        "product_price",
        "product_price_vs_monthly_spending",
        "monthly_spending_30d",
    ),
    # 사고 난 뒤 여유 자금이 남는가
    "projected_balance_after_purchase": (
        "projected_balance_after_purchase",
        "savebox_balance",
    ),
    # 비상자금이 충분한가
    "emergency_fund_balance": (
        "emergency_fund_balance",
        "product_price_vs_emergency_fund",
    ),
    # 카드 결제 부담이 단기 현금흐름을 누르는가
    "days_until_card_due": (
        "days_until_card_due",
        "expected_card_payment_amount",
        "current_balance",
    ),
}

BACKEND_NAME = "shap_tree"
_BACKGROUND_ROWS = 100
_BACKGROUND_SEED = 0
_TARGET_CLASS = "high"


@lru_cache(maxsize=1)
def _background_frame() -> Any:
    rows = generate_training_rows("persona", row_count=_BACKGROUND_ROWS, seed=_BACKGROUND_SEED)
    return build_feature_frame(rows)


def _high_class_index(model: Any) -> int:
    classes = [str(c) for c in model.classes_]
    if _TARGET_CLASS not in classes:
        raise ValueError(f"model has no {_TARGET_CLASS!r} class: {classes}")
    return classes.index(_TARGET_CLASS)


def _class_column(raw: Any, class_index: int) -> Any:
    import numpy as np

    return np.asarray(raw)[:, class_index]


def _raw_margin_function(model: Any, class_index: int):
    """DataFrame -> 'high' 클래스의 raw margin. 모델 종류별로 한 곳에서 맞춘다."""
    module = type(model).__module__
    if module.startswith("lightgbm"):
        return lambda frame: _class_column(model.predict(frame, raw_score=True), class_index)
    if module.startswith("catboost"):
        return lambda frame: _class_column(model.predict(frame, prediction_type="RawFormulaVal"), class_index)
    raise ValueError(f"unsupported model family for explanation: {module}")


def explain_model_features(model: Any, payload: Mapping[str, float]) -> tuple[dict[str, float], float]:
    """모델 열 10개 각각의 'high 위험' 기여도와 기준값을 돌려준다.

    payload 는 원본 입력 7개다 (파생 3개는 여기서 계산한다).

    - LightGBM : TreeExplainer(interventional). 빠르다(약 0.3초).
    - 그 밖(CatBoost): 모델에 무관한 정확한 Shapley(ExactExplainer). 10개 열이라
      2^10 가지 조합을 모두 계산하므로 몇 초 걸린다. shap 의 CatBoost 트리 해석기는
      이 환경에서 프로세스를 비정상 종료시켜 쓰지 않는다.
      두 방식은 같은 기준 인구에서 같은 값을 낸다 (테스트로 고정).
    """
    import numpy as np
    import pandas as pd
    import shap

    frame = build_feature_frame([payload])
    index = _high_class_index(model)
    names = list(frame.columns)

    if type(model).__module__.startswith("lightgbm"):
        explainer = shap.TreeExplainer(
            model,
            data=_background_frame(),
            feature_perturbation="interventional",
            model_output="raw",
        )
        values = explainer.shap_values(frame)
        # shap 버전에 따라 (샘플, 열, 클래스) 배열이거나 클래스별 배열의 목록이다.
        if isinstance(values, list):
            row = np.asarray(values[index])[0]
        else:
            arr = np.asarray(values)
            row = arr[0, :, index] if arr.ndim == 3 else arr[0]
        base = float(np.ravel(explainer.expected_value)[index])
    else:
        margin = _raw_margin_function(model, index)
        explainer = shap.explainers.ExactExplainer(
            lambda data: margin(pd.DataFrame(data, columns=names)),
            _background_frame(),
        )
        explanation = explainer(frame)
        row = np.asarray(explanation.values)[0]
        base = float(np.ravel(explanation.base_values)[0])

    return {name: float(row[i]) for i, name in enumerate(names)}, base


def group_contributions(feature_contributions: Mapping[str, float]) -> dict[str, float]:
    """열별 기여도를 의미 묶음별로 합친다."""
    return {
        group: float(sum(feature_contributions[name] for name in members))
        for group, members in EXPLANATION_GROUPS.items()
    }


def explain_finance_signal(
    *,
    current_price: int | None,
    finance_profile: Mapping[str, float | int],
    explicit_model_path: str | None = None,
) -> tuple[dict[str, float], dict[str, Any]]:
    """사용자에게 보여줄 재무 요인 점수. (묶음별 '구매 유리도', 상태).

    실패하면 ({}, 사유) 이다. 호출하는 쪽은 {} 를 '설명 없음'으로 다뤄야 하며,
    가짜 점수로 채우면 안 된다.
    """
    artifact, model_path, failure = load_validated_artifact(explicit_model_path)
    if failure is not None or artifact is None:
        return {}, failure or {"enabled": False, "backend": "fallback", "reason": "model_load_failed"}

    payload = build_finance_inference_payload(
        current_price=current_price,
        finance_profile=dict(finance_profile),
    )
    try:
        features, base = explain_model_features(artifact.model, payload)
    except ImportError:
        return {}, {"enabled": False, "backend": "fallback", "reason": "shap_unavailable", "artifact_path": model_path}
    except Exception as exc:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "shap_error",
            "artifact_path": model_path,
            "error_type": type(exc).__name__,
        }

    risk = group_contributions(features)
    favorability = {group: -value for group, value in risk.items()}
    high_margin = base + sum(features.values())
    return favorability, {
        "enabled": True,
        "backend": BACKEND_NAME,
        "feature_count": len(training_feature_names()),
        "group_count": len(favorability),
        "reference_population": PERSONA_PARAMS_VERSION,
        "base_margin": base,
        "high_margin": high_margin,
        "artifact_path": model_path,
    }
