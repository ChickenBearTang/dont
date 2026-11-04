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
from ai.finance_engine.synthetic import RULE_VERSION, generate_rows  # noqa: E402
from ai.finance_engine.train_lgbm import train_finance_model_lgbm  # noqa: E402


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

    all_rows = generate_rows(row_count=args.rows, seed=args.seed)
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
        "generated_from": "mock_finance_rows_v2",
        # 이 라벨은 손으로 쓴 규칙이 붙인 것이다. accuracy_test 는 '정확도'가 아니라
        # 규칙을 얼마나 흉내 냈는지를 뜻한다.
        "label_source": "synthetic_rule",
        "label_rule_version": RULE_VERSION,
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
