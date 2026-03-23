from fastapi import APIRouter, HTTPException, Query
from domain.consumption.service import ReportService
from domain.consumption.schemas import ConsumptionAnalysisRequest

router = APIRouter()
service = ReportService()

@router.get("/users")
def list_users() -> dict[str, list[dict[str, str]]]:
    return {"users": service.list_users()}

@router.post("/reports/regenerate")
def regenerate_reports() -> dict[str, object]:
    generated_files = service.regenerate()
    return {"status": "ok", "generated_files": generated_files}

@router.get("/consumption-report")
def get_consumption_report(
    user_id: str | None = Query(default=None),
    user_name: str | None = Query(default=None),
    start: str = Query(...),
    end: str = Query(...),
    include_ai: bool = Query(True),
) -> dict:
    try:
        return service.build_report(
            user_id=user_id,
            user_name=user_name,
            start=start,
            end=end,
            include_ai=include_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/mock-consumption-stats")
def get_mock_consumption_stats(
    month: str = Query(...),
    user_id: str | None = Query(default=None),
    user_name: str | None = Query(default=None),
) -> dict:
    try:
        return service.build_mock_statistics(month=month, user_id=user_id, user_name=user_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze")
def analyze_consumption(request: ConsumptionAnalysisRequest) -> dict:
    try:
        return service.build_report_from_data(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
