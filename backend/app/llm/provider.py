"""LLM Provider — OpenAI/OpenRouter 호출, 실패 시 결정적 휴리스틱 폴백.

설계 의도(비용 최적화 + 내결함성):
- API 키가 없어도 데모/테스트가 돌아가도록 mock 경로 제공
- rate-limit/네트워크 오류 시에도 500 없이 휴리스틱으로 응답 (무료 모델 공유풀 대비)
- OPENAI_BASE_URL 지정 시 OpenRouter 등 OpenAI 호환 엔드포인트 사용
"""
from __future__ import annotations

import base64
import json
import re

from app.config import settings
from app.llm import prompts


def _extract_json(text: str) -> str:
    """LLM 출력에서 JSON 블록만 추출."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    s, e = text.find("{"), text.rfind("}")
    sa, ea = text.find("["), text.rfind("]")
    # 배열이 더 바깥이면 배열 반환
    if sa != -1 and (s == -1 or sa < s):
        return text[sa : ea + 1]
    if s != -1:
        return text[s : e + 1]
    return text.strip()


def _client():
    if not settings.llm_enabled:
        return None
    from openai import OpenAI

    kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


# ---------- 텍스트 분류용 ----------
def _heuristic_batch(items: list[dict]) -> list[dict]:
    return [heuristic_classify(it["merchant"]) | {"id": it["id"]} for it in items]


def batch_classify(items: list[dict]) -> list[dict]:
    """items: [{"id": int, "merchant": str, "amount": float, "memo": str}]."""
    client = _client()
    if client is None:
        return _heuristic_batch(items)
    payload = json.dumps(items, ensure_ascii=False)
    try:
        resp = client.chat.completions.create(
            model=settings.text_model,
            messages=[{"role": "user", "content": prompts.BATCH_CLASSIFY_PROMPT.format(transactions=payload)}],
            temperature=0,
        )
        return json.loads(_extract_json(resp.choices[0].message.content or "[]"))
    except Exception:
        # rate-limit/네트워크/파싱 실패 시 휴리스틱 폴백 (500 방지)
        return _heuristic_batch(items)


def infer_column_mapping(headers: list[str], sample_row: dict) -> dict:
    client = _client()
    if client is None:
        return heuristic_column_mapping(headers)
    try:
        resp = client.chat.completions.create(
            model=settings.text_model,
            messages=[
                {
                    "role": "user",
                    "content": prompts.COLUMN_MAPPING_PROMPT.format(
                        headers=headers, sample_row=json.dumps(sample_row, ensure_ascii=False)
                    ),
                }
            ],
            temperature=0,
        )
        return json.loads(_extract_json(resp.choices[0].message.content or "{}"))
    except Exception:
        return heuristic_column_mapping(headers)


def generate_tips(stats: dict) -> list[dict]:
    client = _client()
    if client is None:
        return heuristic_tips(stats)
    try:
        resp = client.chat.completions.create(
            model=settings.text_model,
            messages=[{"role": "user", "content": prompts.TIPS_PROMPT.format(stats=json.dumps(stats, ensure_ascii=False))}],
            temperature=0.3,
        )
        out = json.loads(_extract_json(resp.choices[0].message.content or "[]"))
        return out if isinstance(out, list) else heuristic_tips(stats)
    except Exception:
        return heuristic_tips(stats)


def _receipt_fallback(raw: str = "") -> dict:
    return {"merchant": "판독실패", "date": None, "total_amount": 0,
            "items": [], "confidence": 0.1, "raw_text": raw}


# ---------- 비전(영수증) ----------
def extract_receipt(image_bytes: bytes) -> dict:
    client = _client()
    if client is None:
        return {"merchant": "모의상점", "date": None, "total_amount": 0,
                "items": [], "confidence": 0.3, "raw_text": "mock (API 키 없음)"}
    b64 = base64.b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model=settings.vision_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts.RECEIPT_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
            temperature=0,
        )
        return json.loads(_extract_json(resp.choices[0].message.content or "{}"))
    except Exception as e:
        return _receipt_fallback(raw=f"LLM 오류: {type(e).__name__}")


# ---------- 휴리스틱 폴백 (키워드 규칙 기반) ----------
_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("식비", "배달", ("배달", "요기요", "배민", "쿠팡이츠", "족발", "치킨", "분식", "식당", "한식", "중식")),
    ("식비", "장보기", ("이마트", "홈플러스", "롯데마트", "마켓컬리", "식자재", "마트", "농협", "GS25", "CU", "세븐일레븐", "편의점", "이마트24")),
    ("카페", "카페", ("스타벅스", "투썸", "이디야", "메가커피", "컴포즈", "카페", "커피")),
    ("교통", "대중교통", ("지하철", "버스", "티머니", "교통", "코레일", "SRT")),
    ("교통", "택시", ("택시", "카카오T", "우버", "타다")),
    ("교통", "주유", ("주유", "GS칼텍스", "SK에너지", "현대오일", "충전")),
    ("구독", "OTT", ("넷플릭스", "유튜브프리미엄", "디즈니", "티빙", "웨이브", "왓챠")),
    ("구독", "멤버십", ("쿠팡와우", "네이버플러스", "멜론", "스포티파이", "노션", "챗GPT", "구독")),
    ("쇼핑", "온라인", ("쿠팡", "11번가", "G마켓", "네이버쇼핑", "무신사", "올리브영", "다이소")),
    ("쇼핑", "오프라인", ("백화점", "아울렛", "유니클로", "자라", "이케아")),
    ("의료", "병원", ("병원", "의원", "치과", "약국", "건강검진")),
    ("고정비", "통신", ("SKT", "KT", "LGU+", "통신", "요금")),
    ("고정비", "주거", ("월세", "관리비", "전기", "가스", "수도", "인터넷")),
    ("여가", "문화", ("CGV", "롯데시네마", "메가박스", "공연", "전시", "노래방", "PC방")),
    ("교육", "교육", ("학원", "인강", "교보문고", "YES24", "수강")),
]


def heuristic_classify(merchant: str) -> dict:
    m = (merchant or "").lower()
    for cat, sub, kws in _RULES:
        if any(k.lower() in m for k in kws):
            return {"category": cat, "subcategory": sub, "confidence": 0.85}
    return {"category": "기타", "subcategory": "", "confidence": 0.4}


def heuristic_column_mapping(headers: list[str]) -> dict:
    def find(cands: list[str]) -> str | None:
        for h in headers:
            hl = h.strip().lower()
            if any(c in hl for c in cands):
                return h
        return None

    date_col = find(["날짜", "date", "거래일", "승인일"]) or headers[0]
    merch_col = find(["가맹점", "merchant", "상호", "적요", "내용", "점포"]) or headers[1 if len(headers) > 1 else 0]
    amt_col = find(["금액", "amount", "합계", "이용금액", "출금", "결제"]) or headers[-1]
    return {"date_col": date_col, "merchant_col": merch_col, "amount_col": amt_col, "memo_col": None}


def heuristic_tips(stats: dict) -> list[dict]:
    """stats: {"current": {cat: amt}, "previous": {cat: amt}} — 데이터 기반 팁 생성."""
    cur, prev = stats.get("current", {}), stats.get("previous", {})
    tips = []
    for cat, amt in sorted(cur.items(), key=lambda x: -x[1])[:5]:
        p = prev.get(cat, 0)
        if p > 0 and amt > p * 1.1:
            pct = round((amt - p) / p * 100)
            tips.append({
                "category": cat,
                "tip": f"이번 달 {cat} 지출이 {amt:,.0f}원으로 지난달({p:,.0f}원)보다 {pct}% 증가했습니다. 주 1회만 줄여도 월 {amt * 0.15:,.0f}원 절약이 가능합니다.",
                "potential_savings_amount": round(amt * 0.15),
                "based_on": f"{cat} {p:,.0f}원 → {amt:,.0f}원 ({pct:+d}%)",
            })
    if not tips and cur:
        top = max(cur.items(), key=lambda x: x[1])
        tips.append({
            "category": top[0],
            "tip": f"가장 큰 지출인 {top[0]}({top[1]:,.0f}원)부터 점검하세요. 고정비라면 요금제/구독 정리를 권장합니다.",
            "potential_savings_amount": round(top[1] * 0.1),
            "based_on": f"{top[0]} 월 지출 {top[1]:,.0f}원",
        })
    return tips
