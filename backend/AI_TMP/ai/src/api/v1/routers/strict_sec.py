import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from domain.consumption.schemas import (
    CardTransactionBase,
    PurchaseIntentionRequest,
    StrictSecretaryDbRequest,
    TTSRequest,
    UserProfileBase,
)
from domain.strict_secretary.service import evaluate_purchase_intention
from domain.strict_secretary.voice import generate_tts_audio
from domain.consumption.service import ReportService

router = APIRouter()
service = ReportService()
logger = logging.getLogger(__name__)

@router.post("")
def handle_strict_secretary(req: PurchaseIntentionRequest) -> dict:
    try:
        logger.warning("[AI] strict-secretary request received")
        result = evaluate_purchase_intention(req)
        logger.warning("[AI] strict-secretary success")
        return result.to_dict()
    except Exception as e:
        logger.exception("[AI] strict-secretary failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/db")
def handle_strict_secretary_db(req: StrictSecretaryDbRequest) -> dict:
    try:
        logger.warning("[AI] strict-secretary/db request: user_id=%s", req.user_id)
        context = service.build_strict_secretary_context_from_db(req.user_id)
        purchase_request = PurchaseIntentionRequest(
            user_profile=UserProfileBase(**context["profile"]),
            item_text=req.item_text,
            item_link=req.item_link,
            user_reason=req.user_reason,
            recent_transactions=[
                CardTransactionBase(
                    transaction_date=row["approved_at"][:10].replace("-", ""),
                    transaction_time=row["approved_at"][11:19].replace(":", ""),
                    merchant_name=row["merchant_name"],
                    category_name=row["category"],
                    transaction_amount=row["amount"],
                )
                for row in context["recent_transactions"]
            ],
            ai_report_context=str(context["ai_report"]),
        )
        result = evaluate_purchase_intention(purchase_request)
        logger.warning("[AI] strict-secretary/db success: user_id=%s", req.user_id)
        return result.to_dict()
    except Exception as e:
        logger.exception("[AI] strict-secretary/db failed: user_id=%s", req.user_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tts")
def handle_tts(req: TTSRequest):
    audio_bytes = generate_tts_audio(req.text)
    if audio_bytes is None:
        raise HTTPException(status_code=500, detail="TTS 생성 실패 (API 키를 확인하세요)")
    return Response(content=audio_bytes, media_type="audio/mpeg")
