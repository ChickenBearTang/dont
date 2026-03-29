from __future__ import annotations

from datetime import datetime, timezone

from consumption_poc.ai_insights import generate_ai_analysis
from consumption_poc.anomaly import detect_anomalies
from consumption_poc.config import (
    ACCOUNT_TRANSACTIONS_PATH,
    CARD_TRANSACTIONS_PATH,
    GENERATED_DATA_DIR,
    GENERATED_ANOMALY_PATH,
    GENERATED_CASHFLOW_PATH,
    GENERATED_CATEGORY_PATH,
    GENERATED_MONTHLY_PATH,
    GENERATED_SUMMARY_PATH,
    GENERATED_TIME_PATH,
    USER_PROFILE_PATH,
)
from consumption_poc.loader import load_account_transactions, load_card_transactions, load_user_profiles
from consumption_poc.reporting import (
    build_cashflow_summary,
    build_category_summary,
    build_mock_statistics_bundle,
    build_monthly_summary,
    build_overview,
    build_rule_based_insights,
    build_time_summary,
    filter_account_transactions,
    filter_card_transactions,
)
from consumption_poc.writers import write_csv, write_json
import json


class ReportService:
    def __init__(self) -> None:
        self.profiles = load_user_profiles(USER_PROFILE_PATH)
        self._profiles_by_id = {profile.user_id: profile for profile in self.profiles}
        self._profiles_by_name = {
            profile.name.lower(): profile for profile in self.profiles
        }
        self.card_transactions = load_card_transactions(CARD_TRANSACTIONS_PATH)
        self.account_transactions = load_account_transactions(ACCOUNT_TRANSACTIONS_PATH)

    def _get_justifications_path(self, user_id: str, month: str):
        return GENERATED_DATA_DIR / "users" / user_id / month / "justifications.json"

    def load_justifications(self, user_id: str, month: str) -> list[dict]:
        path = self._get_justifications_path(user_id, month)
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_justification(self, user_id: str, month: str, justification: dict) -> None:
        path = self._get_justifications_path(user_id, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        items = self.load_justifications(user_id, month)
        items.append(justification)
        write_json(path, items)

    def _resolve_period(self, transactions: list | None = None) -> tuple[str, str]:
        selected = transactions or self.card_transactions
        months = sorted({tx.month for tx in selected})
        if not months:
            raise ValueError("No card transactions found.")
        return months[0], months[-1]

    def _resolve_profile(self, user_id: str | None = None, user_name: str | None = None):
        if user_id:
            profile = self._profiles_by_id.get(user_id)
            if profile is None:
                raise ValueError(f"Unknown user_id: {user_id}")
            if user_name and profile.name.lower() != user_name.lower():
                raise ValueError(f"user_id and user_name mismatch: {user_id}, {user_name}")
            return profile

        if not user_name:
            raise ValueError("Either user_id or user_name must be provided.")

        profile = self._profiles_by_name.get(user_name.lower())
        if profile is None:
            raise ValueError(f"Unknown user_name: {user_name}")
        return profile

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

    def list_users(self) -> list[dict[str, str]]:
        return [{"user_id": p.user_id, "name": p.name} for p in self.profiles]

    def build_report(
        self,
        start: str,
        end: str,
        user_id: str | None = None,
        user_name: str | None = None,
        include_ai: bool = True,
    ) -> dict:
        profile = self._resolve_profile(user_id=user_id, user_name=user_name)

        target_user_id = profile.user_id
        cards = filter_card_transactions(self.card_transactions, target_user_id, start, end)
        accounts = filter_account_transactions(self.account_transactions, target_user_id, start, end)
        if not cards:
            raise ValueError("No card transactions found for the requested period.")

        monthly = build_monthly_summary(cards, profile.monthly_income)
        categories = build_category_summary(cards)
        time_patterns = build_time_summary(cards)
        cashflow = build_cashflow_summary(accounts)
        anomalies = detect_anomalies(cards)
        self._validate_card_bill_alignment(monthly, cashflow)

        overview = build_overview(profile, cards, monthly)
        fallback_analysis = build_rule_based_insights(monthly, categories, time_patterns, anomalies)

        justifications = self.load_justifications(profile.user_id, start)

        llm_payload = {
            "overview": overview,
            "monthly": monthly,
            "top_categories": categories["top_categories"][:5],
            "top_subcategories": categories["top_subcategories"][:5],
            "time_patterns": time_patterns,
            "cashflow": cashflow,
            "anomalies": anomalies[:5],
            "fallback_analysis": fallback_analysis,
            "justifications": justifications,
        }
        ai_analysis, llm_status = generate_ai_analysis(llm_payload, fallback_analysis, include_ai=include_ai)

        return {
            "meta": {
                "user_id": profile.user_id,
                "user_name": profile.name,
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

    def build_mock_statistics(
        self,
        month: str,
        user_id: str | None = None,
        user_name: str | None = None,
    ) -> dict:
        profile = self._resolve_profile(user_id=user_id, user_name=user_name)
        cards = filter_card_transactions(self.card_transactions, profile.user_id, "1900-01", "2900-12")
        if not cards:
            raise ValueError("No card transactions found for the requested user.")

        monthly = build_monthly_summary(cards, profile.monthly_income)
        bundle = build_mock_statistics_bundle(cards, monthly, month)
        return {
            "meta": {
                "user_id": profile.user_id,
                "user_name": profile.name,
                "selected_month": month,
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            },
            **bundle,
        }

    def get_card_recommendation(self, user_name: str, month: str) -> dict:
        profile = self._resolve_profile(user_name=user_name)
        cards = filter_card_transactions(self.card_transactions, profile.user_id, month, month)

        if not cards:
            return {"error": "해당 월에 카드 결제 내역이 없습니다."}

        raw_data = [
            {
                "storeName": tx.merchant_name,
                "amount": tx.amount,
                "category": tx.category,
                "subcategory": tx.subcategory
            } for tx in cards
        ]

        from consumption_poc.recommendation import AIConsumptionEngine
        from consumption_poc.config import RAW_DATA_DIR
        import json

        with open(RAW_DATA_DIR / "persons.json", "r", encoding="utf-8") as f:
            personas = json.load(f)
        with open(RAW_DATA_DIR / "cards.json", "r", encoding="utf-8") as f:
            cards_data = json.load(f)

        engine = AIConsumptionEngine(personas, cards_data)
        return engine.run(raw_data)

    def regenerate(self, user_id: str | None = None, user_name: str | None = None) -> list[str]:
        profile = self._resolve_profile(user_id=user_id, user_name=user_name) if (user_id or user_name) else self.profiles[0]
        target_user_id = profile.user_id
        cards = filter_card_transactions(self.card_transactions, target_user_id, "1900-01", "2900-12")
        start, end = self._resolve_period(cards)
        report = self.build_report(start=start, end=end, user_id=target_user_id, include_ai=False)
        write_csv(GENERATED_MONTHLY_PATH, report["monthly"])
        write_csv(GENERATED_CATEGORY_PATH, report["categories"]["by_month"])
        write_csv(
            GENERATED_TIME_PATH,
            report["time_patterns"]["time_bands"] + report["time_patterns"]["weekdays"],
        )
        write_csv(GENERATED_ANOMALY_PATH, report["anomalies"])
        write_csv(GENERATED_CASHFLOW_PATH, report["cashflow"])
        write_json(GENERATED_SUMMARY_PATH, report)
        generated_files = [
            GENERATED_MONTHLY_PATH.name,
            GENERATED_CATEGORY_PATH.name,
            GENERATED_TIME_PATH.name,
            GENERATED_ANOMALY_PATH.name,
            GENERATED_CASHFLOW_PATH.name,
            GENERATED_SUMMARY_PATH.name,
        ]
        generated_files.extend(self._regenerate_user_mock_outputs())
        return generated_files

    def _regenerate_user_mock_outputs(self) -> list[str]:
        generated: list[str] = []
        users_root = GENERATED_DATA_DIR / "users"
        for profile in self.profiles:
            cards = filter_card_transactions(self.card_transactions, profile.user_id, "1900-01", "2900-12")
            if not cards:
                continue
            monthly = build_monthly_summary(cards, profile.monthly_income)
            for month_row in monthly:
                month = month_row["month"]
                bundle = build_mock_statistics_bundle(cards, monthly, month)
                month_dir = users_root / profile.user_id / month
                write_json(month_dir / "period_summary.json", bundle["period_summary"])
                write_csv(month_dir / "daily_cumulative.csv", bundle["daily_cumulative"])
                write_csv(month_dir / "category_breakdown.csv", bundle["category_breakdown"])
                write_csv(month_dir / "six_month_trend.csv", bundle["six_month_trend"]["months"])
                write_json(month_dir / "six_month_summary.json", bundle["six_month_trend"])
                generated.extend(
                    [
                        f"users/{profile.user_id}/{month}/period_summary.json",
                        f"users/{profile.user_id}/{month}/daily_cumulative.csv",
                        f"users/{profile.user_id}/{month}/category_breakdown.csv",
                        f"users/{profile.user_id}/{month}/six_month_trend.csv",
                        f"users/{profile.user_id}/{month}/six_month_summary.json",
                    ]
                )
        return generated
