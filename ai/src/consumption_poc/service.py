from __future__ import annotations

from datetime import datetime, timezone

from consumption_poc.ai_insights import generate_ai_analysis
from consumption_poc.anomaly import detect_anomalies
from consumption_poc.config import (
    ACCOUNT_TRANSACTIONS_PATH,
    CARD_TRANSACTIONS_PATH,
    GENERATED_ANOMALY_PATH,
    GENERATED_CASHFLOW_PATH,
    GENERATED_CATEGORY_PATH,
    GENERATED_MONTHLY_PATH,
    GENERATED_SUMMARY_PATH,
    GENERATED_TIME_PATH,
    USER_PROFILE_PATH,
)
from consumption_poc.loader import load_account_transactions, load_card_transactions, load_user_profile
from consumption_poc.reporting import (
    build_cashflow_summary,
    build_category_summary,
    build_monthly_summary,
    build_overview,
    build_rule_based_insights,
    build_time_summary,
    filter_account_transactions,
    filter_card_transactions,
)
from consumption_poc.writers import write_csv, write_json


class ReportService:
    def __init__(self) -> None:
        self.profile = load_user_profile(USER_PROFILE_PATH)
        self.card_transactions = load_card_transactions(CARD_TRANSACTIONS_PATH)
        self.account_transactions = load_account_transactions(ACCOUNT_TRANSACTIONS_PATH)

    def _resolve_period(self) -> tuple[str, str]:
        months = sorted({tx.month for tx in self.card_transactions})
        if not months:
            raise ValueError("No card transactions found.")
        return months[0], months[-1]

    def _validate_card_bill_alignment(self, monthly: list[dict], cashflow: list[dict]) -> None:
        cashflow_by_month = {row["month"]: row for row in cashflow}
        for row in monthly:
            month = row["month"]
            expected_bill = row["total_card_spend"]
            actual_bill = cashflow_by_month.get(month, {}).get("card_bill")
            if expected_bill != actual_bill:
                raise ValueError(
                    f"Card bill mismatch for {month}: expected {expected_bill}, actual {actual_bill}"
                )

    def build_report(self, user_id: str, start: str, end: str, include_ai: bool = True) -> dict:
        if user_id != self.profile.user_id:
            raise ValueError(f"Unknown user_id: {user_id}")

        cards = filter_card_transactions(self.card_transactions, user_id, start, end)
        accounts = filter_account_transactions(self.account_transactions, user_id, start, end)
        if not cards:
            raise ValueError("No card transactions found for the requested period.")

        monthly = build_monthly_summary(cards, self.profile.monthly_income)
        categories = build_category_summary(cards)
        time_patterns = build_time_summary(cards)
        cashflow = build_cashflow_summary(accounts)
        anomalies = detect_anomalies(cards)
        self._validate_card_bill_alignment(monthly, cashflow)

        overview = build_overview(self.profile, cards, monthly)
        fallback_analysis = build_rule_based_insights(monthly, categories, time_patterns, anomalies)
        llm_payload = {
            "overview": overview,
            "monthly": monthly,
            "top_categories": categories["top_categories"][:5],
            "top_subcategories": categories["top_subcategories"][:5],
            "time_patterns": time_patterns,
            "cashflow": cashflow,
            "anomalies": anomalies[:5],
            "fallback_analysis": fallback_analysis,
        }
        ai_analysis, llm_status = generate_ai_analysis(llm_payload, fallback_analysis, include_ai=include_ai)

        return {
            "meta": {
                "user_id": user_id,
                "period": {"start": start, "end": end},
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "llm_status": llm_status,
            },
            "overview": overview,
            "monthly": monthly,
            "categories": categories,
            "time_patterns": time_patterns,
            "cashflow": cashflow,
            "anomalies": anomalies,
            "ai_analysis": ai_analysis,
        }

    def regenerate(self) -> list[str]:
        start, end = self._resolve_period()
        report = self.build_report(self.profile.user_id, start, end, include_ai=False)
        write_csv(GENERATED_MONTHLY_PATH, report["monthly"])
        write_csv(GENERATED_CATEGORY_PATH, report["categories"]["by_month"])
        write_csv(
            GENERATED_TIME_PATH,
            report["time_patterns"]["time_bands"] + report["time_patterns"]["weekdays"],
        )
        write_csv(GENERATED_ANOMALY_PATH, report["anomalies"])
        write_csv(GENERATED_CASHFLOW_PATH, report["cashflow"])
        write_json(GENERATED_SUMMARY_PATH, report)
        return [
            GENERATED_MONTHLY_PATH.name,
            GENERATED_CATEGORY_PATH.name,
            GENERATED_TIME_PATH.name,
            GENERATED_ANOMALY_PATH.name,
            GENERATED_CASHFLOW_PATH.name,
            GENERATED_SUMMARY_PATH.name,
        ]
