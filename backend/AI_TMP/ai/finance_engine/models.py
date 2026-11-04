"""재무 모델 후보: LightGBM 과 CatBoost.

두 후보를 모두 유지한다. 어느 쪽을 쓸지는 실제 결과 라벨이 충분히 모인 뒤
selection.py 의 관문을 통과해야 정한다. 그 전까지 운영 모델은 LightGBM 이다.

하이퍼파라미터는 두 후보 모두 튜닝하지 않은 기본 수준이다. 한쪽만 튜닝하면
비교가 불공정해지므로, 비교할 때는 양쪽을 같은 방식으로 튜닝해야 한다.
"""

from __future__ import annotations

import importlib
from typing import Any, Iterable, Mapping

from .allowlist import TARGET_NAME
from .features import build_feature_frame

FAMILIES: tuple[str, ...] = ("lightgbm", "catboost")
DEFAULT_FAMILY = "lightgbm"

# artifacts.metadata["model_family"] 에 기록되는 이름.
FAMILY_LABELS: dict[str, str] = {
    "lightgbm": "lightgbm_classifier",
    "catboost": "catboost_classifier",
}

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

DEFAULT_CATBOOST_PARAMS: dict[str, Any] = {
    "loss_function": "MultiClass",
    "iterations": 250,
    "learning_rate": 0.06,
    "depth": 6,
    "l2_leaf_reg": 3.0,
    "random_seed": 42,
    "verbose": 0,
    "allow_writing_files": False,  # 학습 폴더(catboost_info)를 만들지 않는다
    "thread_count": 1,  # 같은 시드면 같은 결과가 되도록 고정
}


def _check_family(family: str) -> None:
    if family not in FAMILIES:
        raise ValueError(f"unknown model family {family!r}; choose from {list(FAMILIES)}")


def build_classifier(family: str, *, seed: int | None = None, params: Mapping[str, Any] | None = None) -> Any:
    """학습 전 분류기. seed 를 주면 두 후보 모두 그 시드로 고정한다."""
    _check_family(family)
    if family == "lightgbm":
        try:
            lgb = importlib.import_module("lightgbm")
        except ModuleNotFoundError as exc:
            raise RuntimeError("lightgbm is required for finance model training") from exc
        merged = {**DEFAULT_LGBM_PARAMS, **(params or {})}
        if seed is not None:
            merged["random_state"] = seed
        return lgb.LGBMClassifier(**merged)

    try:
        cb = importlib.import_module("catboost")
    except ModuleNotFoundError as exc:
        raise RuntimeError("catboost is required for finance model training") from exc
    merged = {**DEFAULT_CATBOOST_PARAMS, **(params or {})}
    if seed is not None:
        merged["random_seed"] = seed
    return cb.CatBoostClassifier(**merged)


def fit_classifier(family: str, frame: Any, labels: list[str], *, seed: int | None = None, params: Mapping[str, Any] | None = None) -> Any:
    model = build_classifier(family, seed=seed, params=params)
    model.fit(frame, labels)
    return model


def predict_labels(model: Any, frame: Any) -> list[str]:
    """두 후보의 predict 반환 모양이 달라서(CatBoost 는 2차원) 한 곳에서 맞춘다."""
    import numpy as np

    return [str(label) for label in np.ravel(model.predict(frame))]


def class_probability(model: Any, frame: Any, label: str) -> list[float]:
    classes = [str(c) for c in model.classes_]
    index = classes.index(label)
    return [float(row[index]) for row in model.predict_proba(frame)]


def train_finance_model(
    rows: Iterable[Mapping[str, Any]],
    *,
    family: str = DEFAULT_FAMILY,
    target_name: str = TARGET_NAME,
    params: Mapping[str, Any] | None = None,
    seed: int | None = None,
) -> Any:
    """원본 7개 열 + 라벨을 가진 행으로 학습한다. 파생 열은 여기서 계산한다."""
    row_list = list(rows)
    if not row_list:
        raise ValueError("training rows must not be empty")

    labels: list[str] = []
    for row in row_list:
        label = row.get(target_name)
        if not isinstance(label, str) or label.strip() == "":
            raise ValueError(f"row missing target label: {target_name}")
        labels.append(label.strip())

    frame = build_feature_frame(row_list)
    return fit_classifier(family, frame, labels, seed=seed, params=params)
