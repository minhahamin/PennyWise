"""Pydantic 구조화 출력 스키마 (스펙 §3)."""
import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["safe", "warning", "exceeded"]


class NormalizedTransaction(BaseModel):
    date: dt.date
    merchant: str
    amount: float
    memo: str = ""


class TransactionCategory(BaseModel):
    transaction_id: int | None = None
    category: str
    subcategory: str = ""
    confidence: float = Field(ge=0.0, le=1.0)


class ReceiptItem(BaseModel):
    name: str
    quantity: int = 1
    price: float


class ReceiptExtraction(BaseModel):
    merchant: str
    date: Optional[dt.date] = None
    total_amount: float
    items: list[ReceiptItem] = []
    confidence: float = Field(ge=0.0, le=1.0)
    raw_text: str = ""


class ColumnMapping(BaseModel):
    date_col: str
    merchant_col: str
    amount_col: str
    memo_col: str | None = None


class BudgetAlert(BaseModel):
    category: str
    budgeted_amount: float
    actual_amount: float
    percentage_used: float
    severity: Severity


class SavingTip(BaseModel):
    category: str
    tip: str
    potential_savings_amount: float
    based_on: str  # 근거 데이터 인용 (예: "배달의민족 8건 124,000원, 전월 대비 +40%")


class MonthlyReport(BaseModel):
    year: int
    month: int
    total_spending: float
    category_breakdown: dict[str, float]
    top_merchants: list[dict]
    alerts: list[BudgetAlert]
    tips: list[SavingTip]
    comparison_to_last_month: dict[str, float]  # {"total_change_pct": ..., "<cat>_change_pct": ...}


CATEGORIES = ["식비", "교통", "구독", "쇼핑", "의료", "고정비", "카페", "여가", "교육", "기타"]
