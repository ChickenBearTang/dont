"""XAI 입력 계약 테스트.

이 테스트는 실제 사고를 재현하는 회귀 테스트이기도 하다.

    앞단이 값을 못 채움 -> 뒷단이 조용히 기본값으로 메움 -> 판단/SHAP/DiCE 오염

계약이 지켜야 할 것은 세 가지다.
  1. 운영(strict) 경로에서는 필수 필드가 없거나 숫자가 아니면 즉시 실패한다.
  2. 기본값으로 채운 필드는 반드시 origin=default 로 기록된다.
  3. 기본값 표는 한 곳(FINANCE_PROFILE_FIELDS)에만 존재한다.
"""

from __future__ import annotations

import math
import unittest

from ..xai.input_contract import (
    FINANCE_PROFILE_FIELDS,
    InputContractViolation,
    Origin,
    RawField,
    resolve_finance_profile,
)


def _complete_raw() -> dict[str, RawField | None]:
    return {
        "current_balance": RawField(12_000_000),
        "emergency_fund_balance": RawField(3_000_000),
        "expected_card_payment_amount": RawField(150_000),
        "days_until_card_due": RawField(10),
        "savebox_balance": RawField(2_500_000),
        "available_fixed_expense": RawField(400_000),
        "available_fixed_income": RawField(3_000_000),
        "monthly_spending_30d": RawField(900_000),
    }


class StrictModeTest(unittest.TestCase):
    def test_완전한_입력은_전부_upstream으로_기록된다(self) -> None:
        resolved = resolve_finance_profile(_complete_raw())

        self.assertEqual(resolved.defaulted_fields, ())
        self.assertEqual(resolved.default_fallback_rate, 0.0)
        for name, origin in resolved.origins.items():
            self.assertEqual(origin, Origin.UPSTREAM, name)

    def test_필수_필드가_없으면_거부한다(self) -> None:
        """사고 재현: 예전에는 여기서 current_balance=1_500_000 이 조용히 들어갔다."""
        raw = _complete_raw()
        del raw["current_balance"]

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertEqual(
            [(v.field, v.code) for v in ctx.exception.violations],
            [("current_balance", "missing")],
        )

    def test_필수_필드의_값이_None이면_거부한다(self) -> None:
        raw = _complete_raw()
        raw["emergency_fund_balance"] = RawField(None)

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertEqual(ctx.exception.violations[0].code, "missing")

    def test_위반은_한_번에_전부_보고한다(self) -> None:
        """하나씩 고치며 재시도하게 만들지 않는다."""
        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile({})

        reported = {v.field for v in ctx.exception.violations}
        self.assertEqual(
            reported,
            {spec.name for spec in FINANCE_PROFILE_FIELDS if spec.required},
        )

    def test_숫자가_아니면_거부한다(self) -> None:
        for bad in ("abc", "", [], {}, object()):
            with self.subTest(value=bad):
                raw = _complete_raw()
                raw["current_balance"] = RawField(bad)
                with self.assertRaises(InputContractViolation) as ctx:
                    resolve_finance_profile(raw)
                self.assertEqual(ctx.exception.violations[0].code, "not_numeric")

    def test_bool은_숫자로_취급하지_않는다(self) -> None:
        """True 가 1.0 으로 조용히 변환되는 파이썬의 함정."""
        raw = _complete_raw()
        raw["current_balance"] = RawField(True)

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertEqual(ctx.exception.violations[0].code, "not_numeric")

    def test_NaN과_무한대는_거부한다(self) -> None:
        for bad in (math.nan, math.inf, -math.inf):
            with self.subTest(value=bad):
                raw = _complete_raw()
                raw["current_balance"] = RawField(bad)
                with self.assertRaises(InputContractViolation) as ctx:
                    resolve_finance_profile(raw)
                self.assertEqual(ctx.exception.violations[0].code, "not_finite")

    def test_숫자_문자열은_받아들인다(self) -> None:
        raw = _complete_raw()
        raw["current_balance"] = RawField("12000000")

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["current_balance"], 12_000_000.0)

    def test_결제일은_정수여야_하고_소수는_거부한다(self) -> None:
        """예전에는 int(10.9) 로 조용히 10 이 됐다."""
        raw = _complete_raw()
        raw["days_until_card_due"] = RawField(10.9)

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertEqual(ctx.exception.violations[0].code, "not_integer")

    def test_정수로_표현되는_실수_결제일은_받아들인다(self) -> None:
        raw = _complete_raw()
        raw["days_until_card_due"] = RawField(10.0)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["days_until_card_due"], 10)
        self.assertIsInstance(resolved.values["days_until_card_due"], int)

    def test_결제일_범위를_벗어나면_거부한다(self) -> None:
        for bad in (-1, 367):
            with self.subTest(value=bad):
                raw = _complete_raw()
                raw["days_until_card_due"] = RawField(bad)
                with self.assertRaises(InputContractViolation) as ctx:
                    resolve_finance_profile(raw)
                self.assertEqual(ctx.exception.violations[0].code, "out_of_range")

    def test_0은_정당한_값이다(self) -> None:
        """잔고 0원은 '값이 없음'이 아니다. 신규 가입자의 실제 상태다."""
        raw = _complete_raw()
        raw["current_balance"] = RawField(0)
        raw["emergency_fund_balance"] = RawField(0)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["current_balance"], 0.0)
        self.assertEqual(resolved.origins["current_balance"], Origin.UPSTREAM)

    def test_모르는_필드는_거부한다(self) -> None:
        """필드명 오타가 조용히 무시되던 문제."""
        raw = _complete_raw()
        raw["balance"] = RawField(300_000)  # current_balance 의 오타

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertIn(
            ("balance", "unknown_field"),
            [(v.field, v.code) for v in ctx.exception.violations],
        )


class OptionalFieldTest(unittest.TestCase):
    """Spring 은 고정 수입/지출을 아예 보내지 않는다. 이 현실을 계약이 반영한다."""

    def test_선택_필드가_없으면_기본값이고_origin이_default다(self) -> None:
        raw = _complete_raw()
        del raw["available_fixed_income"]
        del raw["available_fixed_expense"]

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["available_fixed_income"], 1_000_000.0)
        self.assertEqual(resolved.values["available_fixed_expense"], 0.0)
        self.assertEqual(resolved.origins["available_fixed_income"], Origin.DEFAULT)
        self.assertEqual(resolved.origins["available_fixed_expense"], Origin.DEFAULT)
        self.assertEqual(
            set(resolved.defaulted_fields),
            {"available_fixed_income", "available_fixed_expense"},
        )

    def test_None으로_보낸_선택_필드도_기본값으로_기록된다(self) -> None:
        raw = _complete_raw()
        raw["available_fixed_income"] = None

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.origins["available_fixed_income"], Origin.DEFAULT)

    def test_세이브박스가_없으면_비상자금을_따라간다(self) -> None:
        raw = _complete_raw()
        del raw["savebox_balance"]

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["savebox_balance"], 3_000_000.0)
        self.assertEqual(resolved.origins["savebox_balance"], Origin.DEFAULT)

    def test_잘못된_선택_필드는_기본값으로_덮지_않고_거부한다(self) -> None:
        """없는 것과 깨진 것은 다르다. 깨진 값을 기본값으로 가리면 사고가 숨는다."""
        raw = _complete_raw()
        raw["available_fixed_income"] = RawField("abc")

        with self.assertRaises(InputContractViolation) as ctx:
            resolve_finance_profile(raw)

        self.assertEqual(ctx.exception.violations[0].field, "available_fixed_income")

    def test_default_fallback_rate는_전체_필드_대비_비율이다(self) -> None:
        raw = _complete_raw()
        del raw["available_fixed_income"]
        del raw["available_fixed_expense"]

        resolved = resolve_finance_profile(raw)

        self.assertAlmostEqual(
            resolved.default_fallback_rate, 2 / len(FINANCE_PROFILE_FIELDS)
        )


class UpstreamFlagTest(unittest.TestCase):
    """앞단이 보낸 isDefault / isEstimated 를 무시하지 않는다."""

    def test_앞단이_기본값이라고_표시하면_default로_기록한다(self) -> None:
        raw = _complete_raw()
        raw["days_until_card_due"] = RawField(14, is_default=True)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["days_until_card_due"], 14)
        self.assertEqual(resolved.origins["days_until_card_due"], Origin.DEFAULT)
        self.assertIn("days_until_card_due", resolved.defaulted_fields)

    def test_앞단이_추정값이라고_표시하면_estimated로_기록한다(self) -> None:
        raw = _complete_raw()
        raw["savebox_balance"] = RawField(2_000_000, is_estimated=True)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.origins["savebox_balance"], Origin.ESTIMATED)
        self.assertEqual(resolved.estimated_fields, ("savebox_balance",))
        self.assertEqual(resolved.defaulted_fields, ())

    def test_기본값과_추정이_동시에_표시되면_default가_우선한다(self) -> None:
        raw = _complete_raw()
        raw["savebox_balance"] = RawField(0, is_default=True, is_estimated=True)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.origins["savebox_balance"], Origin.DEFAULT)

    def test_필수_필드가_기본값이어도_값_자체는_보존한다(self) -> None:
        """플래그는 판단을 바꾸지 않는다. 투명하게 기록할 뿐이다."""
        raw = _complete_raw()
        raw["current_balance"] = RawField(500_000, is_default=True)

        resolved = resolve_finance_profile(raw)

        self.assertEqual(resolved.values["current_balance"], 500_000.0)


class LenientModeTest(unittest.TestCase):
    """기존 호출부(CLI, 진단 스크립트, 단위 테스트) 호환용.

    값은 예전과 똑같이 채우되, 이제는 그 사실이 기록된다.
    """

    def test_빈_입력도_예외_없이_예전_기본값으로_채운다(self) -> None:
        resolved = resolve_finance_profile({}, strict=False)

        self.assertEqual(resolved.values["current_balance"], 1_500_000.0)
        self.assertEqual(resolved.values["emergency_fund_balance"], 600_000.0)
        self.assertEqual(resolved.values["expected_card_payment_amount"], 200_000.0)
        self.assertEqual(resolved.values["days_until_card_due"], 14)

    def test_관대_모드에서도_전부_default로_기록된다(self) -> None:
        resolved = resolve_finance_profile({}, strict=False)

        self.assertEqual(resolved.default_fallback_rate, 1.0)
        self.assertEqual(
            set(resolved.defaulted_fields),
            {spec.name for spec in FINANCE_PROFILE_FIELDS},
        )

    def test_관대_모드에서도_깨진_값은_거부한다(self) -> None:
        with self.assertRaises(InputContractViolation):
            resolve_finance_profile(
                {"current_balance": RawField("abc")}, strict=False
            )

    def test_관대_모드에서도_모르는_필드는_거부한다(self) -> None:
        with self.assertRaises(InputContractViolation):
            resolve_finance_profile({"balance": RawField(1)}, strict=False)


class SingleSourceOfTruthTest(unittest.TestCase):
    def test_기본값_표에_중복_필드가_없다(self) -> None:
        names = [spec.name for spec in FINANCE_PROFILE_FIELDS]
        self.assertEqual(len(names), len(set(names)))

    def test_필수_필드는_관대_모드용_기본값을_가진다(self) -> None:
        for spec in FINANCE_PROFILE_FIELDS:
            if spec.required:
                self.assertIsNotNone(spec.lenient_default, spec.name)

    def test_선택_필드는_기본값이나_파생_규칙을_가진다(self) -> None:
        for spec in FINANCE_PROFILE_FIELDS:
            if not spec.required:
                self.assertTrue(
                    spec.default is not None or spec.default_from is not None,
                    spec.name,
                )

    def test_as_dict는_기존_finance_profile과_같은_키를_가진다(self) -> None:
        resolved = resolve_finance_profile(_complete_raw())

        self.assertEqual(
            set(resolved.as_dict()),
            {
                "current_balance",
                "emergency_fund_balance",
                "expected_card_payment_amount",
                "days_until_card_due",
                "savebox_balance",
                "available_fixed_expense",
                "available_fixed_income",
                "monthly_spending_30d",
            },
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
