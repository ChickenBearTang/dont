"""구매 판단에 대한 사용자 반응(좋았다/별로였다) 수집 계약.

가격 모델에는 '좋은 가격'의 정답이 없다. 이 반응이 쌓이면 그것이 정답 후보가 된다.
지금은 수집 계약과 저장만 만든다. 이 데이터로 모델을 학습하거나 선택하는 일은 하지 않는다.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackAspect(str, Enum):
    """무엇에 대한 반응인가. 섞어서 집계하면 라벨의 뜻이 흐려지므로 반드시 구분한다."""

    PRICE = "price"  # 이 가격이 좋았다/별로였다  -> 가격 모델의 정답 후보
    DECISION = "decision"  # 이 구매 판단(바로 구매/관망/비추천)이 맞았다/틀렸다
    EXPLANATION = "explanation"  # 근거/설명이 납득됐다/안 됐다


class FeedbackVerdict(str, Enum):
    GOOD = "good"
    BAD = "bad"


class FeedbackAction(str, Enum):
    """사용자가 실제로 어떻게 했는가. '좋았다'의 뜻이 구매 여부에 따라 달라진다."""

    PURCHASED = "purchased"
    NOT_PURCHASED = "not_purchased"
    UNKNOWN = "unknown"


class FeedbackReason(str, Enum):
    PRICE_TOO_HIGH = "PRICE_TOO_HIGH"
    PRICE_FAIR = "PRICE_FAIR"
    CHEAPER_ELSEWHERE = "CHEAPER_ELSEWHERE"
    BUDGET_TOO_TIGHT = "BUDGET_TOO_TIGHT"
    TOO_CAUTIOUS = "TOO_CAUTIOUS"
    TOO_PERMISSIVE = "TOO_PERMISSIVE"
    WRONG_PRODUCT = "WRONG_PRODUCT"
    OTHER = "OTHER"


MAX_REASONS = 5
MAX_COMMENT_LENGTH = 300


class PurchaseFeedbackRequest(BaseModel):
    """요청 본문. 평가 requestId 는 경로(/{requestId}/feedback)로 받는다."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    purchase_request_id: int = Field(alias="purchaseRequestId", ge=0)
    aspect: FeedbackAspect
    verdict: FeedbackVerdict
    action: FeedbackAction = FeedbackAction.UNKNOWN
    reasons: list[FeedbackReason] = Field(default_factory=list, max_length=MAX_REASONS)
    comment: str | None = Field(default=None, max_length=MAX_COMMENT_LENGTH)
    client_submitted_at: datetime | None = Field(default=None, alias="clientSubmittedAt")

    @field_validator("reasons")
    @classmethod
    def _unique_reasons(cls, value: list[FeedbackReason]) -> list[FeedbackReason]:
        return list(dict.fromkeys(value))  # 중복 제거, 순서 유지

    @field_validator("comment")
    @classmethod
    def _strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class FeedbackStatus(str, Enum):
    RECORDED = "recorded"  # 새로 기록
    DUPLICATE = "duplicate"  # 같은 내용이 이미 있음 (재전송 안전)
    CHANGED = "changed"  # 같은 평가/대상에 대해 의견을 바꿈. 마지막 값이 유효


class PurchaseFeedbackResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(alias="requestId")
    purchase_request_id: int = Field(alias="purchaseRequestId")
    aspect: FeedbackAspect
    verdict: FeedbackVerdict
    status: FeedbackStatus
    feedback_id: str = Field(alias="feedbackId")
