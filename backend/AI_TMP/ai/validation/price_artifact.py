"""학습된 가격 모델 아티팩트를 쓸 만한지 메타데이터로 판정한다.

모델 파일을 열어 보지 않고 학습 때 남긴 기록(metadata.json)만 본다. 그래서 빠르고,
모델 종류와 무관하다. 기록에 없는 항목은 판단하지 않는다 (옛 아티팩트는 정답 누수와
학습 행 수만 판단할 수 있다).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .price_rows import MIN_HISTORY_COVERAGE, MIN_PRODUCTS, MIN_ROWS

REASON_TEXT = {
    "TARGET_IN_FEATURES": "정답이 입력 피처에도 들어 있다 (타깃 누수)",
    "TOO_FEW_TRAIN_ROWS": "학습 행이 너무 적다",
    "TOO_FEW_PRODUCTS": "학습에 쓴 상품 종류가 너무 적다",
    "HISTORY_FEATURES_MOSTLY_NULL": "학습 데이터의 가격 이력 피처가 대부분 비어 있다",
}


@dataclass(frozen=True)
class TrustVerdict:
    trusted: bool
    reasons: list[str]

    def describe(self) -> str:
        return "; ".join(REASON_TEXT.get(r, r) for r in self.reasons) or "문제 없음"


def assess_price_artifact(metadata: Mapping[str, Any]) -> TrustVerdict:
    reasons: list[str] = []
    target = metadata.get("target_name")
    features = metadata.get("feature_names") or []
    if target and target in features:
        reasons.append("TARGET_IN_FEATURES")

    rows = metadata.get("train_row_count")
    if isinstance(rows, (int, float)) and rows < MIN_ROWS:
        reasons.append("TOO_FEW_TRAIN_ROWS")

    products = metadata.get("distinct_products")
    if isinstance(products, (int, float)) and products < MIN_PRODUCTS:
        reasons.append("TOO_FEW_PRODUCTS")

    coverage = metadata.get("history_feature_coverage")
    if isinstance(coverage, (int, float)) and coverage < MIN_HISTORY_COVERAGE:
        reasons.append("HISTORY_FEATURES_MOSTLY_NULL")

    return TrustVerdict(trusted=not reasons, reasons=reasons)
