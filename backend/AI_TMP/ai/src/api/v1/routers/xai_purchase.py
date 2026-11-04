from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai.xai.input_contract import InputContractViolation
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
    except InputContractViolation as exc:
        # 앞단이 보낸 데이터가 계약을 어겼다. 원인을 필드 단위로 돌려줘서
        # 앞단 개발자가 로그를 뒤지지 않고도 고칠 수 있게 한다.
        raise HTTPException(status_code=422, detail=exc.to_dict()) from exc
    except Exception as exc:  # pragma: no cover - defensive error boundary
        raise HTTPException(status_code=400, detail=str(exc)) from exc
