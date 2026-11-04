"""XAI 모듈이 어떻게 동작하는지 단계별로 보여주는 데모.

DB, Spring, 외부 네트워크 없이 노트북에서 그대로 실행된다.

    cd backend/AI_TMP
    python -m ai.scripts.xai_walkthrough              # 3개 시나리오 전부
    python -m ai.scripts.xai_walkthrough tight        # 하나만
    AI_XAI_HEAVY_ENABLED=0 python -m ai.scripts.xai_walkthrough   # DiCE 끄기(빠름)

왜 DB 없이 도는가
    재무 DB 는 Spring 쪽에 있다. Python 은 Spring 이 보낸 JSON 한 건만 받으므로,
    아래 SCENARIOS 의 payload 가 곧 Spring 이 보내는 요청과 같은 모양이다.
    모델 파일(LightGBM 2개)은 data/artifacts 에 커밋돼 있다.
    가격 이력 DB(Postgres)만 없을 뿐이며, 그러면 NO_PRICE_HISTORY 경고가 붙고
    가격 평가가 degraded 로 내려간다. 실패하지 않는다.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("AI_XAI_HEAVY_ENABLED", "1")

from ai.xai.input_contract import InputContractViolation  # noqa: E402
from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore  # noqa: E402
from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest  # noqa: E402
from domain.xai_purchase.service import (  # noqa: E402
    _resolve_request_finance_profile,
    evaluate_pr_purchase_xai,
)


def _pv(value: object, **flags: bool) -> dict[str, object]:
    return {
        "value": value,
        "source": "demo",
        "snapshotId": "demo-1",
        "isDefault": flags.get("is_default", False),
        "isEstimated": flags.get("is_estimated", False),
    }


def _recent(*days_ago_and_amount: tuple[int, int]) -> list[dict[str, object]]:
    """오늘 기준 N일 전 거래. 월 지출이 거래에서 계산되는 것을 보여주기 위한 데모용."""
    today = datetime.now(timezone.utc).date()
    return [
        {
            "transactionDate": (today - timedelta(days=days)).strftime("%Y%m%d"),
            "transactionTime": "120000",
            "merchantName": "데모상점",
            "categoryName": "식비",
            "transactionAmount": amount,
        }
        for days, amount in days_ago_and_amount
    ]


def _request(
    *,
    item: str,
    price: int,
    finance: dict[str, object],
    transactions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "requestId": f"demo-{item}",
        "schemaVersion": "v1",
        "contextVersion": "v1",
        "purchase": {
            "postId": 1,
            "title": f"{item} 구매 요청",
            "itemName": item,
            "content": "데모",
            "category": "IT",
            "purchaseUrl": None,  # 네트워크 호출을 막는다
            "priceAmount": _pv(price),
        },
        "financeProfile": finance,
        "recentTransactions": transactions or [],
    }


SCENARIOS: dict[str, dict[str, object]] = {
    "healthy": _request(
        item="기계식 키보드",
        price=89_000,
        finance={
            "currentBalance": _pv(8_000_000),
            "emergencyFundBalance": _pv(3_000_000),
            "expectedCardPaymentAmount": _pv(300_000),
            "daysUntilCardDue": _pv(20),
            "saveboxBalance": _pv(2_500_000),
            "availableFixedExpense": _pv(600_000),
            "availableFixedIncome": _pv(3_200_000),
        },
        transactions=_recent((2, 150_000), (6, 90_000), (11, 210_000), (19, 130_000), (27, 120_000)),
    ),
    "tight": _request(
        item="맥북 프로",
        price=2_500_000,
        finance={
            "currentBalance": _pv(900_000),
            "emergencyFundBalance": _pv(150_000),
            "expectedCardPaymentAmount": _pv(700_000),
            "daysUntilCardDue": _pv(2),
            "saveboxBalance": _pv(150_000),
            "availableFixedExpense": _pv(900_000),
            "availableFixedIncome": _pv(1_500_000),
        },
        transactions=_recent((1, 400_000), (5, 350_000), (12, 300_000), (20, 250_000)),
    ),
    # Spring 이 실제로 보내는 모양: 고정 수입/지출/세이브박스가 없고, 거래가 창 밖이거나 없다.
    "spring_like": _request(
        item="모니터",
        price=350_000,
        finance={
            "currentBalance": _pv(1_800_000),
            "emergencyFundBalance": _pv(600_000),
            "expectedCardPaymentAmount": _pv(250_000),
            "daysUntilCardDue": _pv(14, is_default=True),
        },
    ),
}


def _bar(title: str) -> None:
    print(f"\n{'─' * 70}\n  {title}\n{'─' * 70}")


def _won(value: object) -> str:
    try:
        return f"{int(float(str(value))):,}원"
    except (TypeError, ValueError):
        return str(value)


def run(name: str, payload: dict[str, object]) -> None:
    print(f"\n{'═' * 70}\n  시나리오: {name}\n{'═' * 70}")
    request = PurchaseXaiEvaluationRequest.model_validate(payload)

    _bar("1단계  입력 계약  (앞단 데이터를 믿어도 되는가)")
    try:
        profile = _resolve_request_finance_profile(request)
    except InputContractViolation as exc:
        print("  ✗ 계약 위반 — 여기서 중단됩니다 (HTTP 422)")
        for violation in exc.violations:
            print(f"    - {violation.field}: {violation.code}  {violation.detail}")
        return
    for field_name, value in profile.as_dict().items():
        origin = profile.origins[field_name]
        mark = {"upstream": "  ", "estimated": "~ ", "default": "! "}[origin]
        print(f"  {mark}{field_name:<30} {value!s:>12}   [{origin}]")
    print(f"  → default_fallback_rate = {profile.default_fallback_rate:.0%}")

    with tempfile.TemporaryDirectory() as tmp:
        store = JsonlXaiAuditLogStore(Path(tmp) / "audit.jsonl")
        with patch("domain.xai_purchase.service._AUDIT_STORE", store):
            response = evaluate_pr_purchase_xai(request)
        log_lines = (Path(tmp) / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    # 감사 로그는 한 줄이 곧 항목 하나다 (audit_store.save 참고).
    fired = [
        rule
        for line in log_lines
        for rule in json.loads(line).get("fired_rule_ids", [])
    ]

    _bar("2단계  모델 신호  (LightGBM 2개가 돌았는가)")
    engines = response.runtime_engines
    for label in ("price_model", "finance_model", "shap", "dice"):
        print(f"  {label:<14} {getattr(engines, label, '?')}")

    _bar("3단계  판단  (규칙 엔진 — 학습 모델이 아니라 if/else)")
    print(f"  결정        {response.decision}")
    print(f"  발화한 규칙  {', '.join(fired) or '(기록 없음)'}")
    print(f"  확신도      {response.confidence.decision_confidence:.2f}")
    print(f"  재무 상태    {response.financial_evaluation.status}")
    print(f"  가격 상태    {response.price_evaluation.status}")

    _bar("4단계  SHAP  (왜 그렇게 판단했나)")
    for factor in response.top_factors:
        arrow = "▲" if factor.direction == "positive" else "▼"
        print(f"  {arrow} {factor.impact:6.3f}  {factor.label}")
    if not response.top_factors:
        print("  (없음)")

    _bar("5단계  DiCE  (무엇을 바꾸면 되나)")
    for cf in response.counterfactuals:
        print(f"  → {cf.label}")
        print(f"      바뀌는 결정: {cf.target_decision}   validated={cf.validated}")
    if not response.counterfactuals:
        print("  (없음)")

    _bar("6단계  신뢰도와 경고")
    print(f"  dataCompleteness     {response.confidence.data_completeness:.2f}")
    print(f"  explanationFidelity  {response.confidence.explanation_fidelity:.2f}")
    for warning in response.warnings:
        print(f"  ⚠ {warning}")


def main(argv: list[str]) -> int:
    selected = argv[1:] or list(SCENARIOS)
    unknown = [n for n in selected if n not in SCENARIOS]
    if unknown:
        print(f"알 수 없는 시나리오: {unknown}. 선택지: {list(SCENARIOS)}")
        return 2
    for name in selected:
        run(name, SCENARIOS[name])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
