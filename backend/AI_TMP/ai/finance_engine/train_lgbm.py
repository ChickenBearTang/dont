from __future__ import annotations

from typing import Any

from .allowlist import TARGET_NAME
from .models import DEFAULT_LGBM_PARAMS, train_finance_model

__all__ = ["DEFAULT_LGBM_PARAMS", "train_finance_model_lgbm"]


def train_finance_model_lgbm(
    rows: list[dict[str, Any]],
    *,
    target_name: str = TARGET_NAME,
    params: dict[str, Any] | None = None,
) -> Any:
    """기존 호출부 호환용. 새 코드는 models.train_finance_model(family=...) 를 쓴다."""
    return train_finance_model(rows, family="lightgbm", target_name=target_name, params=params)
