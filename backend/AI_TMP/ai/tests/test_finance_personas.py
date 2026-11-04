"""20~30대 유형별 합성 생성기 테스트.

이 데이터의 파라미터는 가정값이고 라벨은 규칙이 붙인다. 테스트가 고정하는 것은
'분포의 모양'(양수, 로그정규, 상관)과 '재현성'이지 현실 일치 여부가 아니다.
"""

from __future__ import annotations

import unittest
from collections import Counter

from ..finance_engine.allowlist import TARGET_NAME, raw_input_names, training_feature_names
from ..finance_engine.personas import (
    DEFAULT_TRAIN_POPULATION,
    PERSONA_NAMES,
    TRAIN_POPULATIONS,
    generate_persona_rows,
    generate_training_rows,
)
from ..finance_engine.synthetic import rule_bucket


class PersonaRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_persona_rows(row_count=6000, seed=1)

    def test_같은_시드는_같은_결과다(self) -> None:
        self.assertEqual(
            generate_persona_rows(row_count=50, seed=3), generate_persona_rows(row_count=50, seed=3)
        )
        self.assertNotEqual(
            generate_persona_rows(row_count=50, seed=3), generate_persona_rows(row_count=50, seed=4)
        )

    def test_모델_열과_라벨과_유형_이름을_가진다(self) -> None:
        row = self.rows[0]

        for name in training_feature_names():
            self.assertIn(name, row)
        self.assertIn(row[TARGET_NAME], {"low", "medium", "high"})
        self.assertIn(row["persona"], PERSONA_NAMES)

    def test_라벨은_규칙이_붙인다(self) -> None:
        for row in self.rows[:300]:
            self.assertEqual(row[TARGET_NAME], rule_bucket(row))

    def test_금액은_음수가_없다(self) -> None:
        """정규분포였다면 음수 잔액이 나왔을 것이다."""
        for name in ("current_balance", "emergency_fund_balance", "savebox_balance",
                     "expected_card_payment_amount", "monthly_spending_30d", "product_price"):
            self.assertGreaterEqual(min(r[name] for r in self.rows), 0.0, name)

    def test_가격은_범위_안이다(self) -> None:
        prices = [r["product_price"] for r in self.rows]

        self.assertGreaterEqual(min(prices), 10_000.0)
        self.assertLessEqual(max(prices), 3_000_000.0)

    def test_월_지출은_오른쪽으로_치우친_로그정규_모양이다(self) -> None:
        import numpy as np

        monthly = np.array([r["monthly_spending_30d"] for r in self.rows])

        self.assertGreater(float(monthly.mean()), float(np.median(monthly)))  # 평균 > 중앙값
        self.assertLess(abs(float(np.mean(np.log(monthly)) - np.median(np.log(monthly)))), 0.1)  # 로그는 대칭

    def test_월_지출이_큰_사람이_잔액도_큰_경향이다(self) -> None:
        import numpy as np

        sub = [r for r in self.rows if r["persona"] == "20대후반_직장인"]
        corr = np.corrcoef(
            np.log([r["monthly_spending_30d"] for r in sub]),
            np.log([r["current_balance"] for r in sub]),
        )[0, 1]

        self.assertGreater(float(corr), 0.4)

    def test_소득_수준_공통_요인이_잔액과_비상금_여력을_함께_움직인다(self) -> None:
        """잔액은 월 지출에 비례해 만들어지므로 위 상관은 구조상 생긴다. 공통 요인이
        실제로 작동하는지는 '월 지출 대비 비율'끼리의 상관으로 봐야 한다."""
        import numpy as np

        sub = [r for r in self.rows if r["emergency_fund_balance"] > 0]
        balance_months = np.log([r["current_balance"] / r["monthly_spending_30d"] for r in sub])
        emergency_months = np.log([r["emergency_fund_balance"] / r["monthly_spending_30d"] for r in sub])

        self.assertGreater(float(np.corrcoef(balance_months, emergency_months)[0, 1]), 0.15)

    def test_일부는_비상자금이_없다(self) -> None:
        zero_share = sum(1 for r in self.rows if r["emergency_fund_balance"] == 0.0) / len(self.rows)

        self.assertGreater(zero_share, 0.05)
        self.assertLess(zero_share, 0.4)

    def test_사회초년생이_고령_유형보다_high_비율이_높다(self) -> None:
        def high_share(name: str) -> float:
            sub = [r for r in self.rows if r["persona"] == name]
            return sum(1 for r in sub if r[TARGET_NAME] == "high") / len(sub)

        self.assertGreater(high_share("사회초년생"), high_share("30대후반_가구"))

    def test_유형_비율을_조절할_수_있다(self) -> None:
        rows = generate_persona_rows(row_count=500, seed=1, weights={"사회초년생": 1.0})

        self.assertEqual(set(r["persona"] for r in rows), {"사회초년생"})

    def test_모르는_유형이나_가중치_합_0은_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            generate_persona_rows(row_count=5, seed=1, weights={"없는유형": 1.0})
        with self.assertRaises(ValueError):
            generate_persona_rows(row_count=5, seed=1, weights={"사회초년생": 0.0})

    def test_모든_유형이_기본_비율로_나타난다(self) -> None:
        counts = Counter(r["persona"] for r in self.rows)

        self.assertEqual(set(counts), set(PERSONA_NAMES))


class TrainingPopulationTest(unittest.TestCase):
    def test_운영_학습_기본값은_혼합이다(self) -> None:
        self.assertEqual(DEFAULT_TRAIN_POPULATION, "mixed")

    def test_혼합은_균등과_유형을_절반씩_섞는다(self) -> None:
        rows = generate_training_rows("mixed", row_count=400, seed=1)

        self.assertEqual(len(rows), 400)
        self.assertEqual(sum(1 for r in rows if "persona" in r), 200)

    def test_모든_분포가_원본_입력_열을_가진다(self) -> None:
        for population in TRAIN_POPULATIONS:
            with self.subTest(population=population):
                rows = generate_training_rows(population, row_count=20, seed=2)
                for name in raw_input_names():
                    self.assertIn(name, rows[0])
                self.assertIn(TARGET_NAME, rows[0])

    def test_모르는_분포는_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            generate_training_rows("gaussian", row_count=5, seed=1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
