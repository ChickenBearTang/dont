from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from domain.consumption.schemas import PurchaseIntentionRequest, TTSRequest
from config import DATA_DIR
from domain.strict_secretary.models import PurchaseRequest
from domain.strict_secretary.service import evaluate_purchase_intention
from domain.strict_secretary.voice import generate_tts_audio
from domain.consumption.service import ReportService

router = APIRouter()
service = ReportService()

@router.post("")
def handle_strict_secretary(req: PurchaseIntentionRequest) -> dict:
    try:
        result = evaluate_purchase_intention(req)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tts")
def handle_tts(req: TTSRequest):
    audio_bytes = generate_tts_audio(req.text)
    if audio_bytes is None:
        raise HTTPException(status_code=500, detail="TTS 생성 실패 (API 키를 확인하세요)")
    return Response(content=audio_bytes, media_type="audio/mpeg")
