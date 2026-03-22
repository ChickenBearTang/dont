from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class XAIContracts:
    SCHEMA_VERSION = "1.0"

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


@dataclass(frozen=True)
class ItemExplanation:
    item_id: str
    reasons: list[dict[str, Any]] = field(default_factory=list)
    errors: list[AnalysisError] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.reasons is None:
            object.__setattr__(self, "reasons", [])
        if self.errors is None:
            object.__setattr__(self, "errors", [])

    def to_dict(self, *, model_version: str, generated_at: str) -> dict[str, Any]:
        normalized_reasons = XAIContracts.normalize_reasons(self.reasons)
        normalized_errors = XAIContracts.normalize_errors(self.errors)
        return {
            "item_id": XAIContracts.require_string(self.item_id, field_name="item_id"),
            "reasons": normalized_reasons,
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
            "analyzer_id": self.analyzer_id,
            "generated_at": generated_at,
            "model_version": self.model_version,
            "crawl": self.crawl.to_dict(
                model_version=self.model_version,
                generated_at=generated_at,
            ),
            "errors": [error.to_dict() for error in normalized_errors],
        }
