from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.graph.workflow import report_graph
from app.models import Budget
from app.services import analytics as A

router = APIRouter(tags=["report"])


class BudgetIn(BaseModel):
    category: str
    year: int
    month: int
    budgeted_amount: float


@router.post("/budget")
def set_budget(body: BudgetIn, db: Session = Depends(get_db)):
    b = db.query(Budget).filter_by(category=body.category, year=body.year, month=body.month).first()
    if b:
        b.budgeted_amount = body.budgeted_amount
    else:
        db.add(Budget(**body.model_dump()))
    db.commit()
    return {"ok": True}


@router.get("/report/monthly/{year}/{month}")
def monthly_report(year: int, month: int):
    result = report_graph.invoke({"year": year, "month": month})
    return result.get("report", {})


@router.get("/alerts")
def alerts(year: int, month: int, db: Session = Depends(get_db)):
    txns = A.monthly_transactions(db, year, month)
    by_cat: dict[str, float] = {}
    for t in txns:
        by_cat[t.category] = by_cat.get(t.category, 0) + t.amount
    return A.check_budgets(db, year, month, by_cat)
