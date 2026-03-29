from .allowlist import (
    FEATURE_ALLOWLIST_PHASE1,
    FORBIDDEN_TRAIN_FIELDS,
    PHASE2_RESERVED_FIELDS,
)
from .artifacts import load_price_model_artifact, save_price_model_artifact
from importlib import import_module
from .inference import predict_price_signal
from .schema_models import (
    PriceObservation,
    RawListing,
    RawMerchantOffer,
    RawPostDetail,
)
from .schema_validator import (
    SchemaValidationError,
    validate_inference_payload,
    validate_schema_version,
)

try:
    from .inference import build_price_inference_payload
except ImportError:  # pragma: no cover - backward compatibility for mixed deployments

    def build_price_inference_payload(*args, **kwargs):
        raise ImportError(
            "build_price_inference_payload is unavailable in ai.price_engine.inference"
        )


try:
    _dataset_builder = import_module("ai.price_engine.dataset_builder")
    build_price_feature_snapshot_v1 = _dataset_builder.build_price_feature_snapshot_v1
except ModuleNotFoundError:  # pragma: no cover - available after later wave ports

    def build_price_feature_snapshot_v1(*args, **kwargs):
        raise ModuleNotFoundError("ai.price_engine.dataset_builder")


try:
    _normalizer = import_module("ai.price_engine.normalizer")
    merge_to_price_observation = _normalizer.merge_to_price_observation
except ModuleNotFoundError:  # pragma: no cover - available after later wave ports

    def merge_to_price_observation(*args, **kwargs):
        raise ModuleNotFoundError("ai.price_engine.normalizer")


__all__ = [
    "FEATURE_ALLOWLIST_PHASE1",
    "FORBIDDEN_TRAIN_FIELDS",
    "PHASE2_RESERVED_FIELDS",
    "PriceObservation",
    "RawListing",
    "RawMerchantOffer",
    "RawPostDetail",
    "SchemaValidationError",
    "build_price_feature_snapshot_v1",
    "merge_to_price_observation",
    "load_price_model_artifact",
    "save_price_model_artifact",
    "build_price_inference_payload",
    "predict_price_signal",
    "validate_inference_payload",
    "validate_schema_version",
]
