from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from domain.consumption.schemas import ChatRequest, JustificationDbRequest
from domain.consumption.service import ReportService
from domain.chat.chat_agent import ChatAgent

router = APIRouter()
service = ReportService()
chat_agent = ChatAgent()

@router.post("")
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


@router.post("/evaluate-db")
def evaluate_justification_from_db(req: JustificationDbRequest) -> dict:
    try:
        context, history = service.build_justification_context_from_db(
            user_id=req.user_id,
            report_month=req.target_month,
        )
        return chat_agent.evaluate_justification(req.message, context, history)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
