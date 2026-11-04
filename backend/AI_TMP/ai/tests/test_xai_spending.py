"""최근 거래에서 월 지출을 계산하는 규칙 테스트.

이전에는 월 지출을 `상품 평균가 x 건수`(크롤링한 핫딜 가격 이력)로 계산해서,
사용자의 실제 소비와 무관한 값이 판단의 분모로 쓰였다. Spring 이 이미 보내는
recentTransactions 로 바꾼다.

Spring 이 보내는 데이터의 성질 (PrXaiContextService.toRecentTransaction):
  - 금액은 max(amount, 0): 환불/취소는 음수가 아니라 0 으로 도착한다.
  - 날짜는 yyyyMMdd, 최근 3개월을 날짜 내림차순으로 최대 50건.
"""

from __future__ import annotations

import unittest
from datetime import date

from ..xai.spending import (
    FETCH_CAP,
    RecentTransaction,
    estimate_monthly_spending,
)

TODAY = date(2026, 8, 21)


def _tx(day: date, amount: int) -> RecentTransaction:
    return RecentTransaction(transaction_date=day.strftime("%Y%m%d"), amount=amount)


class WindowSumTest(unittest.TestCase):
    def test_최근_30일_거래만_합산한다(self) -> None:
        txs = [
            _tx(date(2026, 8, 20), 10_000),
            _tx(date(2026, 8, 1), 20_000),
            _tx(date(2026, 7, 23), 30_000),  # 창의 첫날 (8/21 포함 30일 = 7/23 ~ 8/21)
            _tx(date(2026, 7, 22), 999_999), # 창 밖
        ]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertEqual(estimate.amount, 60_000.0)
        self.assertEqual(estimate.transaction_count, 3)

    def test_창의_경계는_오늘_포함_30일이다(self) -> None:
        inside = estimate_monthly_spending([_tx(date(2026, 7, 23), 1_000)], as_of=TODAY)
        outside = estimate_monthly_spending([_tx(date(2026, 7, 22), 1_000)], as_of=TODAY)

        # 7/23 ~ 8/21 이 30일이다 (오늘 포함).
        self.assertEqual(inside.amount, 1_000.0)
        self.assertIsNone(outside.amount)

    def test_미래_날짜는_무시한다(self) -> None:
        """시계 오차나 잘못된 데이터가 지출을 부풀리지 않게 한다."""
        txs = [_tx(date(2026, 8, 22), 500_000), _tx(date(2026, 8, 20), 10_000)]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertEqual(estimate.amount, 10_000.0)

    def test_금액이_0이거나_음수인_거래는_합산에_영향이_없다(self) -> None:
        txs = [_tx(date(2026, 8, 20), 0), _tx(date(2026, 8, 19), -5_000), _tx(date(2026, 8, 18), 7_000)]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertEqual(estimate.amount, 7_000.0)


class UnknownTest(unittest.TestCase):
    """없는 것을 0원으로 단정하지 않는다. 모르면 모른다고 답한다."""

    def test_거래가_하나도_없으면_모름이다(self) -> None:
        estimate = estimate_monthly_spending([], as_of=TODAY)

        self.assertIsNone(estimate.amount)
        self.assertEqual(estimate.reason, "no_transactions")

    def test_거래는_있지만_창_안에_없으면_모름이다(self) -> None:
        estimate = estimate_monthly_spending([_tx(date(2026, 5, 1), 50_000)], as_of=TODAY)

        self.assertIsNone(estimate.amount)
        self.assertEqual(estimate.reason, "no_spending_in_window")

    def test_창_안의_금액이_전부_0이면_모름이다(self) -> None:
        estimate = estimate_monthly_spending([_tx(date(2026, 8, 20), 0)], as_of=TODAY)

        self.assertIsNone(estimate.amount)
        self.assertEqual(estimate.reason, "no_spending_in_window")

    def test_날짜를_못_읽는_행은_건너뛰고_센다(self) -> None:
        txs = [
            RecentTransaction(transaction_date="", amount=10_000),
            RecentTransaction(transaction_date="2026-08-20", amount=10_000),  # 형식 불일치
            _tx(date(2026, 8, 19), 5_000),
        ]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertEqual(estimate.amount, 5_000.0)
        self.assertEqual(estimate.invalid_rows, 2)

    def test_전부_읽을_수_없으면_모름이고_이유가_다르다(self) -> None:
        estimate = estimate_monthly_spending(
            [RecentTransaction(transaction_date="x", amount=1)], as_of=TODAY
        )

        self.assertIsNone(estimate.amount)
        self.assertEqual(estimate.reason, "unparseable")


class TruncationTest(unittest.TestCase):
    """Spring 은 최근 50건만 보낸다. 소비가 잦으면 30일이 잘려 과소 추정된다."""

    def test_상한에_걸리고_가장_오래된_거래가_창_안이면_잘린_것이다(self) -> None:
        # 50건이 전부 최근 10일 안에 있다 -> 그 이전 20일은 보이지 않는다.
        txs = [_tx(date(2026, 8, 21 - (i % 10)), 1_000) for i in range(FETCH_CAP)]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertTrue(estimate.truncated)
        self.assertEqual(estimate.amount, 50_000.0)

    def test_상한에_걸려도_창_밖까지_덮었으면_잘린_것이_아니다(self) -> None:
        txs = [_tx(date(2026, 8, 20), 1_000) for _ in range(FETCH_CAP - 1)]
        txs.append(_tx(date(2026, 6, 1), 1_000))  # 창 밖까지 도달

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertFalse(estimate.truncated)

    def test_상한_미만이면_잘린_것이_아니다(self) -> None:
        txs = [_tx(date(2026, 8, 20), 1_000) for _ in range(FETCH_CAP - 1)]

        estimate = estimate_monthly_spending(txs, as_of=TODAY)

        self.assertFalse(estimate.truncated)


class SourceGuardTest(unittest.TestCase):
    def test_월_지출을_상품_가격_이력으로_계산하지_않는다(self) -> None:
        """옛 계산식 `avg_price x min(count, 30)` 의 재등장을 막는다.

        크롤링한 핫딜 가격으로 사용자의 소비를 추정하면, 같은 상품을 보는 모든
        사용자가 같은 월 지출을 갖게 된다.
        """
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        for relative in ("xai/analyzer.py", "finance_engine/inference.py"):
            source = (root / relative).read_text(encoding="utf-8")
            # assertNotIn 은 실패 시 소스 전체를 메시지에 싣기 때문에 쓰지 않는다.
            for fingerprint in ("min(count, 30", "_monthly_spending_estimate"):
                self.assertFalse(
                    fingerprint in source,
                    f"{relative} 에 옛 월 지출 계산식({fingerprint!r})이 남아 있습니다",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
