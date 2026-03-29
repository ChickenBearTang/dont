from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import pickle
from pathlib import Path
from typing import Any


MODEL_FILENAME = "model.pkl"
METADATA_FILENAME = "metadata.json"


@dataclass(frozen=True)
class PriceModelArtifact:
    model: Any
    metadata: dict[str, Any]


def save_price_model_artifact(
    *,
    model: Any,
    output_dir: str | Path,
    schema_version: str,
    feature_names: list[str],
    target_name: str,
    model_family: str = "lightgbm",
    extra_metadata: dict[str, Any] | None = None,
) -> PriceModelArtifact:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {
        "schema_version": schema_version,
        "model_family": model_family,
        "target_name": target_name,
        "feature_names": list(feature_names),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(extra_metadata, dict):
        for key, value in extra_metadata.items():
            metadata[str(key)] = value

    model_path = output_path / MODEL_FILENAME
    metadata_path = output_path / METADATA_FILENAME
    with model_path.open("wb") as handle:
        pickle.dump(model, handle)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return PriceModelArtifact(model=model, metadata=metadata)


def load_price_model_artifact(
    artifact_dir: str | Path,
) -> PriceModelArtifact:
    artifact_path = Path(artifact_dir)
    model_path = artifact_path / MODEL_FILENAME
    metadata_path = artifact_path / METADATA_FILENAME
    if not model_path.exists():
        raise FileNotFoundError(f"model artifact not found: {model_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata artifact not found: {metadata_path}")

    with model_path.open("rb") as handle:
        model = pickle.load(handle)
    metadata_raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata_raw, dict):
        raise ValueError("metadata.json must be a JSON object")

    required_fields = {"schema_version", "model_family", "target_name", "feature_names"}
    missing = sorted(field for field in required_fields if field not in metadata_raw)
    if missing:
        raise ValueError(f"metadata.json missing required fields: {missing}")

    feature_names = metadata_raw.get("feature_names")
    if not isinstance(feature_names, list) or not all(
        isinstance(item, str) for item in feature_names
    ):
        raise ValueError("metadata.feature_names must be a list[str]")

    return PriceModelArtifact(model=model, metadata=metadata_raw)
