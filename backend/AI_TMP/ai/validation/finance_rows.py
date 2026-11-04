"""재무 모델 학습 행 검증 (원본 입력 7개 + 라벨)."""

from __future__ import annotations

import math
from typing import Any, Iterable

from ai.finance_engine.allowlist import CLASS_LABELS, RAW_INPUT_NAMES, TARGET_NAME

from .core import Severity, ValidationReport

MIN_CLASS_SHARE = 0.01
MAX_AMOUNT = 10_000_000_000.0


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def validate_finance_rows(rows: Iterable[Any], *, check_rule: bool) -> ValidationReport:
    """check_rule=True 는 라벨이 규칙(synthetic.rule_bucket)이 붙인 합성 데이터일 때만 쓴다.
    실제 결과 라벨에는 규칙과의 일치를 요구하지 않는다."""
    from ai.finance_engine.synthetic import rule_bucket

    rows = list(rows)
    report = ValidationReport("finance_rows", rows_checked=len(rows))
    err, warn = Severity.ERROR, Severity.WARNING
    label_counts = {label: 0 for label in CLASS_LABELS}
    labeled = 0

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            report.add("ROW_NOT_OBJECT", err, "행이 객체가 아니다", row_index=i)
            continue
        usable = True
        for name in RAW_INPUT_NAMES:
            value = _finite(row.get(name))
            if value is None:
                report.add("INVALID_VALUE", err, f"{name} 이 없거나 숫자가 아니다/유한하지 않다", row_index=i, field_name=name)
                usable = False
            elif value < 0:
                report.add("NEGATIVE_VALUE", err, f"{name} 이 음수다", row_index=i, field_name=name)
                usable = False
            elif value > MAX_AMOUNT:
                report.add("VALUE_OUT_OF_RANGE", err, f"{name} 이 상한을 넘는다", row_index=i, field_name=name)
                usable = False
        days = _finite(row.get("days_until_card_due"))
        if days is not None and not (0 <= days <= 31):
            report.add("DAYS_OUT_OF_RANGE", err, "카드 결제일까지 남은 일수가 0~31 밖이다", row_index=i, field_name="days_until_card_due")

        label = row.get(TARGET_NAME)
        if label not in CLASS_LABELS:
            report.add("UNKNOWN_LABEL", err, f"알 수 없는 라벨: {label!r}", row_index=i, field_name=TARGET_NAME)
            continue
        label_counts[label] += 1
        labeled += 1
        if check_rule and usable and rule_bucket(row) != label:
            report.add("LABEL_RULE_MISMATCH", err, "라벨이 규칙 결과와 다르다", row_index=i, field_name=TARGET_NAME)

    if labeled >= 100:
        for label, count in label_counts.items():
            if count / labeled < MIN_CLASS_SHARE:
                report.add("CLASS_IMBALANCE", warn, f"{label} 클래스가 {count / labeled:.2%}뿐이다 (최소 {MIN_CLASS_SHARE:.0%})")
    return report
