"""검증 결과의 공통 모양."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR = "error"  # 이 데이터/설정으로 학습·판단하면 안 된다
    WARNING = "warning"  # 쓸 수는 있으나 신뢰에 영향
    INFO = "info"


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Severity
    message: str
    row_index: int | None = None
    field: str | None = None


@dataclass
class ValidationReport:
    name: str
    rows_checked: int = 0
    issues: list[Issue] = field(default_factory=list)

    def add(
        self,
        code: str,
        severity: Severity,
        message: str,
        *,
        row_index: int | None = None,
        field_name: str | None = None,
    ) -> None:
        self.issues.append(Issue(code, severity, message, row_index, field_name))

    @property
    def ok(self) -> bool:
        """오류가 하나도 없는가 (경고는 허용)."""
        return not any(i.severity == Severity.ERROR for i in self.issues)

    def count(self, severity: Severity) -> int:
        return sum(1 for i in self.issues if i.severity == severity)

    def counts_by_code(self) -> dict[str, int]:
        return dict(Counter(i.code for i in self.issues))

    def summary(self) -> str:
        codes = ", ".join(f"{c}x{n}" for c, n in sorted(self.counts_by_code().items())) or "이상 없음"
        return (
            f"[{self.name}] 행 {self.rows_checked:,}개, 오류 {self.count(Severity.ERROR)}, "
            f"경고 {self.count(Severity.WARNING)} — {codes}"
        )

    def to_dict(self, *, samples_per_code: int = 3) -> dict[str, Any]:
        """UI/API 용. 코드마다 대표 사례 몇 개만 싣는다 (행이 수만 개여도 응답이 작다)."""
        by_code: dict[str, dict[str, Any]] = {}
        for issue in self.issues:
            entry = by_code.setdefault(
                issue.code,
                {"code": issue.code, "severity": issue.severity.value, "count": 0, "message": issue.message, "samples": []},
            )
            entry["count"] += 1
            if len(entry["samples"]) < samples_per_code:
                entry["samples"].append({"row_index": issue.row_index, "field": issue.field})
        return {
            "name": self.name,
            "ok": self.ok,
            "rows_checked": self.rows_checked,
            "errors": self.count(Severity.ERROR),
            "warnings": self.count(Severity.WARNING),
            "counts_by_code": self.counts_by_code(),
            "issues": sorted(by_code.values(), key=lambda e: (e["severity"] != "error", -e["count"])),
        }
