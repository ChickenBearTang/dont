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


class PurchaseIntentionRequest(BaseModel):
    user_name: str
    item_text: str
    item_link: str
    user_reason: str


class TTSRequest(BaseModel):
    text: str
