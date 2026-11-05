"""평가 시점의 입력 스냅샷 저장소 (기본 꺼짐).

사용자 반응(좋았다/별로였다)을 학습 데이터로 쓰려면 '그때 어떤 입력이었는지'가 있어야 한다.
감사 로그에는 입력 해시만 있어서 나중에 입력을 복원할 수 없다. 켜면 재무 숫자와 판단 결과만
requestId 로 남긴다. 상품명, 가맹점, 거래 내역 같은 식별 가능한 문자열은 저장하지 않는다.

재무 정보는 개인정보다. 켜기 전에 보관 기간과 접근 권한을 정해야 한다 (docs/xai_budget_and_feedback.md).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any

from config import RUNTIME_DIR

# 스냅샷에 넣어도 되는 재무 필드. 숫자만이다.
SNAPSHOT_FINANCE_FIELDS = (
    "current_balance",
    "emergency_fund_balance",
    "savebox_balance",
    "expected_card_payment_amount",
    "days_until_card_due",
    "monthly_spending_30d",
    "available_fixed_expense",
    "available_fixed_income",
)


class JsonlXaiSnapshotStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (RUNTIME_DIR / "xai_input_snapshots.jsonl")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save(
        self,
        *,
        request_id: str,
        purchase_request_id: int,
        decision: str,
        price: float | None,
        finance_profile: dict[str, float | int],
        origins: dict[str, str],
        budget: dict[str, Any] | None,
        rule_version: str | None,
        model_version: str | None,
    ) -> None:
        row = {
            "requestId": request_id,
            "purchaseRequestId": purchase_request_id,
            "loggedAt": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "price": price,
            "financeProfile": {name: finance_profile[name] for name in SNAPSHOT_FINANCE_FIELDS if name in finance_profile},
            "origins": {name: origins[name] for name in SNAPSHOT_FINANCE_FIELDS if name in origins},
            "budget": budget,
            "ruleVersion": rule_version,
            "modelVersion": model_version,
        }
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with self._lock, self._path.open("a", encoding="utf-8") as handle:
            handle.write(line)
