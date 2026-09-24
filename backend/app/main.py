from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import reports, transactions, uploads
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PennyWise API", version="1.0.0",
              description="개인 재무 관리 AI 에이전트 — CSV/영수증 → 분류 → 분석 → 예산/절약팁")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(uploads.router)
app.include_router(transactions.router)
app.include_router(reports.router)

try:
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
except Exception:
    pass


@app.get("/health")
def health():
    return {"ok": True, "llm": settings.llm_enabled}
