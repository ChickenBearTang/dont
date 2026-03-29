from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from .allowlist import CLASS_LABELS, SCHEMA_VERSION, TARGET_NAME, training_feature_names
from .artifacts import load_finance_model_artifact


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


def _safe_divide(numerator: float, denominator: float, default: float) -> float:
    if denominator == 0:
        return float(default)
    return float(numerator / denominator)


def _window_bucket(
    window_stats: dict[str, dict[str, float | int | None]] | None,
    key: str,
) -> dict[str, float | int | None]:
    if not isinstance(window_stats, dict):
        return {}
    bucket = window_stats.get(key)
    if not isinstance(bucket, dict):
        return {}
    return bucket


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


def _monthly_spending_estimate(
    window_stats: dict[str, dict[str, float | int | None]] | None,
    *,
    available_fixed_expense: float,
    expected_card_payment_amount: float,
) -> float:
    bucket_30d = _window_bucket(window_stats, "30d")
    avg_price = _as_float(bucket_30d.get("avg_price"), 0.0)
    count = _as_float(bucket_30d.get("count"), 0.0)
    if avg_price > 0 and count > 0:
        return max(avg_price * min(count, 30.0), 1.0)
    fallback = max(
        available_fixed_expense * 2.0,
        expected_card_payment_amount * 2.0,
        800_000.0,
    )
    return max(fallback, 1.0)


def build_finance_inference_payload(
    *,
    current_price: int | None,
    finance_profile: dict[str, float | int],
    window_stats: dict[str, dict[str, float | int | None]] | None,
) -> dict[str, float]:
    current_balance = _as_float(finance_profile.get("current_balance"), 0.0)
    emergency_fund_balance = _as_float(finance_profile.get("emergency_fund_balance"), 0.0)
    expected_card_payment_amount = _as_float(
        finance_profile.get("expected_card_payment_amount"), 0.0
    )
    days_until_card_due = max(
        _as_float(finance_profile.get("days_until_card_due"), 0.0),
        0.0,
    )
    savebox_balance = _as_float(
        finance_profile.get("savebox_balance"),
        emergency_fund_balance,
    )
    available_fixed_expense = _as_float(
        finance_profile.get("available_fixed_expense"),
        0.0,
    )
    available_fixed_income = _as_float(
        finance_profile.get("available_fixed_income"), 1_000_000.0
    )
    product_price = (
        float(current_price)
        if isinstance(current_price, int) and current_price > 0
        else 0.0
    )
    monthly_spending = _monthly_spending_estimate(
        window_stats,
        available_fixed_expense=available_fixed_expense,
        expected_card_payment_amount=expected_card_payment_amount,
    )

    return {
        "current_balance": max(current_balance, 0.0),
        "emergency_fund_balance": max(emergency_fund_balance, 0.0),
        "expected_card_payment_amount": max(expected_card_payment_amount, 0.0),
        "days_until_card_due": max(days_until_card_due, 0.0),
        "savebox_balance": max(savebox_balance, 0.0),
        "available_fixed_expense": max(available_fixed_expense, 0.0),
        "available_fixed_income": max(available_fixed_income, 0.0),
        "monthly_spending_30d_estimate": monthly_spending,
        "product_price": max(product_price, 0.0),
        "product_price_vs_monthly_spending": _safe_divide(
            product_price, monthly_spending, 0.0
        ),
        "projected_balance_after_purchase": savebox_balance - product_price,
        "product_price_vs_emergency_fund": _safe_divide(
            product_price, max(emergency_fund_balance, 1.0), 0.0
        ),
    }


@lru_cache(maxsize=4)
def _load_cached_artifact(resolved_artifact_dir: str) -> Any:
    return load_finance_model_artifact(resolved_artifact_dir)


def predict_finance_signal(
    *,
    current_price: int | None,
    finance_profile: dict[str, float | int],
    window_stats: dict[str, dict[str, float | int | None]] | None,
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
        window_stats=window_stats,
    )

    try:
        import pandas as pd
    except Exception:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "pandas_unavailable",
            "artifact_path": model_path,
        }

    feature_order = list(training_feature_names())
    frame = pd.DataFrame([payload], columns=feature_order)
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
