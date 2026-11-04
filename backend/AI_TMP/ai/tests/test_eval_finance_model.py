"""재무 모델 평가 하네스 테스트.

하네스가 올바른 숫자를 내는지가 중요하다. 틀린 평가는 모델이 없는 것보다 나쁘다.
"""

from __future__ import annotations

import unittest

from ..finance_engine.personas import PERSONA_NAMES
from ..scripts.eval_finance_model import (
    ALL_SEGMENT,
    FEATURE_SETS,
    evaluate,
    evaluate_by_persona,
    summarize,
    summarize_by_persona,
)

SMALL = {"train_rows": 800, "test_rows": 1500, "train_seeds": (1,), "test_seed": 99}


class FeatureSetDefinitionTest(unittest.TestCase):
    def test_원본7_구성이_호출하는_쪽_입력과_같다(self) -> None:
        from ..finance_engine.allowlist import raw_input_names

        self.assertEqual(tuple(FEATURE_SETS["raw7"]), raw_input_names())

    def test_raw7_derived3_구성이_운영_모델_열과_같다(self) -> None:
        from ..finance_engine.allowlist import training_feature_names

        self.assertEqual(tuple(FEATURE_SETS["raw7_derived3"]), training_feature_names())

    def test_옛_12개는_제거된_입력을_모두_포함한다(self) -> None:
        old12 = set(FEATURE_SETS["old12"])

        self.assertEqual(len(old12), 12)
        self.assertTrue(set(FEATURE_SETS["raw7"]) <= old12)
        self.assertIn("available_fixed_income", old12)
        self.assertIn("product_price_vs_monthly_spending", old12)

    def test_세트들은_서로_포함_관계다(self) -> None:
        raw7, raw7d3, old12 = (set(FEATURE_SETS[k]) for k in ("raw7", "raw7_derived3", "old12"))

        self.assertTrue(raw7 < raw7d3)
        self.assertEqual(len(raw7d3 - raw7), 3)
        self.assertTrue(raw7d3 < old12)


class EvaluateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = evaluate(**SMALL)

    def test_규칙_기준선은_구조상_1점이다(self) -> None:
        """라벨을 규칙이 붙였으니 규칙이 라벨을 맞히는 것은 당연하다. 모델은
        이 기준선을 넘을 수 없고, 이 사실을 결과에 항상 같이 보여줘야 한다."""
        rule = self.result["rule_baseline"]

        self.assertEqual(rule["macro_f1"], 1.0)
        self.assertEqual(rule["high_recall"], 1.0)

    def test_모든_후보가_같은_지표를_낸다(self) -> None:
        for name in (
            "raw7", "raw7_derived3", "old12",
            "catboost_raw7", "catboost_raw7_derived3",
            "logistic_raw7", "majority_class",
        ):
            with self.subTest(candidate=name):
                metrics = self.result["candidates"][name]
                for key in ("macro_f1", "high_recall", "high_precision", "high_pr_auc"):
                    self.assertIn(key, metrics)
                    self.assertGreaterEqual(metrics[key]["mean"], 0.0)
                    self.assertLessEqual(metrics[key]["mean"], 1.0)

    def test_항상_다수_클래스를_찍는_모델은_high를_전혀_못_찾는다(self) -> None:
        """정확도가 높아도 쓸모없는 모델을 지표가 걸러내는지 확인한다."""
        majority = self.result["candidates"]["majority_class"]

        self.assertEqual(majority["high_recall"]["mean"], 0.0)
        self.assertLess(majority["macro_f1"]["mean"], 0.5)

    def test_학습된_모델은_다수_클래스_기준선을_넘는다(self) -> None:
        trained = self.result["candidates"]["raw7"]["macro_f1"]["mean"]
        majority = self.result["candidates"]["majority_class"]["macro_f1"]["mean"]

        self.assertGreater(trained, majority)

    def test_테스트_세트가_학습_세트와_다른_시드다(self) -> None:
        self.assertNotIn(self.result["config"]["test_seed"], self.result["config"]["train_seeds"])

    def test_같은_설정은_같은_결과를_낸다(self) -> None:
        again = evaluate(**SMALL)

        self.assertEqual(
            again["candidates"]["raw7"]["macro_f1"],
            self.result["candidates"]["raw7"]["macro_f1"],
        )

    def test_요약은_합성_점수로_운영_모델을_바꾸지_말라고_경고한다(self) -> None:
        text = summarize(self.result)

        self.assertIn("운영 모델을 바꾸는 근거로 쓰면 안 된다", text)

    def test_요약_문자열에_점수의_의미_경고가_들어_있다(self) -> None:
        text = summarize(self.result)

        self.assertIn("규칙", text)
        self.assertIn("정확도가 아니", text)


class EvaluateByPersonaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = evaluate_by_persona(
            train_rows=800, test_rows=2000, train_seeds=(1,), test_seed=99,
            families=("lightgbm",), populations=("uniform", "mixed"),
        )

    def test_학습분포마다_전체와_유형별_점수를_낸다(self) -> None:
        self.assertEqual(set(self.result["candidates"]), {"lightgbm/uniform", "lightgbm/mixed"})
        for segments in self.result["candidates"].values():
            self.assertEqual(set(segments), {ALL_SEGMENT, *PERSONA_NAMES})
            for metrics in segments.values():
                for key in ("macro_f1", "high_recall", "high_precision", "high_pr_auc"):
                    self.assertGreaterEqual(metrics[key]["mean"], 0.0)
                    self.assertLessEqual(metrics[key]["mean"], 1.0)

    def test_유형별_high_비율이_보고된다(self) -> None:
        share = self.result["config"]["segment_class_share"]

        self.assertEqual(set(share), {ALL_SEGMENT, *PERSONA_NAMES})
        self.assertGreater(share["사회초년생"]["high"], share["30대후반_가구"]["high"])

    def test_테스트_시드가_학습_시드와_같으면_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_by_persona(train_rows=100, test_rows=100, train_seeds=(1,), test_seed=1)

    def test_요약에_가정값과_규칙_흉내_경고가_들어_있다(self) -> None:
        text = summarize_by_persona(self.result)

        self.assertIn("검증되지 않음", text)
        self.assertIn("규칙을 얼마나 흉내", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
