"""LangGraph 상태 정의."""
from datetime import date
from typing import TypedDict


class PipelineState(TypedDict, total=False):
    raw_items: list[dict]            # 입력 정규화 전 (CSV row dict 또는 영수증 dict)
    source: str                     # "csv" | "receipt"
    normalized: list[dict]          # [{date, merchant, amount, memo}]
    classified: list[dict]          # normalized + category/subcategory/confidence
    trend: dict
    alerts: list[dict]
    tips: list[dict]
    report: dict
    year: int
    month: int
    skipped_duplicates: int


class ReportState(TypedDict, total=False):
    year: int
    month: int
    trend: dict
    alerts: list[dict]
    tips: list[dict]
    report: dict
