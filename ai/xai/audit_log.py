from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class XAIAuditLogEntry:
    item_id: str
    raw_source_refs: list[dict[str, Any]]
    normalization_steps: list[str]
    feature_snapshot_id: str
    data_snapshot_id: str
    model_input_vector_hash: str
    fired_rule_ids: list[str]
    feature_contributions: list[dict[str, Any]]
    final_decision: str
    rendered_explanation: str
    model_version: str
    rule_version: str
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "raw_source_refs": self.raw_source_refs,
            "normalization_steps": self.normalization_steps,
            "feature_snapshot_id": self.feature_snapshot_id,
            "data_snapshot_id": self.data_snapshot_id,
            "model_input_vector_hash": self.model_input_vector_hash,
            "fired_rule_ids": self.fired_rule_ids,
            "feature_contributions": self.feature_contributions,
            "final_decision": self.final_decision,
            "rendered_explanation": self.rendered_explanation,
            "model_version": self.model_version,
            "rule_version": self.rule_version,
            "schema_version": self.schema_version,
        }


def build_model_input_vector_hash(feature_scores: dict[str, float]) -> str:
    joined = "|".join(
        f"{name}:{feature_scores[name]:.6f}" for name in sorted(feature_scores.keys())
    )
    return sha256(joined.encode("utf-8")).hexdigest()
