from __future__ import annotations

from typing import Protocol

from .schemas import PurchaseFeedbackRequest, PurchaseFeedbackResponse
from .store import JsonlFeedbackStore


class EvaluationLookup(Protocol):
    def purchase_request_id_for(self, request_id: str) -> int | None:
        """우리가 만든 평가면 그 평가의 purchaseRequestId, 모르는 평가면 None."""


class EvaluationNotFound(Exception):
    """우리가 만든 적 없는 평가 id 에 대한 반응. 임의 id 로 데이터가 오염되는 것을 막는다."""

    def __init__(self, request_id: str) -> None:
        super().__init__(f"unknown evaluation: {request_id}")
        self.request_id = request_id


class PurchaseRequestMismatch(Exception):
    def __init__(self, request_id: str, expected: int, got: int) -> None:
        super().__init__(f"evaluation {request_id} belongs to purchase request {expected}, not {got}")
        self.request_id, self.expected, self.got = request_id, expected, got


def submit_feedback(
    request_id: str,
    body: PurchaseFeedbackRequest,
    *,
    evaluations: EvaluationLookup,
    store: JsonlFeedbackStore,
) -> PurchaseFeedbackResponse:
    expected = evaluations.purchase_request_id_for(request_id)
    if expected is None:
        raise EvaluationNotFound(request_id)
    if expected != body.purchase_request_id:
        raise PurchaseRequestMismatch(request_id, expected, body.purchase_request_id)
    stored = store.save(request_id, body)
    return PurchaseFeedbackResponse(
        requestId=request_id,
        purchaseRequestId=body.purchase_request_id,
        aspect=body.aspect,
        verdict=body.verdict,
        status=stored.status,
        feedbackId=stored.feedback_id,
    )
