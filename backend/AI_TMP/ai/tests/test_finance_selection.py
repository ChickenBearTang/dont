"""운영 모델 선택 관문 테스트.

약속: 실제 라벨 10만 건 전에는 어떤 점수가 나와도 운영 모델(LightGBM)을 바꾸지 않는다.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ..finance_engine import selection
from ..finance_engine.allowlist import TARGET_NAME
from ..finance_engine.selection import (
    MIN_REAL_ROWS,
    REAL_LABEL_SOURCE,
    STATUS_DECIDED,
    STATUS_INSUFFICIENT_CLASS,
    STATUS_INSUFFICIENT_ROWS,
    STATUS_NOT_DECIDABLE,
    STATUS_TIE,
    corrected_resampled_t_test,
    decide_champion,
)
from ..finance_engine.synthetic import generate_rows, rule_bucket


class _Oracle:
    """규칙 그대로 답하는 모델(항상 맞는다)."""

    classes_ = ["high", "low", "medium"]

    def predict(self, frame):
        return [rule_bucket(row) for row in frame.to_dict("records")]


class _AlwaysLow:
    classes_ = ["high", "low", "medium"]

    def predict(self, frame):
        return ["low"] * len(frame)


def _fit_factory(oracle_family: str | None):
    def fake_fit(family, frame, labels, *, seed=None, params=None):
        return _Oracle() if family == oracle_family else _AlwaysLow()

    return fake_fit


SMALL_GATE = {"min_rows": 600, "min_class_rows": 20, "folds": 3, "repeats": 2}


class GateConstantsTest(unittest.TestCase):
    def test_기준은_10만_건이다(self) -> None:
        self.assertEqual(MIN_REAL_ROWS, 100_000)


class GateOrderTest(unittest.TestCase):
    def test_합성_라벨은_건수가_충분해도_판정하지_않는다(self) -> None:
        rows = generate_rows(row_count=700, seed=1)

        decision = decide_champion(rows, label_source="synthetic_rule", **SMALL_GATE)

        self.assertEqual(decision.status, STATUS_NOT_DECIDABLE)
        self.assertEqual(decision.champion, "lightgbm")

    def test_실제_라벨이어도_건수가_모자라면_보류한다(self) -> None:
        rows = generate_rows(row_count=300, seed=1)

        decision = decide_champion(rows, label_source=REAL_LABEL_SOURCE, **SMALL_GATE)

        self.assertEqual(decision.status, STATUS_INSUFFICIENT_ROWS)
        self.assertEqual(decision.champion, "lightgbm")
        self.assertIn("300", decision.reason)

    def test_기본_기준에서는_수만_건도_보류한다(self) -> None:
        rows = generate_rows(row_count=3000, seed=1)

        decision = decide_champion(rows, label_source=REAL_LABEL_SOURCE)

        self.assertEqual(decision.status, STATUS_INSUFFICIENT_ROWS)

    def test_건수가_충분해도_어떤_클래스가_너무_적으면_보류한다(self) -> None:
        rows = generate_rows(row_count=700, seed=1)
        rows = [{**r, TARGET_NAME: "low" if r[TARGET_NAME] == "high" else r[TARGET_NAME]} for r in rows]

        decision = decide_champion(rows, label_source=REAL_LABEL_SOURCE, **SMALL_GATE)

        self.assertEqual(decision.status, STATUS_INSUFFICIENT_CLASS)
        self.assertIn("high", decision.reason)

    def test_같은_후보끼리나_모르는_후보는_거부한다(self) -> None:
        rows = generate_rows(row_count=10, seed=1)
        with self.assertRaises(ValueError):
            decide_champion(rows, label_source=REAL_LABEL_SOURCE, incumbent="lightgbm", challenger="lightgbm")
        with self.assertRaises(ValueError):
            decide_champion(rows, label_source=REAL_LABEL_SOURCE, challenger="xgboost")


class CompareOutcomeTest(unittest.TestCase):
    """모델을 가짜로 바꿔 관문의 판정 로직만 검증한다."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_rows(row_count=900, seed=2)

    def _run(self, oracle_family: str | None):
        with patch.object(selection, "fit_classifier", _fit_factory(oracle_family)):
            return decide_champion(self.rows, label_source=REAL_LABEL_SOURCE, **SMALL_GATE)

    def test_도전자가_확실히_낫으면_도전자를_채택한다(self) -> None:
        decision = self._run("catboost")

        self.assertEqual(decision.status, STATUS_DECIDED)
        self.assertEqual(decision.champion, "catboost")
        self.assertGreater(decision.details["macro_f1_diff_challenger_minus_incumbent"], 0.5)

    def test_기존이_확실히_낫으면_기존을_유지한다(self) -> None:
        decision = self._run("lightgbm")

        self.assertEqual(decision.status, STATUS_DECIDED)
        self.assertEqual(decision.champion, "lightgbm")

    def test_차이가_없으면_무승부로_기존을_유지한다(self) -> None:
        decision = self._run(None)  # 둘 다 같은 모델

        self.assertEqual(decision.status, STATUS_TIE)
        self.assertEqual(decision.champion, "lightgbm")

    def test_두_후보의_macro_F1과_high_재현율을_함께_보고한다(self) -> None:
        decision = self._run("catboost")

        self.assertEqual(set(decision.details["macro_f1_mean"]), {"lightgbm", "catboost"})
        self.assertEqual(set(decision.details["high_recall_mean"]), {"lightgbm", "catboost"})
        self.assertEqual(decision.details["high_recall_mean"]["catboost"], 1.0)
        self.assertEqual(decision.details["high_recall_mean"]["lightgbm"], 0.0)


class RealModelsSmokeTest(unittest.TestCase):
    def test_실제_LightGBM과_CatBoost로_끝까지_돈다(self) -> None:
        rows = generate_rows(row_count=900, seed=4)

        decision = decide_champion(
            rows, label_source=REAL_LABEL_SOURCE, min_rows=600, min_class_rows=20, folds=3, repeats=1
        )

        self.assertIn(decision.status, {STATUS_DECIDED, STATUS_TIE})
        self.assertIn(decision.champion, {"lightgbm", "catboost"})
        self.assertIn("p_value", decision.details)


class CorrectedTTestTest(unittest.TestCase):
    def test_보정_분산_항을_포함한다(self) -> None:
        """Nadeau-Bengio: 분산에 (1/k + n_test/n_train) 을 곱한다. 보통 t검정보다 보수적이다."""
        diffs = [0.01, 0.02, 0.015, 0.012, 0.018, 0.011, 0.02, 0.014, 0.016, 0.013]
        t_corrected, p_corrected = corrected_resampled_t_test(diffs, n_train=80, n_test=20)
        t_naive, p_naive = corrected_resampled_t_test(diffs, n_train=10**9, n_test=1)

        self.assertLess(abs(t_corrected), abs(t_naive))
        self.assertGreater(p_corrected, p_naive)

    def test_손으로_계산한_값과_같다(self) -> None:
        import math

        diffs = [1.0, 3.0]  # 평균 2, 분산(ddof=1) 2
        t, _ = corrected_resampled_t_test(diffs, n_train=3, n_test=1)

        expected = 2.0 / math.sqrt((1 / 2 + 1 / 3) * 2.0)
        self.assertAlmostEqual(t, expected, places=9)

    def test_차이가_전부_0이면_무승부다(self) -> None:
        self.assertEqual(corrected_resampled_t_test([0.0, 0.0, 0.0], n_train=8, n_test=2), (0.0, 1.0))

    def test_차이가_늘_같은_양수면_유의하다(self) -> None:
        t, p = corrected_resampled_t_test([0.5, 0.5, 0.5], n_train=8, n_test=2)

        self.assertEqual(t, float("inf"))
        self.assertEqual(p, 0.0)

    def test_분할이_하나뿐이면_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            corrected_resampled_t_test([0.1], n_train=8, n_test=2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
