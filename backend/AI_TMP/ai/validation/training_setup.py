"""학습 설정 검증: 정답이 입력에 새어 들어가는 문제."""

from __future__ import annotations

from typing import Iterable, Sequence

from .core import Severity, ValidationReport


def validate_training_setup(
    *,
    feature_names: Sequence[str],
    target_name: str,
    derived_from_target: Iterable[str] = (),
) -> ValidationReport:
    """정답(target)이 입력 피처에 들어 있거나, 정답에서 계산되는 피처가 있는지 본다.

    가격 모델은 정답이 current_effective_price 인데 같은 열이 입력 피처에도 들어 있었다.
    이 상태로 학습하면 모델이 정답을 그대로 베끼거나(이력이 있을 때) 아무것도 못 배운다
    (이력이 비었을 때). 어느 쪽이든 점수가 좋든 나쁘든 의미가 없다.
    """
    report = ValidationReport("training_setup", rows_checked=len(feature_names))
    features = list(feature_names)
    if target_name in features:
        report.add(
            "TARGET_IN_FEATURES",
            Severity.ERROR,
            f"정답({target_name})이 입력 피처에도 들어 있다 (타깃 누수)",
            field_name=target_name,
        )
    leaky = sorted(set(derived_from_target) & set(features))
    if leaky:
        report.add(
            "TARGET_DERIVED_FEATURES",
            Severity.WARNING,
            f"정답에서 계산되는 피처가 입력에 있다: {', '.join(leaky)}",
        )
    return report
