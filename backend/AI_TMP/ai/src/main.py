from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
AI_DIR = Path(__file__).resolve().parents[1]
AI_TMP_DIR = Path(__file__).resolve().parents[2]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

if str(AI_TMP_DIR) not in sys.path:
    sys.path.insert(0, str(AI_TMP_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_DIR

from api.v1.routers import consumption, xai_feedback, xai_lab, xai_purchase
from domain.xai_lab.service import lab_enabled

app = FastAPI(title="AI Consumption Report POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

app.include_router(consumption.router, prefix="/api/v1")
app.include_router(xai_purchase.router, prefix="/api/v1/xai/purchase-evaluations")
app.include_router(xai_feedback.router, prefix="/api/v1/xai/purchase-evaluations")
app.include_router(xai_lab.router, prefix="/api/v1/xai-lab")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/xai-lab")
def xai_lab_page() -> FileResponse:
    """모델 검증용 화면. AI_XAI_LAB_ENABLED=1 일 때만 열린다."""
    if not lab_enabled():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(FRONTEND_DIR / "xai-lab.html")
