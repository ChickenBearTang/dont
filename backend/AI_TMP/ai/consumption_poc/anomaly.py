from __future__ import annotations

from collections import Counter

from consumption_poc.models import CardTransaction
from consumption_poc.reporting import category_medians


def detect_anomalies(cards: list[CardTransaction]) -> list[dict]:
    if not cards:
        return []

    medians = category_medians(cards)
    merchant_counter = Counter(tx.merchant_name for tx in cards)
    anomalies: list[dict] = []

    for tx in sorted(cards, key=lambda item: item.approved_at):
        score = 0
        category_median = medians.get(tx.category, 1.0)
        ratio = tx.amount / max(category_median, 1.0)
        is_new_high_spend = merchant_counter[tx.merchant_name] == 1 and tx.amount >= 100000
        is_late_night = 0 <= tx.approved_at.hour <= 4

        if tx.amount >= 300000:
            score += 55
        if ratio >= 3:
            score += 25
        if is_late_night:
            score += 15
        if is_new_high_spend:
            score += 10

        score = min(score, 100)
        if score < 50:
            continue

        if tx.amount >= 300000 and is_late_night:
            anomaly_type = "high_amount_late_night"
            reason = "고액 결제와 심야 결제가 동시에 발생했습니다."
        elif tx.amount >= 300000:
            anomaly_type = "high_amount"
            reason = "절대 금액 기준 고액 결제입니다."
        elif is_late_night:
            anomaly_type = "late_night_spend"
            reason = "심야 시간대 소비 패턴 이탈입니다."
        else:
            anomaly_type = "spending_spike"
            reason = "동일 카테고리 중앙값 대비 과도하게 큰 결제입니다."

        anomalies.append(
            {
                "transaction_id": tx.transaction_id,
                "approved_at": tx.approved_at.isoformat(),
                "merchant_name": tx.merchant_name,
                "amount": tx.amount,
                "category": tx.category,
                "subcategory": tx.subcategory,
                "anomaly_type": anomaly_type,
                "risk_score": score,
                "reason": reason,
            }
        )

    anomalies.sort(key=lambda row: (-row["risk_score"], -row["amount"], row["approved_at"]))
    return anomalies
