from __future__ import annotations

from dataclasses import dataclass

from .allowlist import (
    FEATURE_ALLOWLIST_PHASE1,
    SCHEMA_VERSION,
    training_feature_names,
)


@dataclass(frozen=True)
class FeatureRegistry:
    schema_version: str
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]

    @property
    def all_features(self) -> tuple[str, ...]:
        return self.numeric_features + self.categorical_features


PRICE_FEATURE_REGISTRY_V1 = FeatureRegistry(
    schema_version=SCHEMA_VERSION,
    numeric_features=FEATURE_ALLOWLIST_PHASE1["numeric"],
    categorical_features=FEATURE_ALLOWLIST_PHASE1["categorical"],
)


def phase1_feature_names() -> tuple[str, ...]:
    return training_feature_names()
