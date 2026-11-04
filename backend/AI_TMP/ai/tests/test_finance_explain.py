"""재무 모델의 실제 SHAP 설명 테스트.

예전 'SHAP' 은 손으로 만든 점수에 `입력 x 0.25` 를 곱한 값이었다. 여기서는 그 값이
정말 모델을 설명하는지를 성질로 검증한다: 가산성, 방향, 모델 종류 무관, 실패 시
가짜로 채우지 않기.
"""

from __future__ import annotations

import tempfile
import unittest

from ..finance_engine.allowlist import (
    SCHEMA_VERSION,
    TARGET_NAME,
    training_feature_names,
)
from ..finance_engine.artifacts import load_finance_model_artifact, save_finance_model_artifact
from ..finance_engine.explain import (
    EXPLANATION_GROUPS,
    explain_finance_signal,
    explain_model_features,
    group_contributions,
)
from ..finance_engine.features import build_feature_frame
from ..finance_engine.inference import (
    _load_cached_artifact,
    build_finance_inference_payload,
)
from ..finance_engine.models import FAMILY_LABELS, train_finance_model
from ..finance_engine.personas import generate_training_rows

TIGHT = dict(
    current_price=2_500_000,
    finance_profile=dict(
        current_balance=900_000, emergency_fund_balance=150_000, savebox_balance=150_000,
        expected_card_payment_amount=700_000, days_until_card_due=2, monthly_spending_30d=1_300_000,
    ),
)
HEALTHY = dict(
    current_price=89_000,
    finance_profile=dict(
        current_balance=8_000_000, emergency_fund_balance=3_000_000, savebox_balance=2_500_000,
        expected_card_payment_amount=300_000, days_until_card_due=20, monthly_spending_30d=1_400_000,
    ),
)


class GroupDefinitionTest(unittest.TestCase):
    def test_묶음은_모델_열_10개를_빠짐없이_겹치지_않게_나눈다(self) -> None:
        members = [name for group in EXPLANATION_GROUPS.values() for name in group]

        self.assertEqual(sorted(members), sorted(training_feature_names()))
        self.assertEqual(len(members), len(set(members)))

    def test_묶음_합은_열_합과_같다(self) -> None:
        features = {name: float(i) for i, name in enumerate(training_feature_names())}

        self.assertAlmostEqual(
            sum(group_contributions(features).values()), sum(features.values())
        )


class AdditivityTest(unittest.TestCase):
    """SHAP 의 핵심 성질: 기여도의 합 + 기준값 = 모델의 high raw margin."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_training_rows("mixed", row_count=1500, seed=21)

    def test_두_모델_모두_합이_모델_출력과_정확히_맞는다(self) -> None:
        for family in ("lightgbm", "catboost"):
            with self.subTest(family=family):
                model = train_finance_model(self.rows, family=family, seed=1)
                for case in (TIGHT, HEALTHY):
                    payload = build_finance_inference_payload(
                        current_price=case["current_price"], finance_profile=case["finance_profile"]
                    )
                    contributions, base = explain_model_features(model, payload)
                    frame = build_feature_frame([payload])
                    index = [str(c) for c in model.classes_].index("high")
                    if family == "lightgbm":
                        margin = float(model.predict(frame, raw_score=True)[0][index])
                    else:
                        margin = float(model.predict(frame, prediction_type="RawFormulaVal")[0][index])

                    self.assertAlmostEqual(sum(contributions.values()) + base, margin, places=4)

    def test_열마다_기여도가_있고_모델_열과_이름이_같다(self) -> None:
        model = train_finance_model(self.rows, family="lightgbm", seed=1)
        payload = build_finance_inference_payload(
            current_price=TIGHT["current_price"], finance_profile=TIGHT["finance_profile"]
        )

        contributions, _ = explain_model_features(model, payload)

        self.assertEqual(set(contributions), set(training_feature_names()))


class ExplainerAgreementTest(unittest.TestCase):
    """LightGBM 은 TreeExplainer, CatBoost 는 정확한 Shapley 를 쓴다. 두 길이 같은
    값을 내야 모델을 바꿔도 설명의 의미가 변하지 않는다."""

    def test_트리_방식과_정확한_Shapley가_같은_값을_낸다(self) -> None:
        import pandas as pd
        import shap
        from ..finance_engine.explain import _background_frame, _raw_margin_function

        model = train_finance_model(generate_training_rows("mixed", row_count=1500, seed=21), family="lightgbm", seed=1)
        payload = build_finance_inference_payload(
            current_price=TIGHT["current_price"], finance_profile=TIGHT["finance_profile"]
        )
        tree, tree_base = explain_model_features(model, payload)

        frame = build_feature_frame([payload])
        names = list(frame.columns)
        index = [str(c) for c in model.classes_].index("high")
        margin = _raw_margin_function(model, index)
        exact = shap.explainers.ExactExplainer(
            lambda data: margin(pd.DataFrame(data, columns=names)), _background_frame()
        )(frame)

        self.assertAlmostEqual(tree_base, float(exact.base_values[0]), places=4)
        for i, name in enumerate(names):
            self.assertAlmostEqual(tree[name], float(exact.values[0][i]), places=4, msg=name)


class DirectionTest(unittest.TestCase):
    """운영 아티팩트로, 상식과 같은 방향인가."""

    def test_빠듯한_사용자는_네_요인_모두_구매에_불리하다(self) -> None:
        scores, state = explain_finance_signal(**TIGHT)

        self.assertTrue(state["enabled"], state)
        self.assertEqual(state["backend"], "shap_tree")
        self.assertEqual(set(scores), set(EXPLANATION_GROUPS))
        for group, value in scores.items():
            self.assertLess(value, 0.0, group)

    def test_여유_있는_사용자는_네_요인_모두_구매에_유리하다(self) -> None:
        scores, _ = explain_finance_signal(**HEALTHY)

        for group, value in scores.items():
            self.assertGreater(value, 0.0, group)

    def test_비상자금을_늘리면_비상자금_요인이_더_유리해진다(self) -> None:
        def emergency_score(amount: int) -> float:
            profile = {**HEALTHY["finance_profile"], "emergency_fund_balance": amount}
            scores, _ = explain_finance_signal(current_price=HEALTHY["current_price"], finance_profile=profile)
            return scores["emergency_fund_balance"]

        self.assertGreater(emergency_score(3_000_000), emergency_score(0))

    def test_카드_결제일이_임박하면_카드_요인이_불리해진다(self) -> None:
        def card_score(days: int) -> float:
            profile = {**TIGHT["finance_profile"], "days_until_card_due": days}
            scores, _ = explain_finance_signal(current_price=TIGHT["current_price"], finance_profile=profile)
            return scores["days_until_card_due"]

        self.assertLess(card_score(1), card_score(28))

    def test_상태에_high_margin과_기준_인구가_기록된다(self) -> None:
        _, state = explain_finance_signal(**TIGHT)

        self.assertIn("high_margin", state)
        self.assertIn("base_margin", state)
        self.assertEqual(state["reference_population"], "personas-assumed-v1")


class FailureTest(unittest.TestCase):
    def test_모델을_읽을_수_없으면_가짜로_채우지_않고_빈_결과를_준다(self) -> None:
        scores, state = explain_finance_signal(explicit_model_path="/no/such/dir", **TIGHT)

        self.assertEqual(scores, {})
        self.assertFalse(state["enabled"])
        self.assertEqual(state["reason"], "model_load_failed")

    def test_옛_스키마_아티팩트는_거부한다(self) -> None:
        rows = generate_training_rows("uniform", row_count=300, seed=2)
        with tempfile.TemporaryDirectory() as tmp:
            save_finance_model_artifact(
                model=train_finance_model(rows, family="lightgbm", seed=1),
                output_dir=tmp,
                schema_version="finance-engine-mvp-v2",
                feature_names=list(training_feature_names()),
                target_name=TARGET_NAME,
            )
            _load_cached_artifact.cache_clear()

            scores, state = explain_finance_signal(explicit_model_path=tmp, **TIGHT)

        self.assertEqual(scores, {})
        self.assertEqual(state["reason"], "schema_version_mismatch")
        _load_cached_artifact.cache_clear()


class CatBoostArtifactTest(unittest.TestCase):
    def test_CatBoost_아티팩트도_같은_계약으로_설명된다(self) -> None:
        rows = generate_training_rows("mixed", row_count=2000, seed=5)
        with tempfile.TemporaryDirectory() as tmp:
            save_finance_model_artifact(
                model=train_finance_model(rows, family="catboost", seed=1),
                output_dir=tmp,
                schema_version=SCHEMA_VERSION,
                feature_names=list(training_feature_names()),
                target_name=TARGET_NAME,
                model_family=FAMILY_LABELS["catboost"],
            )
            _load_cached_artifact.cache_clear()
            load_finance_model_artifact(tmp)

            scores, state = explain_finance_signal(explicit_model_path=tmp, **TIGHT)
            healthy, _ = explain_finance_signal(explicit_model_path=tmp, **HEALTHY)

        self.assertTrue(state["enabled"], state)
        self.assertEqual(set(scores), set(EXPLANATION_GROUPS))
        self.assertLess(sum(scores.values()), 0.0)
        self.assertGreater(sum(healthy.values()), 0.0)
        _load_cached_artifact.cache_clear()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
