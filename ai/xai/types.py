from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class XAIContracts:
    SCHEMA_VERSION = "financial-purchase-copilot-xai-v1"
    SPEC_VERSION = "1.0"
    MAX_CONSUMER_REASONS = 4
    DEFAULT_REASON_TARGET = 3
    ALLOWED_DECISIONS = {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"}

    @staticmethod
    def require_datetime(value: Any, *, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(f"{field_name} must be a datetime")
        return value

    @staticmethod
    def require_string(value: Any, *, field_name: str) -> str:
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @classmethod
    def serialize_datetime(cls, value: Any, *, field_name: str) -> str:
        return cls.require_datetime(value, field_name=field_name).isoformat()

    @staticmethod
    def normalize_errors(errors: list[AnalysisError] | None) -> list[AnalysisError]:
        if errors is None:
            return []
        if not isinstance(errors, list):
            raise TypeError("errors must be a list")
        return errors

    @staticmethod
    def normalize_reasons(reasons: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if reasons is None:
            return []
        if not isinstance(reasons, list):
            raise TypeError("reasons must be a list")
        return reasons

    @staticmethod
    def normalize_counterfactuals(
        counterfactuals: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        if counterfactuals is None:
            return []
        if not isinstance(counterfactuals, list):
            raise TypeError("counterfactuals must be a list")
        return counterfactuals


@dataclass(frozen=True)
class ItemExplanation:
    item_id: str
    reasons: list[dict[str, Any]] = field(default_factory=list)
    decision: str = "REVIEW"
    decision_confidence: float = 0.0
    reason_codes: list[str] = field(default_factory=list)
    reason_texts: list[str] = field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    counterfactual_conditions: list[dict[str, Any]] = field(default_factory=list)
    user_options: list[str] = field(default_factory=list)
    rule_version: str = "rules-v1"
    data_snapshot_id: str = ""
    counterfactuals: list[dict[str, Any]] = field(default_factory=list)
    polished_summary: str = ""
    errors: list[AnalysisError] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.reasons is None:
            object.__setattr__(self, "reasons", [])
        if self.counterfactuals is None:
            object.__setattr__(self, "counterfactuals", [])
        if self.reason_codes is None:
            object.__setattr__(self, "reason_codes", [])
        if self.reason_texts is None:
            object.__setattr__(self, "reason_texts", [])
        if self.supporting_evidence is None:
            object.__setattr__(self, "supporting_evidence", [])
        if self.counterfactual_conditions is None:
            object.__setattr__(self, "counterfactual_conditions", [])
        if self.user_options is None:
            object.__setattr__(self, "user_options", [])
        if self.errors is None:
            object.__setattr__(self, "errors", [])

    def to_dict(self, *, model_version: str, generated_at: str) -> dict[str, Any]:
        normalized_reasons = XAIContracts.normalize_reasons(self.reasons)[
            : XAIContracts.MAX_CONSUMER_REASONS
        ]
        normalized_counterfactuals = XAIContracts.normalize_counterfactuals(
            self.counterfactuals
        )
        normalized_errors = XAIContracts.normalize_errors(self.errors)
        if self.decision not in XAIContracts.ALLOWED_DECISIONS:
            raise ValueError(f"invalid decision label: {self.decision}")

        reason_codes = self.reason_codes or [
            str(reason.get("reason_code", "")) for reason in normalized_reasons
        ]
        reason_texts = self.reason_texts or [
            str(reason.get("reason_text", "")) for reason in normalized_reasons
        ]
        reason_codes = [code for code in reason_codes if code][
            : XAIContracts.MAX_CONSUMER_REASONS
        ]
        reason_texts = [text for text in reason_texts if text][
            : XAIContracts.MAX_CONSUMER_REASONS
        ]

        counterfactual_conditions = (
            self.counterfactual_conditions or normalized_counterfactuals
        )

        return {
            "item_id": XAIContracts.require_string(self.item_id, field_name="item_id"),
            "decision": self.decision,
            "decision_confidence": float(self.decision_confidence),
            "reason_codes": reason_codes,
            "reason_texts": reason_texts,
            "supporting_evidence": self.supporting_evidence,
            "counterfactual_conditions": counterfactual_conditions,
            "user_options": self.user_options,
            "rule_version": self.rule_version,
            "data_snapshot_id": self.data_snapshot_id,
            "reasons": normalized_reasons,
            "counterfactuals": normalized_counterfactuals,
            "polished_summary": self.polished_summary,
            "errors": [error.to_dict() for error in normalized_errors],
            "model_version": model_version,
            "generated_at": generated_at,
        }


@dataclass(frozen=True)
class CrawlExplanation:
    source: str
    items: list[ItemExplanation]

    def to_dict(self, *, model_version: str, generated_at: str) -> dict[str, Any]:
        return {
            "source": self.source,
            "items": [
                item.to_dict(
                    model_version=model_version,
                    generated_at=generated_at,
                )
                for item in self.items
            ],
        }


@dataclass(frozen=True)
class AnalysisError:
    code: str
    message: str
    item_id: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "item_id": self.item_id,
        }


@dataclass(frozen=True)
class ExplainabilityResult:
    analyzer_id: str
    generated_at: datetime
    model_version: str
    crawl: CrawlExplanation
    errors: list[AnalysisError] = field(default_factory=list)
    schema_version: str = XAIContracts.SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.errors is None:
            object.__setattr__(self, "errors", [])
        XAIContracts.require_datetime(self.generated_at, field_name="generated_at")

    def to_dict(self) -> dict[str, Any]:
        normalized_errors = XAIContracts.normalize_errors(self.errors)
        generated_at = XAIContracts.serialize_datetime(
            self.generated_at,
            field_name="generated_at",
        )
        return {
            "schema_version": self.schema_version,
            "spec_version": XAIContracts.SPEC_VERSION,
            "analyzer_id": self.analyzer_id,
            "generated_at": generated_at,
            "model_version": self.model_version,
            "crawl": self.crawl.to_dict(
                model_version=self.model_version,
                generated_at=generated_at,
            ),
            "errors": [error.to_dict() for error in normalized_errors],
        }
