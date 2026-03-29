from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from .allowlist import FEATURE_ALLOWLIST_PHASE1, SCHEMA_VERSION, training_feature_names
from .artifacts import load_price_model_artifact
from .schema_validator import validate_inference_payload, validate_schema_version


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


def _normalize_categorical(value: str | None, *, fallback: str) -> str:
    if value is None:
        return fallback
    normalized = value.strip()
    if normalized == "":
        return fallback
    return normalized


def build_price_inference_payload(
    *,
    current_price: int | None,
    window_stats: dict[str, dict[str, float | int | None]] | None,
    category: str | None,
    brand: str | None = None,
    seller_type: str | None = None,
    availability_status: str | None = None,
) -> dict[str, Any]:
    price = float(current_price) if isinstance(current_price, int) and current_price > 0 else 0.0

    bucket_30d = _window_bucket(window_stats, "30d")
    bucket_7d = _window_bucket(window_stats, "7d")
    avg_30d = _as_float(bucket_30d.get("avg_price"), price if price > 0 else 1.0)
    min_30d = _as_float(bucket_30d.get("min_price"), price if price > 0 else avg_30d)
    max_30d = _as_float(bucket_30d.get("max_price"), price if price > 0 else avg_30d)
    avg_7d = _as_float(bucket_7d.get("avg_price"), avg_30d if avg_30d > 0 else price)
    count_30d = _as_float(bucket_30d.get("count"), 1.0)

    if avg_7d <= 0:
        avg_7d = avg_30d if avg_30d > 0 else max(price, 1.0)
    if avg_30d <= 0:
        avg_30d = avg_7d if avg_7d > 0 else max(price, 1.0)
    if min_30d <= 0:
        min_30d = min(avg_30d, price) if price > 0 else avg_30d
    if max_30d <= 0:
        max_30d = max(avg_30d, price) if price > 0 else avg_30d
    if max_30d < min_30d:
        max_30d, min_30d = min_30d, max_30d

    volatility_30d = _as_float(
        bucket_30d.get("price_volatility"),
        max(max_30d - min_30d, 0.0) / 6.0,
    )
    shipping_fee_mode_30d = _as_float(bucket_30d.get("shipping_fee_mode"), 0.0)
    seller_count_same_product = max(count_30d, 1.0)
    release_age_days = max(_as_float(bucket_30d.get("release_age_days"), 30.0), 0.0)

    payload = {
        "current_effective_price": max(price, 0.0),
        "avg_price_7d": avg_7d,
        "avg_price_30d": avg_30d,
        "min_price_30d": min_30d,
        "max_price_30d": max_30d,
        "price_volatility_30d": max(volatility_30d, 0.0),
        "seller_count_same_product": seller_count_same_product,
        "release_age_days": release_age_days,
        "shipping_fee_mode_30d": max(shipping_fee_mode_30d, 0.0),
        "price_vs_avg_7d": _safe_divide(price, avg_7d, 1.0),
        "price_vs_avg_30d": _safe_divide(price, avg_30d, 1.0),
        "price_to_min_30d_gap": max(price - min_30d, 0.0),
        "price_to_max_30d_gap": max(max_30d - price, 0.0),
        "brand": _normalize_categorical(brand, fallback="unknown"),
        "category": _normalize_categorical(category, fallback="unknown"),
        "seller_type": _normalize_categorical(seller_type, fallback="unknown"),
        "availability_status": _normalize_categorical(
            availability_status, fallback="in_stock"
        ),
    }
    validate_inference_payload(payload)
    return payload


@lru_cache(maxsize=4)
def _load_cached_artifact(resolved_artifact_dir: str) -> Any:
    return load_price_model_artifact(resolved_artifact_dir)


def _resolve_model_path(explicit_model_path: str | None) -> str | None:
    if explicit_model_path is not None and explicit_model_path.strip() != "":
        return explicit_model_path.strip()
    env_value = os.getenv("AI_PRICE_MODEL_PATH")
    if env_value is None or env_value.strip() == "":
        return None
    return env_value.strip()


def predict_price_signal(
    *,
    current_price: int | None,
    window_stats: dict[str, dict[str, float | int | None]] | None,
    category: str | None,
    brand: str | None = None,
    seller_type: str | None = None,
    availability_status: str | None = None,
    explicit_model_path: str | None = None,
    enabled: bool | None = None,
) -> tuple[dict[str, float], dict[str, Any]]:
    model_enabled = _env_flag("AI_PRICE_MODEL_ENABLED", default=False)
    if enabled is not None:
        model_enabled = bool(enabled)
    if not model_enabled:
        return {}, {
            "enabled": False,
            "backend": "disabled",
            "reason": "price_model_disabled",
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
    try:
        validate_schema_version(str(metadata.get("schema_version", "")))
    except Exception:
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

    try:
        payload = build_price_inference_payload(
            current_price=current_price,
            window_stats=window_stats,
            category=category,
            brand=brand,
            seller_type=seller_type,
            availability_status=availability_status,
        )
    except Exception:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "inference_payload_invalid",
            "artifact_path": model_path,
        }

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
    for category_name in FEATURE_ALLOWLIST_PHASE1["categorical"]:
        frame[category_name] = frame[category_name].astype("category")

    try:
        predicted_price = float(artifact.model.predict(frame)[0])
    except Exception:
        return {}, {
            "enabled": False,
            "backend": "fallback",
            "reason": "model_predict_failed",
            "artifact_path": model_path,
        }

    current_value = float(payload["current_effective_price"])
    denominator = max(abs(predicted_price), 1.0)
    gap_ratio = (predicted_price - current_value) / denominator
    price_model_gap_score = max(min(gap_ratio * 2.0, 1.0), -1.0)

    return {
        "price_model_predicted_price": predicted_price,
        "price_model_gap_ratio": gap_ratio,
        "price_model_gap_score": price_model_gap_score,
    }, {
        "enabled": True,
        "backend": str(metadata.get("model_family", "lightgbm")),
        "reason": "ok",
        "artifact_path": model_path,
        "target_name": str(metadata.get("target_name", "unknown")),
        "schema_version": SCHEMA_VERSION,
        "predicted_price": predicted_price,
    }
