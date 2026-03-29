from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PurchaseCoreInput:
    price_bucket: str
    expected_drop_prob: float
    finance_risk_bucket: str
    affordability_score: float
    feature_scores: Mapping[str, Any] = field(default_factory=dict)
    top_k_reasons: int = 3


@dataclass(frozen=True)
class ReasonItem:
    reason_code: str
    reason_text: str
    feature: str
    score: float
    source_type: str


@dataclass(frozen=True)
class PurchaseCoreResult:
    decision: str
    raw_decision: str
    reasons: list[ReasonItem]
