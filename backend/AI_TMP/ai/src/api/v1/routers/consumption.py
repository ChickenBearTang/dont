import logging

from fastapi import APIRouter, HTTPException, Query
from domain.consumption.service import ReportService
from domain.consumption.schemas import (
    CardRecommendationDbRequest,
    ConsumptionAnalysisRequest,
    DateRangeAnalysisRequest,
    MonthlyReportDbRequest,
)

router = APIRouter()
service = ReportService()
logger = logging.getLogger(__name__)

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


@router.post("/consumption/monthly-report")
def analyze_monthly_report(request: MonthlyReportDbRequest) -> dict:
    try:
        report = service.build_report_from_db(
            user_id=request.user_id,
            report_month=request.report_month,
            include_ai=True,
        )
        return {
            "analysis_payload": report.get("ai_analysis", {}),
            "llm_status": report.get("meta", {}).get("llm_status", "skipped"),
            "report_context": report,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/consumption/date-range-report")
def analyze_date_range_report(request: DateRangeAnalysisRequest) -> dict:
    try:
        logger.warning(
            "[AI] date-range-report request: user_id=%s, start_date=%s, end_date=%s",
            request.user_id,
            request.start_date,
            request.end_date,
        )
        response = service.build_report_from_db_range(
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_ai=True,
        )
        logger.warning(
            "[AI] date-range-report success: user_id=%s, start_date=%s, end_date=%s",
            request.user_id,
            request.start_date,
            request.end_date,
        )
        return response
    except Exception as exc:
        logger.exception(
            "[AI] date-range-report failed: user_id=%s, start_date=%s, end_date=%s",
            request.user_id,
            request.start_date,
            request.end_date,
        )
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/recommendation/db")
def recommend_card_from_db(request: CardRecommendationDbRequest) -> dict:
    try:
        logger.warning(
            "[AI] recommendation/db request: user_id=%s, month=%s",
            request.user_id,
            request.month,
        )
        response = service.get_card_recommendation_from_db(
            user_id=request.user_id,
            month=request.month,
        )
        logger.warning(
            "[AI] recommendation/db success: user_id=%s, month=%s",
            request.user_id,
            request.month,
        )
        return response
    except Exception as exc:
        logger.exception(
            "[AI] recommendation/db failed: user_id=%s, month=%s",
            request.user_id,
            request.month,
        )
        raise HTTPException(status_code=400, detail=str(exc))
