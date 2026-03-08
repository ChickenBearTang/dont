from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median

from consumption_poc.models import AccountTransaction, CardTransaction, UserProfile


WEEKDAY_ORDER = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
TIME_BAND_ORDER = ["morning", "lunch", "evening", "late_night"]


def _round_one(value: float) -> float:
    return round(value, 1)


def month_in_range(month: str, start: str, end: str) -> bool:
    return start <= month <= end


def filter_card_transactions(
    transactions: list[CardTransaction], user_id: str, start: str, end: str
) -> list[CardTransaction]:
    return [
        tx
        for tx in transactions
        if tx.user_id == user_id and tx.status == "approved" and month_in_range(tx.month, start, end)
    ]


def filter_account_transactions(
    transactions: list[AccountTransaction], user_id: str, start: str, end: str
) -> list[AccountTransaction]:
    return [tx for tx in transactions if tx.user_id == user_id and month_in_range(tx.month, start, end)]


def get_time_band(hour: int) -> str:
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 15:
        return "lunch"
    if 15 <= hour < 22:
        return "evening"
    return "late_night"


def build_monthly_summary(cards: list[CardTransaction], monthly_income: int) -> list[dict]:
    monthly_totals: dict[str, dict[str, float | int | str | None]] = defaultdict(
        lambda: {"total": 0, "count": 0, "categories": defaultdict(int)}
    )
    for tx in cards:
        bucket = monthly_totals[tx.month]
        bucket["total"] += tx.amount
        bucket["count"] += 1
        bucket["categories"][tx.category] += tx.amount

    rows: list[dict] = []
    previous_total: int | None = None
    for month in sorted(monthly_totals):
        total = int(monthly_totals[month]["total"])
        count = int(monthly_totals[month]["count"])
        categories = monthly_totals[month]["categories"]
        top_category, top_category_amount = max(categories.items(), key=lambda item: item[1])
        mom_change = None if previous_total is None else _round_one(((total - previous_total) / previous_total) * 100)
        rows.append(
            {
                "month": month,
                "total_card_spend": total,
                "transaction_count": count,
                "avg_transaction_amount": round(total / count, 2),
                "monthly_income": monthly_income,
                "card_spend_ratio_percent": _round_one((total / monthly_income) * 100),
                "top_category": top_category,
                "top_category_amount": top_category_amount,
                "mom_change_percent": mom_change,
            }
        )
        previous_total = total
    return rows


def build_category_summary(cards: list[CardTransaction]) -> dict:
    total_amount = sum(tx.amount for tx in cards)
    by_month: list[dict] = []
    month_category_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    subcategory_totals: Counter[str] = Counter()
    category_totals: Counter[str] = Counter()
    for tx in cards:
        month_category_totals[tx.month][tx.category] += tx.amount
        category_totals[tx.category] += tx.amount
        subcategory_totals[tx.subcategory] += tx.amount

    for month in sorted(month_category_totals):
        month_total = sum(month_category_totals[month].values())
        for category, amount in sorted(
            month_category_totals[month].items(), key=lambda item: item[1], reverse=True
        ):
            by_month.append(
                {
                    "month": month,
                    "category": category,
                    "amount": amount,
                    "share_percent": _round_one((amount / month_total) * 100),
                }
            )

    top_categories = [
        {
            "category": category,
            "amount": amount,
            "share_percent": _round_one((amount / total_amount) * 100),
        }
        for category, amount in category_totals.most_common()
    ]
    top_subcategories = [
        {
            "subcategory": subcategory,
            "amount": amount,
            "share_percent": _round_one((amount / total_amount) * 100),
        }
        for subcategory, amount in subcategory_totals.most_common()
    ]
    return {
        "by_month": by_month,
        "top_categories": top_categories,
        "top_subcategories": top_subcategories,
    }


def build_time_summary(cards: list[CardTransaction]) -> dict:
    time_band_buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total": 0})
    weekday_buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total": 0})
    total_amount = sum(tx.amount for tx in cards)

    for tx in cards:
        band = get_time_band(tx.approved_at.hour)
        time_band_buckets[band]["count"] += 1
        time_band_buckets[band]["total"] += tx.amount
        weekday = tx.approved_at.strftime("%A").lower()
        weekday_buckets[weekday]["count"] += 1
        weekday_buckets[weekday]["total"] += tx.amount

    time_bands = [
        {
            "dimension_type": "time_band",
            "dimension_key": band,
            "transaction_count": time_band_buckets[band]["count"],
            "total_amount": time_band_buckets[band]["total"],
            "share_percent": _round_one((time_band_buckets[band]["total"] / total_amount) * 100),
        }
        for band in TIME_BAND_ORDER
        if band in time_band_buckets
    ]
    weekdays = [
        {
            "dimension_type": "weekday",
            "dimension_key": weekday,
            "transaction_count": weekday_buckets[weekday]["count"],
            "total_amount": weekday_buckets[weekday]["total"],
            "share_percent": _round_one((weekday_buckets[weekday]["total"] / total_amount) * 100),
        }
        for weekday in WEEKDAY_ORDER
        if weekday in weekday_buckets
    ]
    return {"time_bands": time_bands, "weekdays": weekdays}


def build_cashflow_summary(accounts: list[AccountTransaction]) -> list[dict]:
    monthly: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "income": 0,
            "total_outflow": 0,
            "fixed_cost": 0,
            "card_bill": 0,
            "net_cashflow": 0,
            "ending_balance": 0,
        }
    )

    for tx in accounts:
        bucket = monthly[tx.month]
        if tx.transaction_type == "in":
            bucket["income"] += tx.amount
        else:
            bucket["total_outflow"] += tx.amount
        if tx.category == "fixed_cost":
            bucket["fixed_cost"] += tx.amount
        if tx.category == "card_bill":
            bucket["card_bill"] += tx.amount
        bucket["ending_balance"] = tx.balance_after

    rows: list[dict] = []
    for month in sorted(monthly):
        bucket = monthly[month]
        bucket["net_cashflow"] = bucket["income"] - bucket["total_outflow"]
        rows.append({"month": month, **bucket})
    return rows


def category_medians(cards: list[CardTransaction]) -> dict[str, float]:
    categories: dict[str, list[int]] = defaultdict(list)
    for tx in cards:
        categories[tx.category].append(tx.amount)
    return {category: float(median(amounts)) for category, amounts in categories.items()}


def build_overview(profile: UserProfile, cards: list[CardTransaction], monthly: list[dict]) -> dict:
    total = sum(tx.amount for tx in cards)
    avg_monthly = round(total / len(monthly)) if monthly else 0
    avg_transaction = round(total / len(cards)) if cards else 0
    recurring_total = sum(tx.amount for tx in cards if tx.is_recurring)
    outlier_adjusted_total = total - max((tx.amount for tx in cards), default=0)
    outlier_adjusted_monthly_avg = round(outlier_adjusted_total / len(monthly)) if monthly else 0
    return {
        "total_card_spend": total,
        "transaction_count": len(cards),
        "avg_monthly_card_spend": avg_monthly,
        "avg_transaction_amount": avg_transaction,
        "monthly_income": profile.monthly_income,
        "card_spend_to_income_ratio_percent": _round_one(
            (total / (profile.monthly_income * len(monthly))) * 100
        )
        if monthly
        else 0.0,
        "outlier_adjusted_monthly_avg": outlier_adjusted_monthly_avg,
        "recurring_spend_total": recurring_total,
        "recurring_monthly_avg": round(recurring_total / len(monthly)) if monthly else 0,
    }


def build_rule_based_insights(
    monthly: list[dict], categories: dict, time_patterns: dict, anomalies: list[dict]
) -> dict[str, list[str]]:
    top_category = categories["top_categories"][0] if categories["top_categories"] else None
    top_subcategory = categories["top_subcategories"][0] if categories["top_subcategories"] else None
    peak_month = max(monthly, key=lambda row: row["total_card_spend"]) if monthly else None
    top_time_band = max(time_patterns["time_bands"], key=lambda row: row["total_amount"]) if time_patterns["time_bands"] else None

    patterns: list[str] = []
    anomaly_explanations: list[str] = []
    solutions: list[str] = []

    if peak_month:
        patterns.append(
            f"{peak_month['month']} 소비가 {peak_month['total_card_spend']}원으로 가장 높았습니다."
        )
    if top_category:
        patterns.append(
            f"가장 큰 소비 카테고리는 {top_category['category']}이며 비중은 {top_category['share_percent']}%입니다."
        )
    if top_time_band:
        patterns.append(
            f"지출은 {top_time_band['dimension_key']} 시간대에 가장 집중됐습니다."
        )

    for anomaly in anomalies[:3]:
        anomaly_explanations.append(
            f"{anomaly['approved_at']} {anomaly['merchant_name']} {anomaly['amount']}원 거래가 {anomaly['anomaly_type']}로 분류됐습니다."
        )

    if top_subcategory and top_subcategory["subcategory"] == "luxury":
        solutions.append("럭셔리 지출은 단건 변동성이 크므로 별도 예산 한도를 두는 것이 좋습니다.")
    if any(row["category"] == "food" and row["share_percent"] >= 45 for row in categories["by_month"]):
        solutions.append("식비 비중이 높은 달은 배달과 편의점 소비를 분리해 관리하는 것이 좋습니다.")
    solutions.append("반복 결제는 고정비 목록으로 분리해 매달 자동 점검하는 것이 좋습니다.")

    return {
        "consumption_patterns": patterns,
        "anomaly_explanations": anomaly_explanations,
        "actionable_solutions": solutions,
    }
