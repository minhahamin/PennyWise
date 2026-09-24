"""LangGraph 워크플로우: 입력 정규화 → 분류 → 패턴분석 → 예산체크 → 절약팁 → 리포트종합.

CSV 업로드 파이프라인과 월 리포트 파이프라인 2개를 제공한다.
LLM 키가 없어도 전체 그래프가 동작하도록 휴리스틱 폴백을 사용한다.
"""
from __future__ import annotations

from datetime import date

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.graph.state import PipelineState, ReportState
from app.models import Transaction
from app.services import analytics as A
from app.services import categorizer as C
from app.services import dedup


# ---------- 업로드 파이프라인 노드 ----------
def node_normalize(state: PipelineState) -> dict:
    norm = []
    for r in state.get("raw_items", []):
        d = r["date"]
        if isinstance(d, str):
            d = date.fromisoformat(d[:10])
        norm.append({"date": d, "merchant": str(r["merchant"]).strip(),
                     "amount": abs(float(r["amount"])), "memo": r.get("memo", "")})
    return {"normalized": norm}


def node_classify(state: PipelineState) -> dict:
    db: Session = SessionLocal()
    try:
        merchants = [n["merchant"] for n in state.get("normalized", [])]
        cats = C.classify_batch(db, merchants)
        classified = [{**n, **c} for n, c in zip(state.get("normalized", []), cats)]
        return {"classified": classified}
    finally:
        db.close()


def node_persist(state: PipelineState) -> dict:
    """중복 제거 후 DB 저장 (그래프 노드로 포함해 추적 가능하게)."""
    db: Session = SessionLocal()
    try:
        saved, skipped = 0, 0
        for c in state.get("classified", []):
            if dedup.is_duplicate(db, c["date"], c["merchant"], c["amount"]):
                skipped += 1
                continue
            db.add(Transaction(date=c["date"], merchant=c["merchant"], amount=c["amount"],
                               category=c["category"], subcategory=c.get("subcategory", ""),
                               confidence=c.get("confidence", 0.5),
                               source=state.get("source", "csv"), memo=c.get("memo", "")))
            saved += 1
        db.commit()
        return {"skipped_duplicates": skipped}
    finally:
        db.close()


def build_upload_graph():
    g = StateGraph(PipelineState)
    g.add_node("normalize", node_normalize)
    g.add_node("classify", node_classify)
    g.add_node("persist", node_persist)
    g.set_entry_point("normalize")
    g.add_edge("normalize", "classify")
    g.add_edge("classify", "persist")
    g.add_edge("persist", END)
    return g.compile()


# ---------- 월 리포트 파이프라인 노드 ----------
def node_trend(state: ReportState) -> dict:
    db = SessionLocal()
    try:
        cur = A.monthly_transactions(db, state["year"], state["month"])
        py, pm = A.prev_month(state["year"], state["month"])
        prev = A.monthly_transactions(db, py, pm)
        trend = A.analyze_trend(cur, prev)
        merchants = A.top_merchants(cur)
        return {"trend": {**trend, "top_merchants": merchants,
                          "total": round(sum(t.amount for t in cur))}}
    finally:
        db.close()


def node_budget(state: ReportState) -> dict:
    db = SessionLocal()
    try:
        alerts = A.check_budgets(db, state["year"], state["month"], state["trend"]["current"])
        return {"alerts": alerts}
    finally:
        db.close()


def node_tips(state: ReportState) -> dict:
    tips = A.build_tips({"current": state["trend"]["current"], "previous": state["trend"]["previous"]})
    return {"tips": tips}


def node_report(state: ReportState) -> dict:
    report = {"year": state["year"], "month": state["month"],
              "total_spending": state["trend"]["total"],
              "category_breakdown": state["trend"]["current"],
              "top_merchants": state["trend"]["top_merchants"],
              "alerts": state.get("alerts", []), "tips": state.get("tips", []),
              "comparison_to_last_month": state["trend"]["comparison"]}
    return {"report": report}


def build_report_graph():
    g = StateGraph(ReportState)
    g.add_node("analyze_trend", node_trend)
    g.add_node("check_budget", node_budget)
    g.add_node("make_tips", node_tips)
    g.add_node("compile_report", node_report)
    g.set_entry_point("analyze_trend")
    g.add_edge("analyze_trend", "check_budget")
    g.add_edge("check_budget", "make_tips")
    g.add_edge("make_tips", "compile_report")
    g.add_edge("compile_report", END)
    return g.compile()


upload_graph = build_upload_graph()
report_graph = build_report_graph()
