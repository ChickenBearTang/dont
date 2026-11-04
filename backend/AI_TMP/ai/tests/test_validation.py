"""데이터 오염 검증 테스트.

실제로 발견된 오염을 규칙으로 고정한다 (data/price_training_rows_from_crawl.json):
  - 67행이 전부 한 상품이다 (canonical_product_id 가 하나)
  - 30일 가격 이력 피처가 전부 비어 있다
  - brand 가 모델명과 같다 ('f87'), seller_id 가 크롤러의 검색 URL 이다
  - 정답(current_effective_price)이 입력 피처에도 들어 있다 (타깃 누수)
  그 결과 가격 모델은 어떤 가격을 넣어도 36,707원만 답하는 상수 모델이 됐다.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from ..price_engine.allowlist import training_feature_names as price_features
from ..validation import (
    Severity,
    assess_price_artifact,
    validate_finance_rows,
    validate_price_training_rows,
    validate_training_setup,
)

NOW = datetime(2026, 4, 1, tzinfo=timezone.utc)
REAL_ROWS = Path(__file__).resolve().parents[1] / "data" / "price_training_rows_from_crawl.json"


def _good_row(i: int = 0, **override):
    row = {
        "canonical_product_id": f"p{i % 30}", "variant_id": None, "seller_id": f"seller{i}",
        "snapshot_date": f"2026-03-{1 + (i % 25):02d}T00:00:00+00:00",
        "current_effective_price": 50_000.0 + i,
        "avg_price_7d": 51_000.0, "avg_price_30d": 52_000.0,
        "min_price_30d": 45_000.0, "max_price_30d": 60_000.0, "price_volatility_30d": 3_000.0,
        "seller_count_same_product": 2.0, "release_age_days": 40.0, "shipping_fee_mode_30d": 0.0,
        "price_vs_avg_7d": (50_000.0 + i) / 51_000.0, "price_vs_avg_30d": (50_000.0 + i) / 52_000.0,
        "price_to_min_30d_gap": 5_000.0 + i, "price_to_max_30d_gap": 10_000.0 - i,
        "brand": "logitech", "category": "mouse", "seller_type": "merchant",
        "availability_status": "in_stock", "schema_version": "price-engine-mvp-v1",
    }
    row.update(override)
    return row


NO_HISTORY = {
    name: None for name in (
        "avg_price_7d", "avg_price_30d", "min_price_30d", "max_price_30d", "price_volatility_30d",
        "price_vs_avg_7d", "price_vs_avg_30d", "price_to_min_30d_gap", "price_to_max_30d_gap",
    )
}


def _codes(report):
    return {issue.code for issue in report.issues}


class CleanDataTest(unittest.TestCase):
    def test_깨끗한_데이터는_통과한다(self) -> None:
        rows = [_good_row(i) for i in range(300)]

        report = validate_price_training_rows(rows, now=NOW)

        self.assertTrue(report.ok, report.summary())
        self.assertEqual(report.count(Severity.ERROR), 0)


class RowRuleTest(unittest.TestCase):
    def check(self, row, code, severity=Severity.ERROR):
        report = validate_price_training_rows([row], now=NOW)
        matching = [i for i in report.issues if i.code == code]
        self.assertTrue(matching, f"{code} 없음: {_codes(report)}")
        self.assertEqual(matching[0].severity, severity)

    def test_가격이_0이하(self) -> None:
        self.check(_good_row(current_effective_price=0.0), "PRICE_NOT_POSITIVE")
        self.check(_good_row(current_effective_price=-5.0), "PRICE_NOT_POSITIVE")

    def test_가격이_비정상적으로_크다(self) -> None:
        self.check(_good_row(current_effective_price=2e9), "PRICE_OUT_OF_RANGE")

    def test_가격이_의심스럽게_작다(self) -> None:
        self.check(_good_row(current_effective_price=120.0), "PRICE_SUSPICIOUSLY_LOW", Severity.WARNING)

    def test_가격이_숫자가_아니다(self) -> None:
        self.check(_good_row(current_effective_price="21,200원"), "PRICE_NOT_NUMERIC")

    def test_최소가_최대가보다_크다(self) -> None:
        self.check(_good_row(min_price_30d=70_000.0, max_price_30d=60_000.0), "MIN_GT_MAX")

    def test_평균이_최소_최대_밖이다(self) -> None:
        self.check(_good_row(avg_price_30d=99_000.0), "AVG_OUT_OF_BOUNDS")

    def test_파생_비율이_계산식과_다르다(self) -> None:
        self.check(_good_row(price_vs_avg_30d=9.9), "DERIVED_MISMATCH")

    def test_파생_격차가_계산식과_다르다(self) -> None:
        self.check(_good_row(price_to_min_30d_gap=1.0), "DERIVED_MISMATCH")

    def test_변동성이_음수(self) -> None:
        self.check(_good_row(price_volatility_30d=-1.0), "NEGATIVE_VALUE")

    def test_판매처_수가_1_미만(self) -> None:
        self.check(_good_row(seller_count_same_product=0.0), "SELLER_COUNT_INVALID")

    def test_brand가_상품_ID와_같으면_검색어를_브랜드로_쓴_것이다(self) -> None:
        self.check(_good_row(canonical_product_id="f87", brand="f87"), "BRAND_IS_PRODUCT_ID")

    def test_brand가_비었거나_unknown(self) -> None:
        self.check(_good_row(brand="unknown"), "BRAND_UNKNOWN", Severity.WARNING)

    def test_판매자_ID가_URL이면_크롤러_검색_주소다(self) -> None:
        self.check(_good_row(seller_id="https://quasarzone.com/bbs/qb_saleinfo?page=1"), "SELLER_ID_IS_URL", Severity.WARNING)

    def test_날짜를_읽을_수_없다(self) -> None:
        self.check(_good_row(snapshot_date="어제"), "SNAPSHOT_DATE_INVALID")

    def test_미래_날짜(self) -> None:
        self.check(_good_row(snapshot_date="2027-01-01T00:00:00+00:00"), "SNAPSHOT_IN_FUTURE")

    def test_스키마_버전이_다르다(self) -> None:
        self.check(_good_row(schema_version="old"), "SCHEMA_VERSION_MISMATCH")

    def test_필수_필드_누락(self) -> None:
        row = _good_row()
        del row["canonical_product_id"]
        self.check(row, "MISSING_FIELD")

    def test_행이_객체가_아니다(self) -> None:
        report = validate_price_training_rows(["x"], now=NOW)  # type: ignore[list-item]
        self.assertIn("ROW_NOT_OBJECT", _codes(report))

    def test_이력_피처가_모두_비었으면_경고한다(self) -> None:
        row = _good_row(**NO_HISTORY)
        self.check(row, "NO_HISTORY_FEATURES", Severity.WARNING)


class DatasetRuleTest(unittest.TestCase):
    def test_행이_너무_적다(self) -> None:
        report = validate_price_training_rows([_good_row(i) for i in range(10)], now=NOW)

        self.assertIn("TOO_FEW_ROWS", _codes(report))

    def test_상품이_너무_적다(self) -> None:
        rows = [_good_row(i, canonical_product_id="same") for i in range(300)]

        self.assertIn("TOO_FEW_PRODUCTS", _codes(validate_price_training_rows(rows, now=NOW)))

    def test_이력_피처_채움률이_낮다(self) -> None:
        rows = [_good_row(i, **NO_HISTORY) for i in range(300)]

        self.assertIn("HISTORY_FEATURES_MOSTLY_NULL", _codes(validate_price_training_rows(rows, now=NOW)))

    def test_수집_시점이_하나뿐이다(self) -> None:
        rows = [_good_row(i, snapshot_date="2026-03-26T06:16:59+00:00") for i in range(300)]

        self.assertIn("SINGLE_SNAPSHOT_DATE", _codes(validate_price_training_rows(rows, now=NOW)))

    def test_같은_키가_중복된다(self) -> None:
        rows = [_good_row(1), _good_row(1)]

        self.assertIn("DUPLICATE_KEY", _codes(validate_price_training_rows(rows, now=NOW)))

    def test_같은_상품에서_튀는_가격을_잡는다(self) -> None:
        rows = [_good_row(i, canonical_product_id="same", current_effective_price=50_000.0 + i,
                          price_vs_avg_7d=None, price_vs_avg_30d=None, price_to_min_30d_gap=None,
                          price_to_max_30d_gap=None) for i in range(10)]
        rows.append(_good_row(99, canonical_product_id="same", current_effective_price=5_000_000.0,
                              price_vs_avg_7d=None, price_vs_avg_30d=None, price_to_min_30d_gap=None,
                              price_to_max_30d_gap=None))

        self.assertIn("PRICE_OUTLIER", _codes(validate_price_training_rows(rows, now=NOW)))

    def test_보고서는_이슈를_코드별로_센다(self) -> None:
        report = validate_price_training_rows([_good_row(1, brand="unknown"), _good_row(2, brand="unknown")], now=NOW)

        self.assertEqual(report.counts_by_code()["BRAND_UNKNOWN"], 2)
        self.assertIn("BRAND_UNKNOWN", report.to_dict()["counts_by_code"])


class TrainingSetupTest(unittest.TestCase):
    def test_정답이_입력_피처에_있으면_누수다(self) -> None:
        report = validate_training_setup(
            feature_names=["current_effective_price", "avg_price_30d"], target_name="current_effective_price"
        )

        self.assertFalse(report.ok)
        self.assertIn("TARGET_IN_FEATURES", _codes(report))

    def test_정답에서_계산되는_피처를_경고한다(self) -> None:
        report = validate_training_setup(
            feature_names=["avg_price_30d", "price_vs_avg_30d", "price_to_min_30d_gap"],
            target_name="current_effective_price",
            derived_from_target=("price_vs_avg_30d", "price_to_min_30d_gap"),
        )

        self.assertTrue(report.ok)  # 경고만
        self.assertIn("TARGET_DERIVED_FEATURES", _codes(report))

    def test_깨끗한_설정은_통과한다(self) -> None:
        report = validate_training_setup(feature_names=["a", "b"], target_name="y")

        self.assertTrue(report.ok)
        self.assertEqual(report.issues, [])


class PriceArtifactTrustTest(unittest.TestCase):
    def test_현재_운영_가격_모델은_신뢰할_수_없다(self) -> None:
        metadata = json.loads(
            (Path(__file__).resolve().parents[1] / "data" / "artifacts" / "price_retrain_model" / "metadata.json")
            .read_text(encoding="utf-8")
        )

        verdict = assess_price_artifact(metadata)

        self.assertFalse(verdict.trusted)
        self.assertIn("TARGET_IN_FEATURES", verdict.reasons)
        self.assertIn("TOO_FEW_TRAIN_ROWS", verdict.reasons)

    def test_정답이_피처에_없고_행이_충분하면_신뢰한다(self) -> None:
        verdict = assess_price_artifact({
            "target_name": "y", "feature_names": ["a", "b"], "train_row_count": 5000,
        })

        self.assertTrue(verdict.trusted, verdict.reasons)

    def test_기록된_상품_수가_적으면_신뢰하지_않는다(self) -> None:
        verdict = assess_price_artifact({
            "target_name": "y", "feature_names": ["a"], "train_row_count": 5000, "distinct_products": 1,
        })

        self.assertFalse(verdict.trusted)
        self.assertIn("TOO_FEW_PRODUCTS", verdict.reasons)

    def test_기록된_이력_피처_채움률이_낮으면_신뢰하지_않는다(self) -> None:
        verdict = assess_price_artifact({
            "target_name": "y", "feature_names": ["a"], "train_row_count": 5000, "distinct_products": 100,
            "history_feature_coverage": 0.0,
        })

        self.assertFalse(verdict.trusted)
        self.assertIn("HISTORY_FEATURES_MOSTLY_NULL", verdict.reasons)


class RealDataRegressionTest(unittest.TestCase):
    """저장소에 들어 있는 실제 67행에서 지금 알려진 오염이 전부 잡혀야 한다."""

    def test_실제_67행의_알려진_오염이_모두_잡힌다(self) -> None:
        rows = json.loads(REAL_ROWS.read_text(encoding="utf-8"))

        report = validate_price_training_rows(rows, now=datetime(2026, 4, 1, tzinfo=timezone.utc))
        codes = _codes(report)

        self.assertFalse(report.ok)
        for expected in ("TOO_FEW_ROWS", "TOO_FEW_PRODUCTS", "HISTORY_FEATURES_MOSTLY_NULL",
                         "BRAND_IS_PRODUCT_ID", "SELLER_ID_IS_URL", "SINGLE_SNAPSHOT_DATE", "NO_HISTORY_FEATURES"):
            self.assertIn(expected, codes)
        self.assertEqual(report.counts_by_code()["BRAND_IS_PRODUCT_ID"], 67)

    def test_현재_가격_모델_학습_설정이_누수로_잡힌다(self) -> None:
        report = validate_training_setup(
            feature_names=list(price_features()), target_name="current_effective_price",
            derived_from_target=("price_vs_avg_7d", "price_vs_avg_30d", "price_to_min_30d_gap", "price_to_max_30d_gap"),
        )

        self.assertFalse(report.ok)
        self.assertIn("TARGET_IN_FEATURES", _codes(report))
        self.assertIn("TARGET_DERIVED_FEATURES", _codes(report))


class FinanceRowsTest(unittest.TestCase):
    RAW = {"current_balance": 1e6, "emergency_fund_balance": 5e5, "savebox_balance": 4e5,
           "expected_card_payment_amount": 1e5, "days_until_card_due": 10, "monthly_spending_30d": 1e6,
           "product_price": 1e5}

    def test_정상_행은_통과한다(self) -> None:
        self.assertTrue(validate_finance_rows([{**self.RAW, "finance_risk_bucket": "low"}] * 3, check_rule=False).ok)

    def test_음수_결측_비유한_값을_잡는다(self) -> None:
        for key, value in (("current_balance", -1.0), ("product_price", float("nan")), ("savebox_balance", None),
                           ("monthly_spending_30d", float("inf"))):
            with self.subTest(key=key):
                report = validate_finance_rows([{**self.RAW, key: value, "finance_risk_bucket": "low"}], check_rule=False)
                self.assertFalse(report.ok)

    def test_결제일이_범위_밖(self) -> None:
        report = validate_finance_rows([{**self.RAW, "days_until_card_due": 45, "finance_risk_bucket": "low"}], check_rule=False)

        self.assertIn("DAYS_OUT_OF_RANGE", _codes(report))

    def test_알_수_없는_라벨(self) -> None:
        report = validate_finance_rows([{**self.RAW, "finance_risk_bucket": "danger"}], check_rule=False)

        self.assertIn("UNKNOWN_LABEL", _codes(report))

    def test_합성_데이터는_라벨이_규칙과_일치한다(self) -> None:
        from ..finance_engine.personas import generate_training_rows

        report = validate_finance_rows(generate_training_rows("mixed", row_count=500, seed=3), check_rule=True)

        self.assertTrue(report.ok, report.summary())

    def test_라벨이_규칙과_다르면_잡는다(self) -> None:
        from ..finance_engine.synthetic import generate_rows

        rows = generate_rows(row_count=200, seed=1)
        rows[0]["finance_risk_bucket"] = "high" if rows[0]["finance_risk_bucket"] != "high" else "low"

        report = validate_finance_rows(rows, check_rule=True)

        self.assertIn("LABEL_RULE_MISMATCH", _codes(report))

    def test_한_클래스가_거의_없으면_경고한다(self) -> None:
        rows = [{**self.RAW, "finance_risk_bucket": "low"}] * 300

        self.assertIn("CLASS_IMBALANCE", _codes(validate_finance_rows(rows, check_rule=False)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
