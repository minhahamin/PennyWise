"""카테고리 분류: 규칙 → 캐시 → (유사 가맹점) → 배치 LLM.

비용 최적화: 같은 가맹점명은 MerchantCache 적중 시 LLM 호출 스킵,
CSV 업로드 건은 BATCH_SIZE 단위로 하나의 프롬프트에 묶어 호출.
"""
from __future__ import annotations

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import provider as llm
from app.models import MerchantCache

FUZZY_THRESHOLD = 90


def _norm(name: str) -> str:
    return "".join(name.lower().split())


def cached_lookup(db: Session, merchant: str) -> MerchantCache | None:
    n = _norm(merchant)
    hit = db.query(MerchantCache).filter_by(merchant_normalized=n).first()
    if hit:
        return hit
    # 유사 가맹점 검색 (RAG 느낌의 벡터 유사도 대신 퍼지 매칭)
    for row in db.query(MerchantCache).all():
        if fuzz.ratio(row.merchant_normalized, n) >= FUZZY_THRESHOLD:
            return row
    return None


def classify_batch(db: Session, merchants: list[str]) -> list[dict]:
    """merchants 순서대로 [{category, subcategory, confidence, cached}] 반환."""
    results: list[dict | None] = [None] * len(merchants)
    pending: list[dict] = []
    for i, m in enumerate(merchants):
        rule = llm.heuristic_classify(m)
        if rule["confidence"] >= 0.8:
            results[i] = {**rule, "cached": True}
            continue
        hit = cached_lookup(db, m)
        if hit:
            hit.hits += 1
            results[i] = {"category": hit.category, "subcategory": hit.subcategory,
                          "confidence": 0.9, "cached": True}
        else:
            pending.append({"id": i, "merchant": m, "amount": 0, "memo": ""})
    # 배치 LLM 호출
    for s in range(0, len(pending), settings.batch_size):
        chunk = pending[s : s + settings.batch_size]
        llm_out = llm.batch_classify(chunk)
        for item in llm_out:
            i = item["id"]
            cat = {"category": item.get("category", "기타"),
                   "subcategory": item.get("subcategory", ""),
                   "confidence": float(item.get("confidence", 0.5)), "cached": False}
            results[i] = cat
            # 캐시 저장
            db.merge(MerchantCache(merchant_normalized=_norm(merchants[i]),
                                   category=cat["category"], subcategory=cat["subcategory"]))
    db.commit()
    return [r or {"category": "기타", "subcategory": "", "confidence": 0.4, "cached": False} for r in results]
