from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .allowlist import (
    FORBIDDEN_TRAIN_FIELDS,
    PHASE2_RESERVED_FIELDS,
    SCHEMA_VERSION,
    training_feature_names,
)
from .schema_models import PriceFeatureSnapshotRow, PriceObservation


class SchemaValidationError(ValueError):
    pass


def validate_schema_version(schema_version: str) -> None:
    if schema_version != SCHEMA_VERSION:
        raise SchemaValidationError(
            f"schema_version mismatch: expected={SCHEMA_VERSION}, got={schema_version}"
        )


def validate_price_observation(observation: PriceObservation) -> None:
    validate_schema_version(observation.schema_version)
    if observation.listed_price is not None and observation.listed_price <= 0:
        raise SchemaValidationError("listed_price must be > 0 when present")
    if observation.shipping_fee is not None and observation.shipping_fee < 0:
        raise SchemaValidationError("shipping_fee must be >= 0 when present")


def validate_training_row(row: PriceFeatureSnapshotRow) -> None:
    validate_schema_version(row.schema_version)
    payload = asdict(row)
    forbidden_hits = sorted(
        field for field in FORBIDDEN_TRAIN_FIELDS if field in payload
    )
    if forbidden_hits:
        raise SchemaValidationError(
            f"forbidden fields included in training row: {forbidden_hits}"
        )

    allowlist = set(training_feature_names())
    system_fields = {
        "canonical_product_id",
        "variant_id",
        "seller_id",
        "snapshot_date",
        "schema_version",
        "market_gap",
        "history_gap",
        "price_bucket",
    }
    for field_name in payload.keys():
        if field_name not in allowlist and field_name not in system_fields:
            raise SchemaValidationError(
                f"field not allowed for phase1 training row: {field_name}"
            )

    for reserved_name in PHASE2_RESERVED_FIELDS:
        if reserved_name in payload:
            raise SchemaValidationError(
                f"reserved field leaked into training row: {reserved_name}"
            )


def validate_training_columns(columns: list[str]) -> None:
    allowlist = set(training_feature_names())
    for field_name in columns:
        if field_name in FORBIDDEN_TRAIN_FIELDS:
            raise SchemaValidationError(f"forbidden train column: {field_name}")
        if field_name not in allowlist:
            raise SchemaValidationError(
                f"column not in explicit allowlist: {field_name}"
            )


def validate_inference_payload(payload: dict[str, Any]) -> None:
    allowlist = set(training_feature_names())
    incoming = set(payload.keys())
    unknown = sorted(name for name in incoming if name not in allowlist)
    if unknown:
        raise SchemaValidationError(
            f"inference payload includes unknown fields: {unknown}"
        )

    missing = sorted(name for name in allowlist if name not in incoming)
    if missing:
        raise SchemaValidationError(
            f"inference payload missing required features: {missing}"
        )

    for reserved_name in PHASE2_RESERVED_FIELDS:
        if reserved_name in incoming:
            raise SchemaValidationError(
                f"reserved phase2 field is not allowed at phase1 inference: {reserved_name}"
            )

    for forbidden_name in FORBIDDEN_TRAIN_FIELDS:
        if forbidden_name in incoming:
            raise SchemaValidationError(
                f"forbidden train/source field in inference payload: {forbidden_name}"
            )


def enforce_null_reserved_fields(raw_row: dict[str, Any]) -> None:
    for field_name in PHASE2_RESERVED_FIELDS:
        if field_name not in raw_row:
            continue
        value = raw_row[field_name]
        if value == 0:
            raise SchemaValidationError(
                f"reserved field must keep unknown as null, got zero: {field_name}"
            )
