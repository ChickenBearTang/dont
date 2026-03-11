from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from consumption_poc.config import FRONTEND_DIR
from consumption_poc.service import ReportService
from consumption_poc.chat_agent import ChatAgent


app = FastAPI(title="AI Consumption Report POC")
service = ReportService()
chat_agent = ChatAgent()
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

class ChatRequest(BaseModel):
    user_name: str
    month: str
    message: str
    history: list[dict[str, str]] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/v1/users")
def list_users() -> dict[str, list[dict[str, str]]]:
    return {"users": service.list_users()}


@app.post("/api/v1/reports/regenerate")
def regenerate_reports() -> dict[str, object]:
    generated_files = service.regenerate()
    return {"status": "ok", "generated_files": generated_files}


@app.post("/api/v1/chat")
def handle_chat(req: ChatRequest) -> dict:
    try:
        profile = service._resolve_profile(user_name=req.user_name)
        bundle = service.build_mock_statistics(month=req.month, user_name=req.user_name)
        
        context = {
            "monthly_summary": bundle.get("period_summary", {}),
            "categories": bundle.get("category_breakdown", []),
        }

        result = chat_agent.evaluate_justification(req.message, context, req.history)
        
        if result.get("is_valid"):
            service.add_justification(profile.user_id, req.month, {
                "message": req.message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response": result["response"]
            })
            
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/consumption-report")
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


@app.get("/api/v1/mock-consumption-stats")
def get_mock_consumption_stats(
    month: str = Query(...),
    user_id: str | None = Query(default=None),
    user_name: str | None = Query(default=None),
) -> dict:
    try:
        return service.build_mock_statistics(month=month, user_id=user_id, user_name=user_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
