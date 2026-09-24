"""중복 거래 감지: 날짜+금액+가맹점 유사도."""
from __future__ import annotations

from datetime import date

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models import Transaction

MERCHANT_SIM_THRESHOLD = 85


def is_duplicate(db: Session, d: date, merchant: str, amount: float) -> bool:
    """같은 날짜 & 같은 금액 & 가맹점명 유사도 85↑ 이면 중복."""
    cands = (
        db.query(Transaction)
        .filter(Transaction.date == d, Transaction.amount == amount)
        .all()
    )
    for t in cands:
        if fuzz.ratio(t.merchant, merchant) >= MERCHANT_SIM_THRESHOLD:
            return True
    return False
