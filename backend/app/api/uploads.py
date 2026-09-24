"""POST /upload/csv, POST /upload/receipt — SSE 진행률 포함."""
from __future__ import annotations

import os
import uuid
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.database import get_db
from app.graph.workflow import upload_graph
from app.llm import provider as llm
from app.models import Transaction, UploadHistory
from app.schemas import ReceiptExtraction
from app.services import csv_mapper, dedup
from app.services.categorizer import classify_batch

router = APIRouter(prefix="/upload", tags=["upload"])
os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try:
            import io
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except Exception:
            continue
    else:
        return JSONResponse({"error": "CSV 파싱 실패 (인코딩 확인)"}, status_code=400)

    mapping = csv_mapper.auto_map_columns(df)
    normalized_all = csv_mapper.normalize_csv(df, mapping)

    # 원본 저장 (미리보기용)
    csv_path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex}_{file.filename or 'upload.csv'}")
    with open(csv_path, "wb") as f:
        f.write(raw)

    # LangGraph 실행 (정규화→분류→저장)
    result = upload_graph.invoke({"raw_items": [
        {"date": n["date"].isoformat(), "merchant": n["merchant"],
         "amount": n["amount"], "memo": n["memo"]} for n in normalized_all],
        "source": "csv"})
    skipped = result.get("skipped_duplicates", 0)
    saved = len(normalized_all) - skipped
    db.add(UploadHistory(kind="csv", filename=file.filename or "upload.csv",
                         total_rows=len(df), saved=saved, skipped_duplicates=skipped,
                         image_path=csv_path))
    db.commit()
    return {"filename": file.filename, "mapping": mapping.model_dump(),
            "parsed": len(df), "normalized": len(normalized_all),
            "skipped_duplicates": skipped, "saved": saved}


@router.get("/csv/progress")
async def csv_progress_demo():
    """SSE 데모: 업로드 처리 상태 실시간 스트리밍 (분석중 → 분류중 → 완료)."""
    async def gen():
        for stage in ["분석중", "분류중", "저장중", "완료"]:
            yield {"event": "progress", "data": stage}
    return EventSourceResponse(gen())


@router.post("/receipt")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    ext = os.path.splitext(file.filename or "receipt.jpg")[1] or ".jpg"
    path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(content)

    extracted = llm.extract_receipt(content)
    try:
        rec = ReceiptExtraction(**extracted)
    except Exception:
        rec = ReceiptExtraction(merchant=extracted.get("merchant", "판독실패"),
                                total_amount=float(extracted.get("total_amount", 0) or 0),
                                confidence=float(extracted.get("confidence", 0.1)),
                                raw_text=str(extracted.get("raw_text", "")))
    rdate = rec.date or date.today()
    if dedup.is_duplicate(db, rdate, rec.merchant, rec.total_amount):
        db.add(UploadHistory(kind="receipt", filename=file.filename or "receipt",
                             total_rows=1, saved=0, skipped_duplicates=1,
                             image_path=path, note=f"중복: {rec.merchant} {rec.total_amount:,.0f}원"))
        db.commit()
        return {"duplicate": True, "receipt": rec.model_dump(), "image_path": path}
    cats = classify_batch(db, [rec.merchant])
    c = cats[0]
    txn = Transaction(date=rdate, merchant=rec.merchant, amount=rec.total_amount,
                      category=c["category"], subcategory=c["subcategory"],
                      confidence=min(c["confidence"], rec.confidence or 1.0),
                      source="receipt", receipt_image_path=path,
                      memo="; ".join(i.name for i in rec.items[:5]))
    db.add(txn)
    db.add(UploadHistory(kind="receipt", filename=file.filename or "receipt",
                         total_rows=1, saved=1, skipped_duplicates=0,
                         image_path=path,
                         note=f"{rec.merchant} {rec.total_amount:,.0f}원 → {c['category']}"))
    db.commit()
    return {"duplicate": False, "receipt": rec.model_dump(),
            "transaction_id": txn.id, "category": c, "image_path": path}


@router.get("/history")
def upload_history(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(UploadHistory).order_by(UploadHistory.id.desc()).limit(limit).all()
    return [{"id": h.id, "kind": h.kind, "filename": h.filename,
             "total_rows": h.total_rows, "saved": h.saved,
             "skipped_duplicates": h.skipped_duplicates,
             "image": os.path.basename(h.image_path) if h.image_path else "",
             "note": h.note, "created_at": h.created_at.isoformat()} for h in rows]


@router.get("/preview/{history_id}")
def preview_csv(history_id: int, n: int = 10, db: Session = Depends(get_db)):
    """저장된 CSV 원본의 상위 n행 미리보기."""
    h = db.query(UploadHistory).filter_by(id=history_id, kind="csv").first()
    if not h or not h.image_path or not os.path.exists(h.image_path):
        return JSONResponse({"error": "preview not available"}, status_code=404)
    raw = open(h.image_path, "rb").read()
    import io
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except Exception:
            continue
    else:
        return JSONResponse({"error": "CSV 파싱 실패"}, status_code=400)
    return {"filename": h.filename, "columns": list(df.columns),
            "rows": df.head(n).fillna("").to_dict(orient="records"),
            "total": len(df)}
