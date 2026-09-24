"""LLM 프롬프트 모음."""
COLUMN_MAPPING_PROMPT = """너는 은행/카드 CSV 헤더 매핑 전문가다.
아래 CSV 헤더 목록 중 날짜, 가맹점명, 금액에 해당하는 컬럼명을 JSON으로 답하라.
반드시 키는 date_col, merchant_col, amount_col, memo_col(없으면 null) 로 하라.
헤더: {headers}
예시 행: {sample_row}
JSON만 출력하라."""

BATCH_CLASSIFY_PROMPT = """너는 가계부 분류기다. 아래 거래 목록을 카테고리로 분류하라.
카테고리: 식비, 교통, 구독, 쇼핑, 의료, 고정비, 카페, 여가, 교육, 기타
서브카테고리 예: 배달/외식/장보기, 대중교통/택시/주유, OTT/음악/멤버십 등.

거래 목록(JSON):
{transactions}

각 거래 id에 대해 category, subcategory, confidence(0~1)를 담은 JSON 배열만 출력하라.
형식: [{{"id": 0, "category": "식비", "subcategory": "배달", "confidence": 0.92}}, ...]"""

RECEIPT_PROMPT = """이 영수증 이미지를 분석해 JSON으로 추출하라.
키: merchant(가맹점명), date(YYYY-MM-DD, 모르면 null), total_amount(숫자),
items([{{name, quantity, price}}]), confidence(0~1, 저화질/기울어짐이면 낮게), raw_text(읽힌 원문 요약).
JSON만 출력하라."""

TIPS_PROMPT = """너는 절약 코치다. 아래 월별 지출 데이터를 근거로 구체적인 절약 팁 3~5개를 JSON 배열로 제시하라.
일반론 금지. 반드시 숫자를 인용하라. 예: "이번 달 배달앱에서 12만원 썼는데 지난달보다 40% 증가했습니다."
각 팁은 category, tip, potential_savings_amount(추정 절약액 숫자), based_on(근거 문장) 키를 가져라.
지출 데이터: {stats}
JSON 배열만 출력하라."""
