"""패턴 분석 + 예산 체크 + 절약 팁 (LangGraph 노드에서도 재사용)."""
from __future__ import annotations

import calendar
from collections import Counter, defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.llm import provider as llm
from app.models import Budget, Transaction


def monthly_transactions(db: Session, year: int, month: int) -> list[Transaction]:
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return db.query(Transaction).filter(Transaction.date >= start, Transaction.date <= end).all()


def prev_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def analyze_trend(cur: list[Transaction], prev: list[Transaction]) -> dict:
    cur_by = defaultdict(float)
    prev_by = defaultdict(float)
    for t in cur:
        cur_by[t.category] += t.amount
    for t in prev:
        prev_by[t.category] += t.amount
    comp: dict[str, float] = {}
    for cat in set(cur_by) | set(prev_by):
        c, p = cur_by.get(cat, 0), prev_by.get(cat, 0)
        comp[f"{cat}_change_pct"] = round((c - p) / p * 100, 1) if p else (100.0 if c else 0.0)
    total_c, total_p = sum(cur_by.values()), sum(prev_by.values())
    comp["total_change_pct"] = round((total_c - total_p) / total_p * 100, 1) if total_p else 0.0
    # 급증 항목 (전월 대비 +30% & 3만원↑)
    surges = [c for c in set(cur_by) & set(prev_by)
              if prev_by[c] and (cur_by[c] - prev_by[c]) / prev_by[c] >= 0.3 and cur_by[c] - prev_by[c] >= 30000]
    return {"current": dict(cur_by), "previous": dict(prev_by), "comparison": comp, "surges": surges}


def check_budgets(db: Session, year: int, month: int, spent_by_cat: dict[str, float]) -> list[dict]:
    alerts = []
    for b in db.query(Budget).filter_by(year=year, month=month).all():
        actual = spent_by_cat.get(b.category, 0)
        pct = (actual / b.budgeted_amount * 100) if b.budgeted_amount else 0
        sev = "exceeded" if pct >= 100 else ("warning" if pct >= 80 else "safe")
        alerts.append({"category": b.category, "budgeted_amount": b.budgeted_amount,
                       "actual_amount": actual, "percentage_used": round(pct, 1), "severity": sev})
    return alerts


def build_tips(stats: dict) -> list[dict]:
    return llm.generate_tips(stats)


def top_merchants(txns: list[Transaction], n: int = 5) -> list[dict]:
    c = Counter()
    for t in txns:
        c[t.merchant] += t.amount
    return [{"merchant": m, "amount": round(a)} for m, a in c.most_common(n)]
