from __future__ import annotations

from datetime import datetime, timezone, date, timedelta

from domain.consumption.ai_insights import generate_ai_analysis
from domain.consumption.anomaly import detect_anomalies
from domain.consumption.db import (
    build_date_range,
    fetch_account_transactions,
    fetch_card_transactions,
    fetch_card_transactions_between,
    fetch_justification_history,
    fetch_user_profile,
    fetch_valid_justifications,
    get_connection,
)
from config import (
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
from utils.loader import load_account_transactions, load_card_transactions, load_user_profiles
from domain.consumption.reporting import (
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
from utils.writers import write_csv, write_json
import json


class ReportService:
    def __init__(self) -> None:
        try:
            self.profiles = load_user_profiles(USER_PROFILE_PATH)
        except Exception:
            self.profiles = []

        self._profiles_by_id = {profile.user_id: profile for profile in self.profiles}
        self._profiles_by_name = {
            profile.name.lower(): profile for profile in self.profiles
        }

        try:
            self.card_transactions = load_card_transactions(CARD_TRANSACTIONS_PATH)
        except Exception:
            self.card_transactions = []

        try:
            self.account_transactions = load_account_transactions(ACCOUNT_TRANSACTIONS_PATH)
        except Exception:
            self.account_transactions = []

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

    def _build_report_bundle(
        self,
        profile,
        cards,
        accounts,
        start_date: str,
        end_date: str,
        include_ai: bool,
        justifications: list[dict] | None = None,
    ) -> dict:
        if not cards:
            raise ValueError("No card transactions found for the requested period.")

        monthly = build_monthly_summary(cards, profile.monthly_income)
        categories = build_category_summary(cards)
        time_patterns = build_time_summary(cards)
        cashflow = build_cashflow_summary(accounts)
        anomalies = detect_anomalies(cards)
        overview = build_overview(profile, cards, monthly)
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
            "justifications": justifications or [],
        }
        ai_analysis, llm_status = generate_ai_analysis(
            llm_payload, fallback_analysis, include_ai=include_ai
        )

        return {
            "meta": {
                "user_id": profile.user_id,
                "user_name": profile.name,
                "period": {"start": start_date, "end": end_date},
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

    def build_report_from_db(self, user_id: int, report_month: str, include_ai: bool = True) -> dict:
        from domain.consumption.schemas import (
            AccountTransaction as InternalAccount,
            CardTransaction as InternalCard,
            UserProfile as InternalProfile,
        )

        with get_connection() as connection:
            db_profile = fetch_user_profile(connection, user_id, report_month)
            card_rows = fetch_card_transactions(connection, user_id, report_month)
            account_rows = fetch_account_transactions(connection, user_id, report_month)
            valid_justifications = fetch_valid_justifications(connection, user_id, report_month)

        profile = InternalProfile(
            user_id=db_profile.user_id,
            name=db_profile.name,
            age=30,
            job="Unknown",
            monthly_income=db_profile.monthly_income,
            pay_day=25,
            residence_type="Unknown",
            main_bank="Unknown",
            main_card_type="Unknown",
        )
        cards = [InternalCard(**row) for row in card_rows]
        accounts = [InternalAccount(**row) for row in account_rows]

        return self._build_report_bundle(
            profile=profile,
            cards=cards,
            accounts=accounts,
            start_date=report_month,
            end_date=report_month,
            include_ai=include_ai,
            justifications=valid_justifications,
        )

    def build_report_from_db_range(
        self, user_id: int, start_date: str, end_date: str, include_ai: bool = True
    ) -> dict:
        from domain.consumption.schemas import (
            AccountTransaction as InternalAccount,
            CardTransaction as InternalCard,
            UserProfile as InternalProfile,
        )

        with get_connection() as connection:
            db_profile, card_rows, account_rows = build_date_range(
                connection, user_id, start_date, end_date
            )

        profile = InternalProfile(
            user_id=db_profile.user_id,
            name=db_profile.name,
            age=30,
            job="Unknown",
            monthly_income=db_profile.monthly_income,
            pay_day=25,
            residence_type="Unknown",
            main_bank="Unknown",
            main_card_type="Unknown",
        )
        cards = [InternalCard(**row) for row in card_rows]
        accounts = [InternalAccount(**row) for row in account_rows]

        return self._build_report_bundle(
            profile=profile,
            cards=cards,
            accounts=accounts,
            start_date=start_date,
            end_date=end_date,
            include_ai=include_ai,
            justifications=[],
        )

    def get_card_recommendation_from_db(self, user_id: int, month: str) -> dict:
        with get_connection() as connection:
            db_profile = fetch_user_profile(connection, user_id, month)
            card_rows = fetch_card_transactions(connection, user_id, month)

        if not card_rows:
            return {"error": "해당 월에 카드 결제 내역이 없습니다."}

        raw_data = [
            {
                "storeName": row["merchant_name"],
                "amount": row["amount"],
                "category": row["category"],
                "subcategory": row["subcategory"],
            }
            for row in card_rows
        ]

        from ai.consumption_poc.recommendation import AIConsumptionEngine
        from config import RAW_DATA_DIR

        with open(RAW_DATA_DIR / "persons.json", "r", encoding="utf-8") as f:
            personas = json.load(f)
        with open(RAW_DATA_DIR / "cards.json", "r", encoding="utf-8") as f:
            cards_data = json.load(f)

        engine = AIConsumptionEngine(personas, cards_data)
        result = engine.run(raw_data)
        if result.get("user_persona") is None:
            result["user_persona"] = {
                "type_id": "UNKNOWN",
                "name": f"{db_profile.name}님의 소비 유형",
                "nickname": f"{db_profile.name}님의 소비 유형",
                "description": "분석할 소비 유형 데이터가 충분하지 않습니다.",
                "total_amount": 0,
                "count": 0,
                "score": 0,
            }
        return result

    def build_strict_secretary_context_from_db(self, user_id: int) -> dict:
        from domain.consumption.schemas import CardTransaction as InternalCard

        today = date.today()
        two_months_ago = today.replace(day=1)
        if two_months_ago.month <= 2:
            two_months_ago = two_months_ago.replace(
                year=two_months_ago.year - 1, month=two_months_ago.month + 10
            )
        else:
            two_months_ago = two_months_ago.replace(month=two_months_ago.month - 2)

        current_month = today.strftime("%Y-%m")
        with get_connection() as connection:
            db_profile = fetch_user_profile(connection, user_id, current_month)
            recent_card_rows = fetch_card_transactions_between(
                connection, user_id, two_months_ago, today + timedelta(days=1)
            )

        recent_transactions = [InternalCard(**row) for row in recent_card_rows]
        report_context = self.build_report_from_db(
            user_id=user_id, report_month=current_month, include_ai=False
        )

        return {
            "profile": {
                "user_id": db_profile.user_id,
                "name": db_profile.name,
                "monthly_income": db_profile.monthly_income,
            },
            "recent_transactions": [
                {
                    "approved_at": tx.approved_at.isoformat(),
                    "merchant_name": tx.merchant_name,
                    "amount": tx.amount,
                    "category": tx.category,
                    "subcategory": tx.subcategory,
                }
                for tx in recent_transactions
            ],
            "ai_report": report_context,
            "explain_logs": [],
        }

    def build_justification_context_from_db(self, user_id: int, report_month: str) -> tuple[dict, list[dict[str, str]]]:
        report = self.build_report_from_db(user_id=user_id, report_month=report_month, include_ai=False)
        context = {
            "overview": report.get("overview", {}),
            "monthly": report.get("monthly", []),
            "categories": report.get("categories", {}),
            "anomalies": report.get("anomalies", []),
            "existing_ai_analysis": report.get("ai_analysis", {}),
        }

        with get_connection() as connection:
            history = fetch_justification_history(connection, user_id, report_month)

        return context, history

    def build_report_from_data(self, request: ConsumptionAnalysisRequest) -> dict:
        from domain.consumption.schemas import (
            UserProfile as InternalProfile,
            CardTransaction as InternalCard,
            AccountTransaction as InternalAccount,
        )

        profile = InternalProfile(
            user_id=request.user_profile.user_id,
            name=request.user_profile.name,
            age=30,  # Default
            job="Unknown",  # Default
            monthly_income=request.user_profile.monthly_income,
            pay_day=25,  # Default
            residence_type="Unknown",
            main_bank="Unknown",
            main_card_type="Unknown",
        )

        cards: list[InternalCard] = []
        for tx in request.card_transactions:
            try:
                dt_str = tx.transaction_date.replace("-", "")
                t_str = tx.transaction_time.ljust(6, "0")[:6]
                dt = datetime.strptime(dt_str + t_str, "%Y%m%d%H%M%S")
            except Exception:
                dt = datetime.now()

            cards.append(
                InternalCard(
                    transaction_id=tx.approval_no or "0",
                    user_id=request.user_profile.user_id,
                    approved_at=dt,
                    merchant_name=tx.merchant_name,
                    amount=tx.transaction_amount,
                    category=tx.category_name,
                    subcategory=tx.description or tx.category_name,
                    payment_method="card",
                    status="approved",
                    is_recurring=False,
                )
            )

        accounts: list[InternalAccount] = []
        for tx in request.account_transactions:
            try:
                dt_str = tx.transaction_date.replace("-", "")
                t_str = tx.transaction_time.ljust(6, "0")[:6]
                dt = datetime.strptime(dt_str + t_str, "%Y%m%d%H%M%S")
            except Exception:
                dt = datetime.now()

            accounts.append(
                InternalAccount(
                    transaction_id="0",
                    user_id=request.user_profile.user_id,
                    transacted_at=dt,
                    transaction_type="in" if tx.transaction_type == "1" else "out",
                    counterparty=tx.transaction_summary or "Unknown",
                    amount=tx.transaction_amount,
                    category="general",
                    subcategory=tx.transaction_memo or "general",
                    balance_after=tx.after_balance.to_integral_value() if hasattr(tx.after_balance, "to_integral_value") else int(tx.after_balance),
                )
            )

        justifications = self.load_justifications(profile.user_id, request.start_date)
        return self._build_report_bundle(
            profile=profile,
            cards=cards,
            accounts=accounts,
            start_date=request.start_date,
            end_date=request.end_date,
            include_ai=request.include_ai,
            justifications=justifications,
        )

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
