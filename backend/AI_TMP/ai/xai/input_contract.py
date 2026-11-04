"""XAI 입력 계약.

앞단(Spring)이 보내는 재무 프로필을 판단 엔진이 쓸 수 있는 값으로 확정한다.
이 모듈이 존재하는 이유는 하나다.

    앞단이 값을 못 채움 -> 뒷단이 조용히 기본값으로 메움 -> 판단/SHAP/DiCE 오염

이 흐름을 끊기 위해 세 가지를 보장한다.

1. strict(운영) 모드에서 필수 필드가 없거나 숫자가 아니면 즉시
   InputContractViolation 으로 실패한다.
2. 값이 어디서 왔는지(origin)를 필드마다 기록한다. 기본값으로 채운 필드는
   반드시 Origin.DEFAULT 로 남는다.
3. 기본값 표는 FINANCE_PROFILE_FIELDS 한 곳에만 존재한다. 이전에는
   analyzer.py 안에 같은 숫자가 세 군데 복붙돼 있었다.

이 모듈은 의도적으로 pydantic / fastapi 에 의존하지 않는다. 전송 계층의
스키마(ProvenanceValue)는 RawField 로 옮겨 담아 넘긴다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping


class Origin:
    """필드 값의 출처."""

    UPSTREAM = "upstream"
    ESTIMATED = "estimated"
    DEFAULT = "default"


@dataclass(frozen=True)
class FieldSpec:
    """재무 프로필 필드 하나의 계약.

    Attributes:
        name: 필드 이름. 앞단 JSON 의 camelCase 가 아니라 내부 snake_case.
        kind: float 또는 int.
        required: True 면 strict 모드에서 없을 때 실패한다.
        default: 선택 필드가 없을 때 쓰는 값.
        default_from: 선택 필드의 기본값을 다른 필드에서 가져올 때 그 필드 이름.
        lenient_default: 필수 필드를 lenient 모드에서 채울 때 쓰는 값.
        minimum / maximum: 명백히 말이 안 되는 값만 걸러내는 범위. 실제 데이터를
            거부하지 않도록 필요한 곳에만 둔다.
    """

    name: str
    kind: type
    required: bool
    default: float | int | None = None
    default_from: str | None = None
    lenient_default: float | int | None = None
    minimum: float | None = None
    maximum: float | None = None


# 기본값 표의 단일 진실 원천. 숫자를 바꿀 곳은 여기뿐이다.
FINANCE_PROFILE_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("current_balance", float, required=True, lenient_default=1_500_000.0),
    FieldSpec(
        "emergency_fund_balance", float, required=True, lenient_default=600_000.0
    ),
    FieldSpec(
        "expected_card_payment_amount",
        float,
        required=True,
        lenient_default=200_000.0,
    ),
    FieldSpec(
        "days_until_card_due",
        int,
        required=True,
        lenient_default=14,
        minimum=0,
        maximum=366,
    ),
    FieldSpec(
        "savebox_balance",
        float,
        required=False,
        default_from="emergency_fund_balance",
    ),
    FieldSpec("available_fixed_expense", float, required=False, default=0.0),
    FieldSpec("available_fixed_income", float, required=False, default=1_000_000.0),
)

_SPEC_BY_NAME: dict[str, FieldSpec] = {spec.name: spec for spec in FINANCE_PROFILE_FIELDS}


@dataclass(frozen=True)
class RawField:
    """전송 계층에서 넘어온 값 하나와 앞단이 붙인 출처 표시."""

    value: Any
    is_default: bool = False
    is_estimated: bool = False


@dataclass(frozen=True)
class FieldViolation:
    field: str
    code: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "code": self.code, "detail": self.detail}


class InputContractViolation(ValueError):
    """입력이 계약을 어겼다. 위반은 한 번에 전부 담아 보고한다."""

    def __init__(self, violations: list[FieldViolation]) -> None:
        self.violations = tuple(violations)
        summary = "; ".join(f"{v.field}:{v.code}" for v in self.violations)
        super().__init__(f"finance profile violates input contract: {summary}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": "XAI_INPUT_CONTRACT_VIOLATION",
            "violations": [violation.to_dict() for violation in self.violations],
        }


@dataclass(frozen=True)
class ResolvedFinanceProfile:
    """계약을 통과한 재무 프로필. 값과 출처가 항상 함께 다닌다."""

    values: Mapping[str, float | int]
    origins: Mapping[str, str]
    _order: tuple[str, ...] = field(default=(), repr=False)

    def as_dict(self) -> dict[str, float | int]:
        """기존 analyzer 가 받던 finance_profile dict 와 같은 모양."""
        return {name: self.values[name] for name in self._order}

    @property
    def defaulted_fields(self) -> tuple[str, ...]:
        return tuple(n for n in self._order if self.origins[n] == Origin.DEFAULT)

    @property
    def estimated_fields(self) -> tuple[str, ...]:
        return tuple(n for n in self._order if self.origins[n] == Origin.ESTIMATED)

    @property
    def default_fallback_rate(self) -> float:
        """전체 필드 중 기본값으로 채워진 비율. 운영 목표는 필수 필드 기준 0."""
        if not self._order:
            return 0.0
        return len(self.defaulted_fields) / len(self._order)

    def to_report(self) -> dict[str, Any]:
        return {
            "origins": dict(self.origins),
            "defaulted_fields": list(self.defaulted_fields),
            "estimated_fields": list(self.estimated_fields),
            "default_fallback_rate": self.default_fallback_rate,
        }


def _is_missing(raw: RawField | None) -> bool:
    return raw is None or raw.value is None


def _coerce(spec: FieldSpec, raw_value: Any) -> tuple[float | int | None, FieldViolation | None]:
    """값 하나를 spec 에 맞춰 변환한다. 실패하면 위반을 돌려준다."""
    if isinstance(raw_value, bool):
        # bool 은 int 의 하위 타입이라 True 가 1.0 으로 조용히 통과한다.
        return None, FieldViolation(spec.name, "not_numeric", "bool 은 숫자가 아닙니다")

    if isinstance(raw_value, (int, float)):
        number = float(raw_value)
    elif isinstance(raw_value, str):
        try:
            number = float(raw_value.strip())
        except ValueError:
            return None, FieldViolation(
                spec.name, "not_numeric", f"숫자로 변환할 수 없습니다: {raw_value!r}"
            )
    else:
        return None, FieldViolation(
            spec.name, "not_numeric", f"지원하지 않는 타입: {type(raw_value).__name__}"
        )

    if not math.isfinite(number):
        return None, FieldViolation(spec.name, "not_finite", f"유한하지 않은 값: {number}")

    if spec.kind is int:
        if not number.is_integer():
            return None, FieldViolation(
                spec.name, "not_integer", f"정수여야 합니다: {number}"
            )
        result: float | int = int(number)
    else:
        result = number

    if spec.minimum is not None and result < spec.minimum:
        return None, FieldViolation(
            spec.name, "out_of_range", f"{result} < 최소값 {spec.minimum}"
        )
    if spec.maximum is not None and result > spec.maximum:
        return None, FieldViolation(
            spec.name, "out_of_range", f"{result} > 최대값 {spec.maximum}"
        )
    return result, None


def resolve_finance_profile(
    raw: Mapping[str, RawField | None],
    *,
    strict: bool = True,
) -> ResolvedFinanceProfile:
    """재무 프로필을 계약에 맞춰 확정한다.

    Args:
        raw: 필드 이름 -> RawField. 없는 필드는 키를 빼거나 None 으로 둔다.
        strict: True(운영)면 필수 필드가 없을 때 실패한다. False 는 기존 호출부
            (CLI, 진단 스크립트, 단위 테스트) 호환용이며, 필수 필드를 예전
            기본값으로 채우되 Origin.DEFAULT 로 기록한다.

    Raises:
        InputContractViolation: 모르는 필드, 깨진 값, strict 모드의 필수 필드
            누락. 위반은 처음 하나가 아니라 전부 모아서 한 번에 낸다.
    """
    violations: list[FieldViolation] = []

    for name in raw:
        if name not in _SPEC_BY_NAME:
            violations.append(
                FieldViolation(name, "unknown_field", "계약에 없는 필드입니다")
            )

    values: dict[str, float | int] = {}
    origins: dict[str, str] = {}
    pending_derived: list[FieldSpec] = []

    for spec in FINANCE_PROFILE_FIELDS:
        raw_field = raw.get(spec.name)

        if _is_missing(raw_field):
            if spec.required:
                if strict:
                    violations.append(
                        FieldViolation(spec.name, "missing", "필수 필드가 없습니다")
                    )
                    continue
                values[spec.name] = spec.kind(spec.lenient_default)  # type: ignore[arg-type]
                origins[spec.name] = Origin.DEFAULT
                continue
            if spec.default_from is not None:
                pending_derived.append(spec)
                continue
            values[spec.name] = spec.kind(spec.default)  # type: ignore[arg-type]
            origins[spec.name] = Origin.DEFAULT
            continue

        assert raw_field is not None  # _is_missing 이 False 이므로
        number, violation = _coerce(spec, raw_field.value)
        if violation is not None:
            violations.append(violation)
            continue
        assert number is not None
        values[spec.name] = number
        if raw_field.is_default:
            origins[spec.name] = Origin.DEFAULT
        elif raw_field.is_estimated:
            origins[spec.name] = Origin.ESTIMATED
        else:
            origins[spec.name] = Origin.UPSTREAM

    for spec in pending_derived:
        source = spec.default_from
        if source in values:
            values[spec.name] = spec.kind(values[source])
            origins[spec.name] = Origin.DEFAULT
        # source 가 위반으로 빠졌다면 이미 그 위반이 보고되므로 중복 보고하지 않는다.

    if violations:
        raise InputContractViolation(violations)

    return ResolvedFinanceProfile(
        values=values,
        origins=origins,
        _order=tuple(spec.name for spec in FINANCE_PROFILE_FIELDS),
    )
