from __future__ import annotations

from dataclasses import asdict
import importlib
from typing import Any

from .allowlist import FEATURE_ALLOWLIST_PHASE1, training_feature_names
from .schema_models import PriceFeatureSnapshotRow
from .schema_validator import (
    validate_schema_version,
    validate_training_columns,
)

DEFAULT_LGBM_PARAMS: dict[str, Any] = {
    "objective": "regression",
    "metric": "l2",
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 5.0,
    "random_state": 42,
    "force_col_wise": True,
}


def _ensure_lightgbm() -> Any:
    try:
        lgb = importlib.import_module("lightgbm")
    except ModuleNotFoundError as exc:
        raise RuntimeError("lightgbm is required for mvp_v1_5 training") from exc
    return lgb


def train_mvp_v1_5(
    rows: list[PriceFeatureSnapshotRow],
    *,
    target_name: str = "current_effective_price",
    params: dict[str, Any] | None = None,
) -> Any:
    if not rows:
        raise ValueError("training rows must not be empty")

    validate_schema_version(rows[0].schema_version)
    feature_names = list(training_feature_names())
    validate_training_columns(feature_names)
    numeric_features = list(FEATURE_ALLOWLIST_PHASE1["numeric"])
    categorical_features = list(FEATURE_ALLOWLIST_PHASE1["categorical"])

    feature_payloads: list[dict[str, Any]] = []
    target: list[float] = []

    for row in rows:
        payload = asdict(row)
        validate_schema_version(str(payload["schema_version"]))
        feature_payloads.append({name: payload[name] for name in feature_names})
        target.append(float(payload[target_name]))

    lgb = _ensure_lightgbm()
    pd = importlib.import_module("pandas")
    feature_frame = pd.DataFrame(feature_payloads, columns=feature_names)
    for column in numeric_features:
        if column in feature_frame.columns:
            feature_frame[column] = pd.to_numeric(feature_frame[column], errors="coerce")
    for column in categorical_features:
        if column in feature_frame.columns:
            feature_frame[column] = feature_frame[column].astype("category")

    model = lgb.LGBMRegressor(**{**DEFAULT_LGBM_PARAMS, **(params or {})})
    model.fit(
        feature_frame,
        target,
        categorical_feature=categorical_features,
    )
    return model
