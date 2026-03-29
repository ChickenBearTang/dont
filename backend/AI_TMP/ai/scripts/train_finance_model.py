from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOT_PARENT = ROOT.parent
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.finance_engine.allowlist import (  # noqa: E402
    CLASS_LABELS,
    SCHEMA_VERSION,
    TARGET_NAME,
    training_feature_names,
)
from ai.finance_engine.artifacts import save_finance_model_artifact  # noqa: E402
from ai.finance_engine.train_lgbm import train_finance_model_lgbm  # noqa: E402


def _generate_mock_rows(*, row_count: int, seed: int) -> list[dict[str, Any]]:
    import numpy as np

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for _ in range(max(row_count, 1)):
        monthly_spending_30d_estimate = float(rng.uniform(700_000, 3_800_000))
        current_balance = float(rng.uniform(100_000, 4_500_000))
        emergency_fund_balance = float(rng.uniform(0, 4_000_000))
        expected_card_payment_amount = float(rng.uniform(0, 1_500_000))
        days_until_card_due = float(int(rng.integers(1, 31)))
        savebox_balance = float(
            max(
                0.0,
                emergency_fund_balance * float(rng.uniform(0.5, 1.6)),
            )
        )
        available_fixed_expense = float(
            monthly_spending_30d_estimate * float(rng.uniform(0.25, 0.8))
        )
        available_fixed_income = float(
            monthly_spending_30d_estimate * float(rng.uniform(0.55, 1.6))
        )
        product_price = float(rng.uniform(20_000, 950_000))
        product_price_vs_monthly_spending = (
            product_price / max(monthly_spending_30d_estimate, 1.0)
        )
        projected_balance_after_purchase = savebox_balance - product_price
        product_price_vs_emergency_fund = (
            product_price / max(emergency_fund_balance, 1.0)
        )

        risk_score = 0.0
        if product_price_vs_monthly_spending > 0.30:
            risk_score += 1.0
        if projected_balance_after_purchase < (monthly_spending_30d_estimate * 0.12):
            risk_score += 1.0
        if emergency_fund_balance < (monthly_spending_30d_estimate * 0.45):
            risk_score += 1.0
        if available_fixed_income < available_fixed_expense:
            risk_score += 1.0
        if (
            days_until_card_due <= 7
            and expected_card_payment_amount > (current_balance * 0.35)
        ):
            risk_score += 1.0

        if risk_score >= 3.0:
            finance_risk_bucket = "high"
        elif risk_score >= 1.5:
            finance_risk_bucket = "medium"
        else:
            finance_risk_bucket = "low"

        rows.append(
            {
                "current_balance": current_balance,
                "emergency_fund_balance": emergency_fund_balance,
                "expected_card_payment_amount": expected_card_payment_amount,
                "days_until_card_due": days_until_card_due,
                "savebox_balance": savebox_balance,
                "available_fixed_expense": available_fixed_expense,
                "available_fixed_income": available_fixed_income,
                "monthly_spending_30d_estimate": monthly_spending_30d_estimate,
                "product_price": product_price,
                "product_price_vs_monthly_spending": product_price_vs_monthly_spending,
                "projected_balance_after_purchase": projected_balance_after_purchase,
                "product_price_vs_emergency_fund": product_price_vs_emergency_fund,
                TARGET_NAME: finance_risk_bucket,
            }
        )
    return rows


def _train_test_split(
    rows: list[dict[str, Any]],
    *,
    test_ratio: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], []
    if test_ratio <= 0:
        return rows, []
    import random

    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    test_size = max(1, int(len(shuffled) * min(max(test_ratio, 0.0), 0.5)))
    test_rows = shuffled[:test_size]
    train_rows = shuffled[test_size:]
    if not train_rows:
        return shuffled, []
    return train_rows, test_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Train finance_engine LGBM model")
    parser.add_argument("--output-dir", required=True, help="Directory to save model artifacts")
    parser.add_argument("--rows", type=int, default=12000, help="Mock training row count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.2,
        help="Test split ratio between 0 and 0.5",
    )
    args = parser.parse_args()

    all_rows = _generate_mock_rows(row_count=args.rows, seed=args.seed)
    train_rows, test_rows = _train_test_split(
        all_rows,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    model = train_finance_model_lgbm(train_rows, target_name=TARGET_NAME)

    extra_metadata: dict[str, Any] = {
        "train_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "total_row_count": len(all_rows),
        "class_labels": list(CLASS_LABELS),
        "generated_from": "mock_finance_rows_v1",
    }
    if test_rows:
        from sklearn.metrics import accuracy_score
        import pandas as pd

        x_test = pd.DataFrame(
            [{name: row[name] for name in training_feature_names()} for row in test_rows],
            columns=list(training_feature_names()),
        )
        y_test = [str(row[TARGET_NAME]) for row in test_rows]
        prediction = model.predict(x_test)
        extra_metadata["accuracy_test"] = float(accuracy_score(y_test, prediction))

    artifact = save_finance_model_artifact(
        model=model,
        output_dir=Path(args.output_dir),
        schema_version=SCHEMA_VERSION,
        feature_names=list(training_feature_names()),
        target_name=TARGET_NAME,
        model_family="lightgbm_classifier",
        extra_metadata=extra_metadata,
    )
    print(
        json.dumps(
            {
                "output_dir": str(Path(args.output_dir)),
                "schema_version": artifact.metadata["schema_version"],
                "target_name": artifact.metadata["target_name"],
                "feature_count": len(artifact.metadata["feature_names"]),
                "train_row_count": artifact.metadata.get("train_row_count"),
                "test_row_count": artifact.metadata.get("test_row_count"),
                "accuracy_test": artifact.metadata.get("accuracy_test"),
                "trained_at": datetime.now().isoformat(),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
