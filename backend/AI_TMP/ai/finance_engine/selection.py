"""운영 모델 선택 관문: LightGBM vs CatBoost.

전략
    두 후보를 모두 유지한다. 운영 모델은 기본적으로 LightGBM(incumbent)이고,
    실제 결과 라벨이 10만 건 이상 모였을 때에만 비교해서 바꿀지 정한다.

왜 이 관문이 필요한가
    합성 데이터는 몇 건이든 만들 수 있고 라벨도 우리가 쓴 규칙이 붙인 것이다.
    합성 10만 건으로 비교하면 '어느 쪽이 규칙을 더 잘 흉내 내나'만 알 수 있고,
    그 결과로 운영 모델을 바꾸면 안 된다. 그래서 10만 건은 '실제 라벨' 건수로만
    센다. 라벨 출처가 실제 결과가 아니면 건수와 상관없이 판정하지 않는다.

판정 방법
    같은 행 분할(층화 k-fold, 반복)에서 두 후보를 학습하고 분할별 macro-F1 차이를
    구한다. 분할끼리는 학습 데이터가 겹쳐 독립이 아니므로, 보통 t검정 대신
    Nadeau-Bengio 보정 t검정(분산에 test/train 비율 항을 더한다)을 쓴다.
    유의하지 않으면 무승부로 보고 기존 모델을 유지한다 (바꾸는 쪽에 증거 책임).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .allowlist import CLASS_LABELS, TARGET_NAME
from .features import build_feature_frame
from .models import DEFAULT_FAMILY, FAMILIES, fit_classifier, predict_labels

MIN_REAL_ROWS = 100_000
# 클래스별 최소 건수. 10만 건 중 high 가 몇 건뿐이면 재현율 비교가 의미 없다.
# (판단값이며 필요하면 인자로 바꾼다.)
MIN_CLASS_ROWS = 500
REAL_LABEL_SOURCE = "real_outcome"

STATUS_NOT_DECIDABLE = "not_decidable_non_real_labels"
STATUS_INSUFFICIENT_ROWS = "insufficient_rows"
STATUS_INSUFFICIENT_CLASS = "insufficient_class_rows"
STATUS_DECIDED = "decided"
STATUS_TIE = "tie_keep_incumbent"


@dataclass(frozen=True)
class SelectionDecision:
    status: str
    champion: str
    reason: str
    row_count: int
    details: dict[str, Any] = field(default_factory=dict)


def corrected_resampled_t_test(
    differences: Sequence[float],
    *,
    n_train: int,
    n_test: int,
) -> tuple[float, float]:
    """Nadeau & Bengio (2003) 보정 t검정. (t, 양측 p값)을 돌려준다.

    differences 는 분할마다의 점수 차이다. 차이가 전부 같으면(분산 0) 평균이 0이면
    (0, 1), 아니면 (±inf, 0) 이다.
    """
    from scipy import stats
    import numpy as np

    d = np.asarray(differences, dtype=float)
    count = len(d)
    if count < 2:
        raise ValueError("need at least 2 differences")
    mean = float(d.mean())
    variance = float(d.var(ddof=1))
    if variance == 0.0:
        if mean == 0.0:
            return 0.0, 1.0
        return (float("inf") if mean > 0 else float("-inf")), 0.0
    corrected = (1.0 / count + n_test / n_train) * variance
    t_value = mean / (corrected ** 0.5)
    p_value = float(2.0 * stats.t.sf(abs(t_value), df=count - 1))
    return float(t_value), p_value


def _class_counts(labels: Sequence[str]) -> dict[str, int]:
    return {label: sum(1 for item in labels if item == label) for label in CLASS_LABELS}


def decide_champion(
    rows: Sequence[Mapping[str, Any]],
    *,
    label_source: str,
    incumbent: str = DEFAULT_FAMILY,
    challenger: str = "catboost",
    min_rows: int = MIN_REAL_ROWS,
    min_class_rows: int = MIN_CLASS_ROWS,
    folds: int = 5,
    repeats: int = 2,
    seed: int = 0,
    alpha: float = 0.05,
    target_name: str = TARGET_NAME,
) -> SelectionDecision:
    """충분한 실제 라벨이 있을 때만 두 후보를 비교해 운영 모델을 정한다.

    rows 는 원본 7개 열과 라벨(target_name)을 가진 dict 목록이다.
    관문 순서: 라벨 출처 -> 전체 건수 -> 클래스별 건수 -> 비교.
    """
    for name in (incumbent, challenger):
        if name not in FAMILIES:
            raise ValueError(f"unknown model family {name!r}; choose from {list(FAMILIES)}")
    if incumbent == challenger:
        raise ValueError("incumbent and challenger must differ")

    total = len(rows)
    if label_source != REAL_LABEL_SOURCE:
        return SelectionDecision(
            status=STATUS_NOT_DECIDABLE,
            champion=incumbent,
            reason=(
                f"label_source={label_source!r} 는 실제 결과가 아니다. 이 라벨로 잰 점수는 "
                f"'규칙을 얼마나 흉내 냈나'일 뿐이라 운영 모델을 바꾸는 근거가 되지 않는다."
            ),
            row_count=total,
        )
    if total < min_rows:
        return SelectionDecision(
            status=STATUS_INSUFFICIENT_ROWS,
            champion=incumbent,
            reason=f"실제 라벨 {total:,}건 < 기준 {min_rows:,}건. 기준을 채울 때까지 {incumbent} 유지.",
            row_count=total,
        )

    labels = [str(row[target_name]) for row in rows]
    counts = _class_counts(labels)
    short = {label: n for label, n in counts.items() if n < min_class_rows}
    if short:
        return SelectionDecision(
            status=STATUS_INSUFFICIENT_CLASS,
            champion=incumbent,
            reason=f"클래스별 최소 {min_class_rows:,}건에 못 미침: {short}. {incumbent} 유지.",
            row_count=total,
            details={"class_counts": counts},
        )

    return _compare(
        rows,
        labels,
        incumbent=incumbent,
        challenger=challenger,
        folds=folds,
        repeats=repeats,
        seed=seed,
        alpha=alpha,
        class_counts=counts,
    )


def _compare(
    rows: Sequence[Mapping[str, Any]],
    labels: list[str],
    *,
    incumbent: str,
    challenger: str,
    folds: int,
    repeats: int,
    seed: int,
    alpha: float,
    class_counts: dict[str, int],
) -> SelectionDecision:
    import numpy as np
    from sklearn.metrics import f1_score, recall_score
    from sklearn.model_selection import RepeatedStratifiedKFold

    frame = build_feature_frame(rows)
    y = np.asarray(labels)
    splitter = RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=seed)

    f1: dict[str, list[float]] = {incumbent: [], challenger: []}
    high_recall: dict[str, list[float]] = {incumbent: [], challenger: []}
    n_train = n_test = 0
    for train_index, test_index in splitter.split(frame, y):
        n_train, n_test = len(train_index), len(test_index)
        x_train, x_test = frame.iloc[train_index], frame.iloc[test_index]
        y_train, y_test = list(y[train_index]), list(y[test_index])
        for family in (incumbent, challenger):
            model = fit_classifier(family, x_train, y_train, seed=seed)
            predicted = predict_labels(model, x_test)
            f1[family].append(
                float(f1_score(y_test, predicted, labels=list(CLASS_LABELS), average="macro", zero_division=0))
            )
            high_recall[family].append(
                float(recall_score(y_test, predicted, labels=["high"], average="macro", zero_division=0))
            )

    differences = [c - i for c, i in zip(f1[challenger], f1[incumbent])]
    t_value, p_value = corrected_resampled_t_test(differences, n_train=n_train, n_test=n_test)
    mean_diff = float(np.mean(differences))
    details = {
        "class_counts": class_counts,
        "folds": folds,
        "repeats": repeats,
        "macro_f1_mean": {k: float(np.mean(v)) for k, v in f1.items()},
        "high_recall_mean": {k: float(np.mean(v)) for k, v in high_recall.items()},
        "macro_f1_diff_challenger_minus_incumbent": mean_diff,
        "corrected_t": t_value,
        "p_value": p_value,
        "alpha": alpha,
    }
    if p_value < alpha:
        winner = challenger if mean_diff > 0 else incumbent
        return SelectionDecision(
            status=STATUS_DECIDED,
            champion=winner,
            reason=f"macro-F1 차이 {mean_diff:+.4f} (보정 p={p_value:.4f} < {alpha}). {winner} 채택.",
            row_count=len(rows),
            details=details,
        )
    return SelectionDecision(
        status=STATUS_TIE,
        champion=incumbent,
        reason=f"macro-F1 차이 {mean_diff:+.4f} 는 유의하지 않다 (보정 p={p_value:.4f} >= {alpha}). {incumbent} 유지.",
        row_count=len(rows),
        details=details,
    )
