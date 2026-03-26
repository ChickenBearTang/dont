from __future__ import annotations

from fastapi import APIRouter, HTTPException

from domain.xai_purchase.schemas import (
    PurchaseXaiEvaluationRequest,
    PurchaseXaiEvaluationResponse,
)
from domain.xai_purchase.service import evaluate_pr_purchase_xai

router = APIRouter()


@router.post("", response_model=PurchaseXaiEvaluationResponse)
def handle_purchase_xai(
    req: PurchaseXaiEvaluationRequest,
) -> PurchaseXaiEvaluationResponse:
    try:
        return evaluate_pr_purchase_xai(req)
    except Exception as exc:  # pragma: no cover - defensive error boundary
        raise HTTPException(status_code=400, detail=str(exc)) from exc
