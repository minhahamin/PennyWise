import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base, SessionLocal, engine
from app.models import Budget
from app.services.dedup import is_duplicate
from app.models import Transaction


def test_dedup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(Transaction).delete()
    db.commit()
    db.add(Transaction(date=date(2026, 9, 12), merchant="스타벅스 강남점", amount=5500, category="카페"))
    db.commit()
    assert is_duplicate(db, date(2026, 9, 12), "스타벅스강남점", 5500) is True
    assert is_duplicate(db, date(2026, 9, 12), "스타벅스 강남점", 6000) is False
    assert is_duplicate(db, date(2026, 9, 13), "스타벅스 강남점", 5500) is False
    db.query(Transaction).delete()
    db.commit()
    print("test_dedup OK")


def test_csv_mapping():
    import pandas as pd
    from app.services import csv_mapper
    df = pd.DataFrame([{"승인일자": "2026-09-01", "가맹점명": "스타벅스", "이용금액": "5,500원"}])
    m = csv_mapper.auto_map_columns(df)
    assert m.date_col == "승인일자" and m.merchant_col == "가맹점명", m
    norm = csv_mapper.normalize_csv(df, m)
    assert norm[0]["amount"] == 5500 and norm[0]["merchant"] == "스타벅스"
    print("test_csv_mapping OK")


def test_report_graph():
    from app.database import Base, engine
    from app.graph.workflow import report_graph
    Base.metadata.create_all(bind=engine)
    out = report_graph.invoke({"year": 2026, "month": 9})
    assert "report" in out and "total_spending" in out["report"]
    print("test_report_graph OK")


if __name__ == "__main__":
    test_dedup()
    test_csv_mapping()
    test_report_graph()
    print("ALL TESTS PASSED")
