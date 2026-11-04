from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from domain.xai_feedback.schemas import PurchaseFeedbackRequest, PurchaseFeedbackResponse
from domain.xai_feedback.service import EvaluationNotFound, PurchaseRequestMismatch, submit_feedback
from domain.xai_feedback.store import JsonlFeedbackStore
from domain.xai_purchase import service as purchase_service

router = APIRouter()

_STORE = JsonlFeedbackStore()


@router.post("/{request_id}/feedback", response_model=PurchaseFeedbackResponse)
def handle_purchase_feedback(
    body: PurchaseFeedbackRequest,
    request_id: str = Path(min_length=1, max_length=128),
) -> PurchaseFeedbackResponse:
    """구매 판단에 대한 사용자 반응(좋았다/별로였다)을 기록한다.

    같은 평가·같은 대상(aspect)에 같은 값을 다시 보내면 duplicate, 값을 바꿔 보내면 changed
    (마지막 값이 유효). 우리가 평가한 적 없는 requestId 는 404, purchaseRequestId 가 그 평가와
    다르면 422 다.
    """
    try:
        return submit_feedback(
            request_id,
            body,
            evaluations=purchase_service.current_audit_store(),
            store=_STORE,
        )
    except EvaluationNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVALUATION_NOT_FOUND", "requestId": exc.request_id},
        ) from exc
    except PurchaseRequestMismatch as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "PURCHASE_REQUEST_MISMATCH",
                "requestId": exc.request_id,
                "expectedPurchaseRequestId": exc.expected,
                "gotPurchaseRequestId": exc.got,
            },
        ) from exc
