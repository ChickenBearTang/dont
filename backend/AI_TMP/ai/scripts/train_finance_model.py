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
from ai.finance_engine.features import build_feature_frame  # noqa: E402
from ai.finance_engine.models import (  # noqa: E402
    DEFAULT_FAMILY,
    FAMILIES,
    FAMILY_LABELS,
    predict_labels,
    train_finance_model,
)
from ai.finance_engine.personas import (  # noqa: E402
    DEFAULT_TRAIN_POPULATION,
    PERSONA_PARAMS_VERSION,
    TRAIN_POPULATIONS,
    generate_training_rows,
)
from ai.finance_engine.synthetic import RULE_VERSION  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Train finance_engine model (LightGBM or CatBoost)")
    parser.add_argument("--output-dir", required=True, help="Directory to save model artifacts")
    parser.add_argument(
        "--family",
        choices=FAMILIES,
        default=DEFAULT_FAMILY,
        help="Model family. Production default is lightgbm; catboost is the challenger.",
    )
    parser.add_argument(
        "--population",
        choices=TRAIN_POPULATIONS,
        default=DEFAULT_TRAIN_POPULATION,
        help="Synthetic training distribution (default: mixed = uniform + 20s/30s personas)",
    )
    parser.add_argument("--rows", type=int, default=12000, help="Mock training row count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.2,
        help="Test split ratio between 0 and 0.5",
    )
    args = parser.parse_args()

    all_rows = generate_training_rows(args.population, row_count=args.rows, seed=args.seed)
    train_rows, test_rows = _train_test_split(
        all_rows,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    model = train_finance_model(
        train_rows, family=args.family, target_name=TARGET_NAME, seed=args.seed
    )

    extra_metadata: dict[str, Any] = {
        "train_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "total_row_count": len(all_rows),
        "class_labels": list(CLASS_LABELS),
        "generated_from": f"synthetic_{args.population}_v3",
        "training_population": args.population,
        "persona_params_version": PERSONA_PARAMS_VERSION,
        # 이 라벨은 손으로 쓴 규칙이 붙인 것이다. accuracy_test 는 '정확도'가 아니라
        # 규칙을 얼마나 흉내 냈는지를 뜻한다.
        "label_source": "synthetic_rule",
        "label_rule_version": RULE_VERSION,
    }
    if test_rows:
        from sklearn.metrics import accuracy_score, f1_score

        x_test = build_feature_frame(test_rows)
        y_test = [str(row[TARGET_NAME]) for row in test_rows]
        prediction = predict_labels(model, x_test)
        extra_metadata["accuracy_test"] = float(accuracy_score(y_test, prediction))
        # high 가 적어 accuracy 는 부풀려진다. macro-F1 을 같이 남긴다.
        extra_metadata["macro_f1_test"] = float(
            f1_score(y_test, prediction, labels=list(CLASS_LABELS), average="macro", zero_division=0)
        )

    artifact = save_finance_model_artifact(
        model=model,
        output_dir=Path(args.output_dir),
        schema_version=SCHEMA_VERSION,
        feature_names=list(training_feature_names()),
        target_name=TARGET_NAME,
        model_family=FAMILY_LABELS[args.family],
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
                "model_family": artifact.metadata["model_family"],
                "accuracy_test": artifact.metadata.get("accuracy_test"),
                "macro_f1_test": artifact.metadata.get("macro_f1_test"),
                "trained_at": datetime.now().isoformat(),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
