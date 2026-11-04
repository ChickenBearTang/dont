"""LightGBM / CatBoost 두 후보가 같은 계약으로 학습·저장·추론되는지 확인한다."""

from __future__ import annotations

import tempfile
import unittest

from ..finance_engine.allowlist import (
    CLASS_LABELS,
    SCHEMA_VERSION,
    TARGET_NAME,
    training_feature_names,
)
from ..finance_engine.artifacts import save_finance_model_artifact
from ..finance_engine.features import build_feature_frame
from ..finance_engine.inference import _load_cached_artifact, predict_finance_signal
from ..finance_engine.models import (
    DEFAULT_FAMILY,
    FAMILIES,
    FAMILY_LABELS,
    class_probability,
    predict_labels,
    train_finance_model,
)
from ..finance_engine.synthetic import generate_rows

PROFILE = {
    "current_balance": 900_000,
    "emergency_fund_balance": 150_000,
    "expected_card_payment_amount": 700_000,
    "days_until_card_due": 2,
    "savebox_balance": 150_000,
    "monthly_spending_30d": 1_300_000,
}


class ModelFamilyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = generate_rows(row_count=1500, seed=7)
        cls.frame = build_feature_frame(cls.rows[:200])

    def test_후보는_두_개이고_운영_기본값은_lightgbm이다(self) -> None:
        self.assertEqual(set(FAMILIES), {"lightgbm", "catboost"})
        self.assertEqual(DEFAULT_FAMILY, "lightgbm")

    def test_모르는_패밀리는_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            train_finance_model(self.rows[:50], family="xgboost")

    def test_두_후보_모두_같은_계약으로_예측한다(self) -> None:
        for family in FAMILIES:
            with self.subTest(family=family):
                model = train_finance_model(self.rows, family=family, seed=1)

                self.assertEqual(sorted(str(c) for c in model.classes_), sorted(CLASS_LABELS))
                labels = predict_labels(model, self.frame)
                self.assertEqual(len(labels), 200)  # CatBoost 의 2차원 출력도 1차원으로 펴진다
                self.assertTrue(set(labels) <= set(CLASS_LABELS))
                for row in model.predict_proba(self.frame):
                    self.assertAlmostEqual(float(sum(row)), 1.0, places=5)
                high = class_probability(model, self.frame, "high")
                self.assertTrue(all(0.0 <= p <= 1.0 for p in high))

    def test_같은_시드는_같은_예측을_낸다(self) -> None:
        for family in FAMILIES:
            with self.subTest(family=family):
                a = train_finance_model(self.rows, family=family, seed=5)
                b = train_finance_model(self.rows, family=family, seed=5)

                self.assertEqual(predict_labels(a, self.frame), predict_labels(b, self.frame))

    def test_학습은_원본7개만_있는_행으로도_된다(self) -> None:
        """실제 데이터에는 파생 열이 없다. 파생은 학습 쪽에서 계산한다."""
        from ..finance_engine.allowlist import raw_input_names

        raw_only = [
            {**{k: row[k] for k in raw_input_names()}, TARGET_NAME: row[TARGET_NAME]}
            for row in self.rows
        ]

        model = train_finance_model(raw_only, family="lightgbm", seed=1)

        self.assertEqual(list(model.feature_name_), list(training_feature_names()))

    def test_라벨이_없는_행은_거부한다(self) -> None:
        bad = [{k: v for k, v in self.rows[0].items() if k != TARGET_NAME}]

        with self.assertRaises(ValueError):
            train_finance_model(bad, family="lightgbm")


class ArtifactRoundTripTest(unittest.TestCase):
    """저장한 아티팩트를 운영 추론 경로(predict_finance_signal)로 읽어 쓸 수 있는가."""

    def test_두_후보_아티팩트_모두_운영_추론_경로를_통과한다(self) -> None:
        rows = generate_rows(row_count=1500, seed=11)
        for family in FAMILIES:
            with self.subTest(family=family), tempfile.TemporaryDirectory() as tmp:
                model = train_finance_model(rows, family=family, seed=1)
                save_finance_model_artifact(
                    model=model,
                    output_dir=tmp,
                    schema_version=SCHEMA_VERSION,
                    feature_names=list(training_feature_names()),
                    target_name=TARGET_NAME,
                    model_family=FAMILY_LABELS[family],
                )
                _load_cached_artifact.cache_clear()

                signal, state = predict_finance_signal(
                    current_price=2_500_000,
                    finance_profile=PROFILE,
                    explicit_model_path=tmp,
                    enabled=True,
                )

                self.assertTrue(state["enabled"], state)
                self.assertEqual(state["backend"], FAMILY_LABELS[family])
                total = sum(signal[f"finance_model_{c}_prob"] for c in CLASS_LABELS)
                self.assertAlmostEqual(total, 1.0, places=5)
                # 월 지출의 1.9배짜리 물건에 카드 결제까지 임박한 상황: 두 후보 모두 위험하다고 본다.
                self.assertEqual(signal["finance_model_risk_bucket"], "high")
        _load_cached_artifact.cache_clear()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
