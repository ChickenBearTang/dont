from __future__ import annotations

import importlib
from typing import Any

from .allowlist import TARGET_NAME, training_feature_names

DEFAULT_LGBM_PARAMS: dict[str, Any] = {
    "objective": "multiclass",
    "n_estimators": 250,
    "learning_rate": 0.06,
    "num_leaves": 31,
    "min_data_in_leaf": 40,
    "feature_fraction": 0.85,
    "bagging_fraction": 0.85,
    "bagging_freq": 1,
    "lambda_l2": 3.0,
    "random_state": 42,
    "force_col_wise": True,
    "verbose": -1,
}


def _ensure_lightgbm() -> Any:
    try:
        return importlib.import_module("lightgbm")
    except ModuleNotFoundError as exc:
        raise RuntimeError("lightgbm is required for finance model training") from exc


def train_finance_model_lgbm(
    rows: list[dict[str, Any]],
    *,
    target_name: str = TARGET_NAME,
    params: dict[str, Any] | None = None,
) -> Any:
    if not rows:
        raise ValueError("training rows must not be empty")

    feature_names = list(training_feature_names())
    payload: list[dict[str, Any]] = []
    labels: list[str] = []
    for row in rows:
        payload.append({name: float(row[name]) for name in feature_names})
        label = row.get(target_name)
        if not isinstance(label, str) or label.strip() == "":
            raise ValueError(f"row missing target label: {target_name}")
        labels.append(label.strip())

    pd = importlib.import_module("pandas")
    frame = pd.DataFrame(payload, columns=feature_names)
    lgb = _ensure_lightgbm()

    model = lgb.LGBMClassifier(**{**DEFAULT_LGBM_PARAMS, **(params or {})})
    model.fit(frame, labels)
    return model
