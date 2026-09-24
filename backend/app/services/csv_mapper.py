"""CSV 자동 컬럼 매핑: 규칙 우선 → 애매하면 LLM 추론."""
from __future__ import annotations

import pandas as pd

from app.llm import provider as llm
from app.schemas import ColumnMapping


def auto_map_columns(df: pd.DataFrame) -> ColumnMapping:
    headers = list(df.columns)
    rule = llm.heuristic_column_mapping(headers)
    # 규칙 매핑 신뢰도: 헤더에 키워드가 실제로 있었는지 확인
    ambiguous = rule["date_col"] == rule["merchant_col"] or rule["merchant_col"] == rule["amount_col"]
    if ambiguous and llm._client() is not None:
        sample = df.head(2).to_dict(orient="records")
        inferred = llm.infer_column_mapping(headers, sample[0] if sample else {})
        return ColumnMapping(**{k: inferred.get(k) for k in ("date_col", "merchant_col", "amount_col", "memo_col")})
    return ColumnMapping(**rule)


def normalize_csv(df: pd.DataFrame, mapping: ColumnMapping) -> list[dict]:
    """CSV → 공통 스키마 [{date, merchant, amount, memo}]. 금액 파싱/날짜 파싱 포함."""
    out = []
    for _, row in df.iterrows():
        try:
            date = pd.to_datetime(row[mapping.date_col]).date()
            merchant = str(row[mapping.merchant_col]).strip()
            raw_amt = str(row[mapping.amount_col]).replace(",", "").replace("원", "").strip()
            amount = abs(float(raw_amt))  # 출금/승인금액 모두 지출 양수로 정규화
            memo = str(row[mapping.memo_col]).strip() if mapping.memo_col and mapping.memo_col in df.columns else ""
            if not merchant or merchant.lower() == "nan":
                continue
            out.append({"date": date, "merchant": merchant, "amount": amount, "memo": memo})
        except Exception:
            continue  # 파싱 실패 행 스킵 (업로드 리포트에 카운트)
    return out
