"""최근 거래 목록에서 최근 30일 지출을 계산한다.

월 지출은 재무 판단의 분모(상품 가격 / 월 지출 등)로 쓰이는 핵심 값이다.
예전에는 크롤링한 핫딜의 `평균가 x 건수`로 계산해서, 사용자의 실제 소비와
무관한 값이 들어갔다. 이 모듈은 Spring 이 이미 보내는 recentTransactions 로
대체한다.

Spring 이 보내는 데이터의 성질 (PrXaiContextService.toRecentTransaction)

- 금액은 max(amount, 0). 환불/취소는 음수가 아니라 0 으로 도착한다.
- 날짜는 yyyyMMdd, 최근 3개월을 날짜 내림차순으로 최대 FETCH_CAP 건.

원칙: 모르면 모른다고 답한다. 거래가 없다고 해서 0원을 쓴다고 단정하지 않는다.
없는 데이터를 0원으로 메우면 분모가 0이 되거나, 학습 때 본 적 없는 영역으로
모델을 밀어 넣는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

# Spring 이 한 번에 보내는 최대 건수 (PrXaiContextService 의 limit(50)).
FETCH_CAP = 50
WINDOW_DAYS = 30


@dataclass(frozen=True)
class RecentTransaction:
    transaction_date: str  # yyyyMMdd
    amount: int


@dataclass(frozen=True)
class SpendingEstimate:
    """최근 30일 지출 추정.

    Attributes:
        amount: 창 안의 지출 합. 모르면 None (이유는 reason).
        transaction_count: 합산에 쓰인 거래 수.
        truncated: 전달 건수가 상한에 걸려 창의 앞부분이 잘렸을 수 있다. 이때
            amount 는 실제보다 작을 수 있는 하한값이다.
        invalid_rows: 날짜를 읽지 못해 건너뛴 행 수.
        reason: amount 가 None 인 이유.
    """

    amount: float | None
    transaction_count: int
    truncated: bool
    invalid_rows: int
    reason: str | None = None


def _parse_date(raw: str) -> date | None:
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except (TypeError, ValueError):
        return None


def estimate_monthly_spending(
    transactions: Iterable[RecentTransaction],
    *,
    as_of: date,
    window_days: int = WINDOW_DAYS,
    fetch_cap: int = FETCH_CAP,
) -> SpendingEstimate:
    """as_of 를 포함한 최근 window_days 일의 지출 합을 계산한다."""
    rows = list(transactions)
    if not rows:
        return SpendingEstimate(None, 0, False, 0, reason="no_transactions")

    window_start = as_of - timedelta(days=window_days - 1)

    parsed: list[tuple[date, int]] = []
    invalid = 0
    for row in rows:
        day = _parse_date(row.transaction_date)
        if day is None:
            invalid += 1
            continue
        parsed.append((day, row.amount))

    if not parsed:
        return SpendingEstimate(None, 0, False, invalid, reason="unparseable")

    total = 0
    counted = 0
    for day, amount in parsed:
        if window_start <= day <= as_of and amount > 0:
            total += amount
            counted += 1

    # 상한에 걸렸는데 가장 오래된 거래가 아직 창 안이면, 그보다 오래된 창 안의
    # 거래가 잘려 나갔을 수 있다.
    oldest = min(day for day, _ in parsed)
    truncated = len(rows) >= fetch_cap and oldest > window_start

    if total <= 0:
        return SpendingEstimate(
            None, 0, truncated, invalid, reason="no_spending_in_window"
        )
    return SpendingEstimate(float(total), counted, truncated, invalid)
