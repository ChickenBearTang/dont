"""재무 모델 평가 하네스: 입력 구성별 비교.

    cd backend/AI_TMP
    python -m ai.scripts.eval_finance_model
    python -m ai.scripts.eval_finance_model --train-rows 12000 --test-rows 50000

읽는 법 (중요)
    학습 데이터가 합성이고 라벨은 규칙(finance_engine/synthetic.py)이 붙였다.
    그래서 아래 점수는 '정확도'가 아니라 '규칙을 얼마나 흉내 냈나'다. 규칙 자신은
    구조상 1.0 점이며, 학습된 모델은 이 기준선을 넘을 수 없다. 이 하네스는
    "어떤 입력 구성이 규칙을 더 잘 따라가는가"를 비교하는 용도이고, 실제 사용자에게
    어느 쪽이 맞는지는 실제 결과 라벨이 생기기 전까지 알 수 없다.

설계
    - 테스트 세트는 학습과 다른 시드로 새로 만든다. 합성 데이터는 무한히 만들 수
      있으므로 k-fold 보다 큰 새 테스트 세트가 신뢰구간이 좁다. k-fold 는 데이터가
      귀한 곳(가격 모델 67행, 나중의 실제 데이터)에서 의미가 있다.
    - 학습 시드를 여러 개 돌려 학습 데이터 운에 따른 흔들림(std)을 같이 보고한다.
    - 지표: macro-F1, high 재현율, high 정밀도, high PR-AUC. 정확도는 보고하지
      않는다 (low 가 대부분이라 전부 low 로 찍어도 높게 나온다).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.finance_engine.allowlist import CLASS_LABELS, TARGET_NAME  # noqa: E402
from ai.finance_engine.synthetic import (  # noqa: E402
    RAW_INPUT_NAMES,
    RULE_VERSION,
    generate_rows,
    rule_bucket,
)
from ai.finance_engine.train_lgbm import DEFAULT_LGBM_PARAMS  # noqa: E402

_DERIVED3 = (
    "product_price_vs_monthly_spending",
    "projected_balance_after_purchase",
    "product_price_vs_emergency_fund",
)

# 비교할 입력 구성. raw7 이 새 모델, old12 가 이전 모델의 입력이다.
FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "raw7": RAW_INPUT_NAMES,
    "raw7_derived3": RAW_INPUT_NAMES + _DERIVED3,
    "old12": RAW_INPUT_NAMES
    + ("available_fixed_expense", "available_fixed_income")
    + _DERIVED3,
}

_METRICS = ("macro_f1", "high_recall", "high_precision", "high_pr_auc")


def _frame(rows: list[dict[str, Any]], columns: tuple[str, ...]):
    import pandas as pd

    return pd.DataFrame([{c: float(r[c]) for c in columns} for r in rows], columns=list(columns))


def _score(y_true: list[str], y_pred: list[str], high_proba: list[float] | None) -> dict[str, float]:
    from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score

    is_high = [1 if label == "high" else 0 for label in y_true]
    pr_auc = (
        float(average_precision_score(is_high, high_proba))
        if high_proba is not None
        else float(sum(is_high) / len(is_high))  # 확률이 없으면 무작위 수준
    )
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(CLASS_LABELS), average="macro", zero_division=0)),
        "high_recall": float(recall_score(y_true, y_pred, labels=["high"], average="macro", zero_division=0)),
        "high_precision": float(precision_score(y_true, y_pred, labels=["high"], average="macro", zero_division=0)),
        "high_pr_auc": pr_auc,
    }


def _aggregate(per_seed: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    import numpy as np

    return {
        key: {
            "mean": float(np.mean([m[key] for m in per_seed])),
            "std": float(np.std([m[key] for m in per_seed])),
        }
        for key in _METRICS
    }


def evaluate(
    *,
    train_rows: int = 12_000,
    test_rows: int = 50_000,
    train_seeds: tuple[int, ...] = (1, 2, 3),
    test_seed: int = 999,
) -> dict[str, Any]:
    """입력 구성별로 학습하고 같은 새 테스트 세트에서 비교한다."""
    import lightgbm as lgb
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if test_seed in train_seeds:
        raise ValueError("test_seed 는 학습 시드와 달라야 합니다")

    test = generate_rows(row_count=test_rows, seed=test_seed)
    y_test = [str(r[TARGET_NAME]) for r in test]

    per_candidate: dict[str, list[dict[str, float]]] = {
        name: [] for name in (*FEATURE_SETS, "logistic_raw7", "majority_class")
    }

    for seed in train_seeds:
        train = generate_rows(row_count=train_rows, seed=seed)
        y_train = [str(r[TARGET_NAME]) for r in train]

        for name, columns in FEATURE_SETS.items():
            model = lgb.LGBMClassifier(**{**DEFAULT_LGBM_PARAMS, "random_state": seed})
            model.fit(_frame(train, columns), y_train)
            x_test = _frame(test, columns)
            predicted = [str(p) for p in model.predict(x_test)]
            proba = model.predict_proba(x_test)
            high_index = [str(c) for c in model.classes_].index("high")
            per_candidate[name].append(
                _score(y_test, predicted, [float(row[high_index]) for row in proba])
            )

        logistic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
        logistic.fit(_frame(train, FEATURE_SETS["raw7"]), y_train)
        x_raw = _frame(test, FEATURE_SETS["raw7"])
        l_pred = [str(p) for p in logistic.predict(x_raw)]
        l_high = [str(c) for c in logistic.classes_].index("high")
        per_candidate["logistic_raw7"].append(
            _score(y_test, l_pred, [float(r[l_high]) for r in logistic.predict_proba(x_raw)])
        )

        majority = max(set(y_train), key=y_train.count)
        per_candidate["majority_class"].append(
            _score(y_test, [majority] * len(y_test), None)
        )

    rule_pred = [rule_bucket(r) for r in test]
    rule_scores = _score(y_test, rule_pred, [1.0 if p == "high" else 0.0 for p in rule_pred])

    class_share = {
        label: y_test.count(label) / len(y_test) for label in CLASS_LABELS
    }
    return {
        "config": {
            "train_rows": train_rows,
            "test_rows": test_rows,
            "train_seeds": list(train_seeds),
            "test_seed": test_seed,
            "rule_version": RULE_VERSION,
            "lgbm_params": {k: DEFAULT_LGBM_PARAMS[k] for k in ("n_estimators", "learning_rate", "num_leaves")},
            "test_class_share": class_share,
        },
        "rule_baseline": rule_scores,
        "candidates": {name: _aggregate(runs) for name, runs in per_candidate.items()},
    }


def summarize(result: dict[str, Any]) -> str:
    cfg = result["config"]
    lines = [
        "재무 모델 입력 구성 비교",
        f"  학습 {cfg['train_rows']:,}행 x 시드 {cfg['train_seeds']} / 새 테스트 {cfg['test_rows']:,}행 (시드 {cfg['test_seed']})",
        "  테스트 클래스 비율: "
        + ", ".join(f"{k} {v:.1%}" for k, v in cfg["test_class_share"].items()),
        "",
        f"  {'후보':<16}{'macro-F1':>16}{'high 재현율':>16}{'high 정밀도':>14}{'high PR-AUC':>14}",
    ]

    def cell(m: dict[str, float]) -> str:
        return f"{m['mean']:.3f}±{m['std']:.3f}"

    rule = result["rule_baseline"]
    lines.append(
        f"  {'규칙(기준선)':<14}{rule['macro_f1']:>16.3f}{rule['high_recall']:>16.3f}"
        f"{rule['high_precision']:>14.3f}{rule['high_pr_auc']:>14.3f}   <- 구조상 1.0"
    )
    for name, metrics in result["candidates"].items():
        lines.append(
            f"  {name:<16}{cell(metrics['macro_f1']):>16}{cell(metrics['high_recall']):>16}"
            f"{cell(metrics['high_precision']):>14}{cell(metrics['high_pr_auc']):>14}"
        )
    lines += [
        "",
        "주의: 라벨이 규칙으로 만든 합성 데이터라서 위 점수는 정확도가 아니라",
        "      '규칙을 얼마나 흉내 냈나'다. 규칙 자신이 1.0 이고 모델은 넘을 수 없다.",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare finance model input sets")
    parser.add_argument("--train-rows", type=int, default=12_000)
    parser.add_argument("--test-rows", type=int, default=50_000)
    parser.add_argument("--train-seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--test-seed", type=int, default=999)
    parser.add_argument("--json", action="store_true", help="결과를 JSON 으로 출력")
    args = parser.parse_args()

    result = evaluate(
        train_rows=args.train_rows,
        test_rows=args.test_rows,
        train_seeds=tuple(args.train_seeds),
        test_seed=args.test_seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else summarize(result))


if __name__ == "__main__":
    main()
