from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from .allowlist import (
    CLASS_LABELS,
    SCHEMA_VERSION,
    TARGET_NAME,
    raw_input_names,
    training_feature_names,
)
from .artifacts import load_finance_model_artifact
from .features import build_feature_frame


# 모델 입력 중 finance_profile 에서 오는 것. product_price 는 요청의 가격에서 온다.
_PROFILE_INPUT_NAMES: tuple[str, ...] = tuple(
    name for name in raw_input_names() if name != "product_price"
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _default_artifact_path() -> str | None:
    candidate = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "artifacts"
        / "finance_retrain_model"
    )
    if (candidate / "model.pkl").exists() and (candidate / "metadata.json").exists():
        return str(candidate)
    return None


def _resolve_model_path(explicit_model_path: str | None) -> str | None:
    if explicit_model_path is not None and explicit_model_path.strip() != "":
        return explicit_model_path.strip()
    env_value = os.getenv("AI_FINANCE_MODEL_PATH")
    if env_value is not None and env_value.strip() != "":
        return env_value.strip()
    return _default_artifact_path()


def build_finance_inference_payload(
    *,
    current_price: int | None,
    finance_profile: dict[str, float | int],
) -> dict[str, float]:
    """모델 입력(원본 7개)을 만든다. 파생 비율은 여기서 만들지 않는다(features.py).

    finance_profile 은 입력 계약(xai.input_contract)을 통과해 모든 키가 채워진
    값이어야 한다. 예전에는 여기서 `.get(키, 0.0)` 과 소득 1_000_000 같은 기본값이
    조용히 들어갔다. 이제 키가 없으면 어떤 키인지 밝히며 즉시 실패한다.
    """
    missing = [
        name for name in _PROFILE_INPUT_NAMES if name not in finance_profile
    ]
    if missing:
        raise ValueError(
            f"finance_profile is missing keys required by the model: {missing}"
        )

    product_price = (
        float(current_price)
        if isinstance(current_price, int) and current_price > 0
        else 0.0
    )
    payload = {
        name: max(_as_float(finance_profile[name], 0.0), 0.0)
        for name in _PROFILE_INPUT_NAMES
    }
    payload["product_price"] = max(product_price, 0.0)
    return payload


@lru_cache(maxsize=4)
def _load_cached_artifact(resolved_artifact_dir: str) -> Any:
    return load_finance_model_artifact(resolved_artifact_dir)


def predict_finance_signal(
    *,
    current_price: int | None,
    finance_profile: dict[str, float | int],
    explicit_model_path: str | None = None,
    enabled: bool | None = None,
) -> tuple[dict[str, float | str], dict[str, Any]]:
    model_enabled = _env_flag("AI_FINANCE_MODEL_ENABLED", default=True)
    if enabled is not None:
        model_enabled = bool(enabled)
    if not model_enabled:
        return {}, {
            "enabled": False,
            "backend": "disabled",
            "reason": "finance_model_disabled",
        }

    model_path_raw = _resolve_model_path(explicit_model_path)
    if model_path_raw is None:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "model_path_missing",
        }
    model_path = str(Path(model_path_raw))

    try:
        artifact = _load_cached_artifact(model_path)
    except Exception as exc:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "model_load_failed",
            "artifact_path": model_path,
            "error_type": type(exc).__name__,
        }

    metadata = artifact.metadata
    if str(metadata.get("schema_version", "")) != SCHEMA_VERSION:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "schema_version_mismatch",
            "artifact_path": model_path,
        }

    trained_features = metadata.get("feature_names")
    expected_features = list(training_feature_names())
    if trained_features != expected_features:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "feature_schema_mismatch",
            "artifact_path": model_path,
        }
    if str(metadata.get("target_name", "")) != TARGET_NAME:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "target_schema_mismatch",
            "artifact_path": model_path,
        }

    payload = build_finance_inference_payload(
        current_price=current_price,
        finance_profile=finance_profile,
    )

    try:
        frame = build_feature_frame([payload])
    except ImportError:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "pandas_unavailable",
            "artifact_path": model_path,
        }

    model = artifact.model
    try:
        probabilities = model.predict_proba(frame)[0]
        classes = [str(name) for name in model.classes_]
    except Exception:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "model_predict_failed",
            "artifact_path": model_path,
        }

    class_probabilities: dict[str, float] = {}
    for index, class_name in enumerate(classes):
        class_probabilities[class_name] = float(probabilities[index])

    low_prob = float(class_probabilities.get("low", 0.0))
    medium_prob = float(class_probabilities.get("medium", 0.0))
    high_prob = float(class_probabilities.get("high", 0.0))

    max_label = max(
        CLASS_LABELS,
        key=lambda label: class_probabilities.get(label, 0.0),
    )
    finance_model_risk_score = max(min(high_prob - low_prob, 1.0), -1.0)
    finance_model_affordability_score = max(min(low_prob - high_prob, 1.0), -1.0)

    return {
        "finance_model_risk_bucket": max_label,
        "finance_model_low_prob": low_prob,
        "finance_model_medium_prob": medium_prob,
        "finance_model_high_prob": high_prob,
        "finance_model_risk_score": finance_model_risk_score,
        "finance_model_affordability_score": finance_model_affordability_score,
    }, {
        "enabled": True,
        "backend": str(metadata.get("model_family", "lightgbm_classifier")),
        "reason": "ok",
        "artifact_path": model_path,
        "target_name": str(metadata.get("target_name", "unknown")),
        "schema_version": SCHEMA_VERSION,
        "risk_bucket": max_label,
    }
