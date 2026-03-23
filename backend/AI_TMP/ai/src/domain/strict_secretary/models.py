from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.consumption.schemas import UserProfile, CardTransaction

@dataclass
class PurchaseRequest:
    user_id: str
    item_text: str
    item_link: str
    user_reason: str

@dataclass
class SecretaryResponse:
    is_approved: bool
    fact_violence_comment: str
    reasoning: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_approved": self.is_approved,
            "fact_violence_comment": self.fact_violence_comment,
            "reasoning": self.reasoning,
        }
