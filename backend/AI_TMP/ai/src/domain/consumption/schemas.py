from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    name: str
    age: int
    job: str
    monthly_income: int
    pay_day: int
    residence_type: str
    main_bank: str
    main_card_type: str


@dataclass(frozen=True)
class CardTransaction:
    transaction_id: str
    user_id: str
    approved_at: datetime
    merchant_name: str
    amount: int
    category: str
    subcategory: str
    payment_method: str
    status: str
    is_recurring: bool

    @property
    def month(self) -> str:
        return self.approved_at.strftime("%Y-%m")


@dataclass(frozen=True)
class AccountTransaction:
    transaction_id: str
    user_id: str
    transacted_at: datetime
    transaction_type: str
    counterparty: str
    amount: int
    category: str
    subcategory: str
    balance_after: int

    @property
    def month(self) -> str:
        return self.transacted_at.strftime("%Y-%m")


class ChatRequest(BaseModel):
    user_name: str
    month: str
    message: str
    history: list[dict[str, str]] = []


class MonthlyReportDbRequest(BaseModel):
    user_id: int
    report_month: str


class JustificationDbRequest(BaseModel):
    user_id: int
    target_month: str
    message: str


class DateRangeAnalysisRequest(BaseModel):
    user_id: int
    start_date: str
    end_date: str


class CardRecommendationDbRequest(BaseModel):
    user_id: int
    month: str


class StrictSecretaryDbRequest(BaseModel):
    user_id: int
    item_text: str
    item_link: str
    user_reason: str


class PurchaseIntentionRequest(BaseModel):
    user_profile: UserProfileBase
    item_text: str
    item_link: str
    user_reason: str
    recent_transactions: list[CardTransactionBase] = []
    ai_report_context: str | None = None


class TTSRequest(BaseModel):
    text: str


class UserProfileBase(BaseModel):
    user_id: str
    name: str
    monthly_income: int


class CardTransactionBase(BaseModel):
    transaction_date: str  # YYYYMMDD or YYYY-MM-DD
    transaction_time: str
    merchant_name: str
    category_name: str
    transaction_amount: int
    transaction_type: str | None = None
    approval_no: str | None = None
    description: str | None = None


class AccountTransactionBase(BaseModel):
    transaction_date: str
    transaction_time: str
    transaction_type: str  # 1: 입금, 2: 출금
    transaction_type_name: str | None = None
    transaction_amount: int
    after_balance: int
    transaction_summary: str | None = None
    transaction_memo: str | None = None


class ConsumptionAnalysisRequest(BaseModel):
    user_profile: UserProfileBase
    card_transactions: list[CardTransactionBase]
    account_transactions: list[AccountTransactionBase]
    start_date: str
    end_date: str
    include_ai: bool = True
