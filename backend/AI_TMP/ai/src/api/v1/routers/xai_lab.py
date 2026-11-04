from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from domain.xai_lab import service

# 모델 내부를 보여주는 화면이라 기본은 꺼져 있다. 요청 때마다 환경변수를 확인한다.


def _require_lab() -> None:
    if not service.lab_enabled():
        raise HTTPException(status_code=404, detail="Not Found")


router = APIRouter(dependencies=[Depends(_require_lab)])


class InspectRequest(BaseModel):
    price: float = Field(gt=0, description="상품 가격(원)")
    current_balance: float = Field(ge=0)
    emergency_fund_balance: float = Field(ge=0)
    savebox_balance: float = Field(ge=0)
    expected_card_payment_amount: float = Field(ge=0)
    days_until_card_due: float = Field(ge=0, le=31)
    monthly_spending_30d: float = Field(ge=0)
    # 5·3·2 예산 판단용. 비우면 운영에서 앞단이 안 보낸 경우와 같이 '판단 불가'가 된다.
    monthly_income: float | None = Field(default=None, gt=0, description="월 소득(원)")
    fixed_expense: float | None = Field(default=None, ge=0, description="월 고정지출(비상금 적립 포함, 원)")


@router.get("/overview")
def overview() -> dict[str, Any]:
    return service.build_overview()


@router.get("/validation")
def validation() -> dict[str, Any]:
    return service.build_validation()


@router.get("/distributions")
def distributions() -> dict[str, Any]:
    return service.build_distributions()


@router.get("/evaluation")
def evaluation() -> dict[str, Any]:
    return service.load_evaluation_snapshot()


@router.post("/inspect")
def inspect(req: InspectRequest) -> dict[str, Any]:
    profile = req.model_dump(exclude={"price", "monthly_income", "fixed_expense"})
    try:
        return service.inspect_finance(price=req.price, profile=profile)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/simulate")
def simulate(req: InspectRequest) -> dict[str, Any]:
    """운영 판단 경로로 모의 평가 (감사 로그에 남지 않는다)."""
    from ai.xai.input_contract import InputContractViolation

    try:
        return service.simulate_purchase(req.model_dump())
    except InputContractViolation as exc:
        raise HTTPException(status_code=422, detail=exc.to_dict()) from exc
