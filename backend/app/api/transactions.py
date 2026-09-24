from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Budget, Feedback, MerchantCache, Transaction
from app.services.categorizer import _norm

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(category: str | None = None, start: date | None = None,
                      end: date | None = None, q: str | None = None,
                      needs_review: bool = False, limit: int = 20, offset: int = 0,
                      db: Session = Depends(get_db)):
    query = db.query(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
    if category:
        query = query.filter(Transaction.category == category)
    if start:
        query = query.filter(Transaction.date >= start)
    if end:
        query = query.filter(Transaction.date <= end)
    if q:
        query = query.filter(Transaction.merchant.contains(q))
    if needs_review:
        query = query.filter(Transaction.confidence < 0.6)
    total = query.count()
    rows = query.offset(offset).limit(min(limit, 100)).all()
    return {"items": [{"id": t.id, "date": t.date.isoformat(), "merchant": t.merchant,
             "amount": t.amount, "category": t.category, "subcategory": t.subcategory,
             "confidence": t.confidence, "source": t.source,
             "receipt_image_path": t.receipt_image_path, "memo": t.memo,
             "needs_review": t.confidence < 0.6} for t in rows],
            "total": total, "limit": limit, "offset": offset}


class CorrectIn(BaseModel):
    category: str
    subcategory: str = ""


@router.patch("/transactions/{txn_id}")
def correct_category(txn_id: int, body: CorrectIn, db: Session = Depends(get_db)):
    """수동 수정 → Feedback 축적 + MerchantCache 갱신 (재학습 구조)."""
    t = db.query(Transaction).filter_by(id=txn_id).first()
    if not t:
        return {"error": "not found"}
    t.category, t.subcategory, t.confidence = body.category, body.subcategory, 1.0
    db.add(Feedback(transaction_id=txn_id, corrected_category=body.category,
                    corrected_subcategory=body.subcategory))
    db.merge(MerchantCache(merchant_normalized=_norm(t.merchant),
                           category=body.category, subcategory=body.subcategory))
    db.commit()
    return {"ok": True}
