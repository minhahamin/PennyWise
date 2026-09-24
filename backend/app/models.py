"""SQLAlchemy ORM models.

ERD:
  Transaction (id, date, merchant, amount, category, subcategory,
               confidence, source[csv|receipt], receipt_image_path, memo)
      1 ── * MerchantCache (merchant_normalized -> category, subcategory, hits)
      1 ── * Feedback (transaction_id -> corrected_category)
  Budget (category, year, month, budgeted_amount)  UNIQUE(category, year, month)
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    merchant: Mapped[str] = mapped_column(String(255), index=True)
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(64), default="기타", index=True)
    subcategory: Mapped[str] = mapped_column(String(64), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(16), default="csv")  # csv | receipt
    receipt_image_path: Mapped[str] = mapped_column(String(512), default="")
    memo: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MerchantCache(Base):
    """가맹점명 -> 카테고리 캐시 (LLM 호출 최소화 / RAG 대용 규칙 캐시)."""

    __tablename__ = "merchant_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_normalized: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64))
    subcategory: Mapped[str] = mapped_column(String(64), default="")
    hits: Mapped[int] = mapped_column(Integer, default=1)


class Feedback(Base):
    """사용자 수동 수정 이력 — 재학습/캐시 갱신용."""

    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    corrected_category: Mapped[str] = mapped_column(String(64))
    corrected_subcategory: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("category", "year", "month", name="uq_budget_cat_ym"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    budgeted_amount: Mapped[float] = mapped_column(Float)
