"""재무 모델의 합성 학습 데이터와 라벨 규칙 테스트.

이 데이터는 난수로 만든 입력에 손으로 쓴 규칙으로 라벨을 붙인 것이다. 따라서
이 데이터로 잰 점수는 '정확도'가 아니라 '규칙을 얼마나 흉내 냈나'다.
규칙이 어떤 입력에 의존하는지를 코드로 고정해 두면, 입력을 줄이거나 늘릴 때
라벨이 몰래 달라지는 일을 막을 수 있다.
"""

from __future__ import annotations

import unittest
from collections import Counter

from ..finance_engine.allowlist import (
    CLASS_LABELS,
    SCHEMA_VERSION,
    TARGET_NAME,
    training_feature_names,
)
from ..finance_engine.synthetic import (
    RAW_INPUT_NAMES,
    RULE_VERSION,
    generate_rows,
    rule_bucket,
)


class AllowlistTest(unittest.TestCase):
    def test_입력은_원본_7개이고_파생값이_없다(self) -> None:
        self.assertEqual(
            training_feature_names(),
            (
                "current_balance",
                "emergency_fund_balance",
                "savebox_balance",
                "expected_card_payment_amount",
                "days_until_card_due",
                "monthly_spending_30d",
                "product_price",
            ),
        )

    def test_파생_비율_피처는_입력에_없다(self) -> None:
        for name in training_feature_names():
            self.assertNotIn("_vs_", name)
            self.assertNotIn("projected_", name)

    def test_Spring이_보내지_않는_값은_입력에_없다(self) -> None:
        """고정 수입/지출은 Spring 이 보내지 않아 운영에서 항상 기본값이었다."""
        self.assertNotIn("available_fixed_income", training_feature_names())
        self.assertNotIn("available_fixed_expense", training_feature_names())

    def test_스키마_버전이_올라갔다(self) -> None:
        """입력이 바뀌었으니 옛 아티팩트는 schema_version_mismatch 로 거부돼야 한다."""
        self.assertEqual(SCHEMA_VERSION, "finance-engine-mvp-v2")

    def test_합성_원본_이름이_허용목록과_같다(self) -> None:
        self.assertEqual(tuple(RAW_INPUT_NAMES), training_feature_names())


class GenerationTest(unittest.TestCase):
    def test_같은_시드는_같은_데이터를_만든다(self) -> None:
        self.assertEqual(
            generate_rows(row_count=50, seed=7), generate_rows(row_count=50, seed=7)
        )

    def test_다른_시드는_다른_데이터를_만든다(self) -> None:
        self.assertNotEqual(
            generate_rows(row_count=50, seed=7), generate_rows(row_count=50, seed=8)
        )

    def test_라벨은_규칙과_정확히_일치한다(self) -> None:
        for row in generate_rows(row_count=500, seed=1):
            self.assertEqual(row[TARGET_NAME], rule_bucket(row))

    def test_세_클래스가_모두_충분히_존재한다(self) -> None:
        """한 클래스가 거의 없으면 macro-F1 이 의미를 잃는다."""
        counts = Counter(r[TARGET_NAME] for r in generate_rows(row_count=5000, seed=3))

        for label in CLASS_LABELS:
            self.assertGreater(counts[label] / 5000, 0.03, f"{label}: {counts}")

    def test_비교_실험을_위해_제거된_입력도_열로_들어_있다(self) -> None:
        row = generate_rows(row_count=1, seed=1)[0]

        for name in (
            "available_fixed_expense",
            "available_fixed_income",
            "product_price_vs_monthly_spending",
            "projected_balance_after_purchase",
            "product_price_vs_emergency_fund",
        ):
            self.assertIn(name, row)


class RuleDependsOnlyOnRawInputsTest(unittest.TestCase):
    """라벨 규칙이 원본 7개에만 의존한다는 성질.

    제거한 입력(소득/지출/파생 비율)을 마음대로 바꿔도 라벨이 변하면 안 된다.
    그렇지 않으면 7개 입력 모델은 구조적으로 규칙을 배울 수 없다.
    """

    def test_제거된_입력을_바꿔도_라벨이_같다(self) -> None:
        for row in generate_rows(row_count=300, seed=5):
            mutated = dict(row)
            mutated["available_fixed_income"] = 0.0
            mutated["available_fixed_expense"] = 9e9
            mutated["product_price_vs_monthly_spending"] = -1.0
            mutated["projected_balance_after_purchase"] = 1e12
            mutated["product_price_vs_emergency_fund"] = 123.0

            self.assertEqual(rule_bucket(mutated), rule_bucket(row))

    def test_원본_입력을_바꾸면_라벨이_바뀔_수_있다(self) -> None:
        """위 성질이 '규칙이 아무것도 안 본다'는 뜻이 아님을 확인한다."""
        base = {
            "current_balance": 5_000_000.0,
            "emergency_fund_balance": 3_000_000.0,
            "savebox_balance": 3_000_000.0,
            "expected_card_payment_amount": 0.0,
            "days_until_card_due": 20.0,
            "monthly_spending_30d": 2_000_000.0,
            "product_price": 100_000.0,
        }
        risky = dict(base, product_price=900_000.0, savebox_balance=100_000.0,
                     emergency_fund_balance=100_000.0)

        self.assertEqual(rule_bucket(base), "low")
        self.assertEqual(rule_bucket(risky), "high")

    def test_규칙_버전이_기록된다(self) -> None:
        self.assertEqual(RULE_VERSION, "finance-risk-rule-v2")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
