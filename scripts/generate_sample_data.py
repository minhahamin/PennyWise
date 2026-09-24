"""가상 3개월치 거래내역 생성 — 은행/카드사별 다른 컬럼명으로 3종 포맷 출력."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "samples"
OUT.mkdir(parents=True, exist_ok=True)

MERCHANTS = [
    ("스타벅스 강남점", "카페", (4500, 8000), 0.10),
    ("배달의민족", "식비", (12000, 30000), 0.10),
    ("쿠팡", "쇼핑", (15000, 90000), 0.08),
    ("GS25 역삼점", "식비", (3000, 12000), 0.06),
    ("카카오T택시", "교통", (6000, 20000), 0.05),
    ("지하철 정기권", "교통", (55000, 55000), 0.01),
    ("넷플릭스", "구독", (13500, 13500), 0.02),
    ("쿠팡와우", "구독", (4990, 4990), 0.02),
    ("올리브영", "쇼핑", (8000, 40000), 0.05),
    ("이마트 성수점", "식비", (30000, 90000), 0.05),
    ("CGV", "여가", (14000, 30000), 0.03),
    ("서울대병원약국", "의료", (5000, 25000), 0.02),
    ("SKT 통신요금", "고정비", (60000, 80000), 0.02),
    ("월세", "고정비", (550000, 550000), 0.02),
    ("메가커피", "카페", (2500, 5000), 0.07),
    ("교보문고", "교육", (12000, 35000), 0.02),
    ("무신사", "쇼핑", (20000, 70000), 0.04),
    ("요기요", "식비", (15000, 28000), 0.06),
]

START = date(2026, 7, 1)
rows = []
d = START
end = date(2026, 9, 30)
labeled = []
while d <= end:
    for merch, cat, (lo, hi), p in MERCHANTS:
        if random.random() < min(0.9, p * 2.5 * (1.3 if d.month == 9 and merch in ("배달의민족", "요기요", "쿠팡") else 1.0)):
            amt = random.randint(lo // 100, hi // 100) * 100
            rows.append((d.isoformat(), merch, amt, cat))
            labeled.append({"merchant": merch, "amount": amt, "label": cat})
    d += timedelta(days=1)

random.shuffle(rows)
print(f"총 {len(rows)}건 생성")

# 포맷 A: 국민카드식
with open(OUT / "card_kookmin_3months.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["승인일자", "가맹점명", "이용금액", "적요"])
    for d_, m, a, _ in rows:
        w.writerow([d_, m, a, "일시불"])
# 포맷 B: 영문 헤더 은행식
with open(OUT / "bank_generic_3months.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date", "description", "amount", "balance"])
    bal = 3000000
    for d_, m, a, _ in rows:
        bal -= a
        w.writerow([d_, m, f"{a}원", bal])
# 포맷 C: 다른 순서/명칭
with open(OUT / "card_hyundai_3months.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["거래일", "내용", "출금액", "입금액"])
    for d_, m, a, _ in rows:
        w.writerow([d_, m, a, ""])

# 라벨 테스트셋 (100건 샘플)
import json
random.seed(7)
test = random.sample(labeled, min(100, len(labeled)))
with open(OUT / "labeled_test.json", "w", encoding="utf-8") as f:
    json.dump([{"merchant": t["merchant"], "expected": t["label"]} for t in test], f, ensure_ascii=False, indent=2)
print("saved:", list(OUT.glob('*')))
