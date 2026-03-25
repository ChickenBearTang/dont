from .allowlist import (
    FEATURE_ALLOWLIST_PHASE1,
    FORBIDDEN_TRAIN_FIELDS,
    PHASE2_RESERVED_FIELDS,
)
from importlib import import_module
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
    "validate_inference_payload",
    "validate_schema_version",
]
