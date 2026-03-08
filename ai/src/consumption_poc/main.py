from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from consumption_poc.service import ReportService


app = FastAPI(title="AI Consumption Report POC")
service = ReportService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/reports/regenerate")
def regenerate_reports() -> dict[str, object]:
    generated_files = service.regenerate()
    return {"status": "ok", "generated_files": generated_files}


@app.get("/api/v1/consumption-report")
def get_consumption_report(
    user_id: str = Query(...),
    start: str = Query(...),
    end: str = Query(...),
    include_ai: bool = Query(True),
) -> dict:
    try:
        return service.build_report(user_id=user_id, start=start, end=end, include_ai=include_ai)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
