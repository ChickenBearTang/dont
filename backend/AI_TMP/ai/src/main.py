from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_DIR

from api.v1.routers import consumption, chat, strict_sec

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
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(strict_sec.router, prefix="/api/v1/strict-secretary")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
