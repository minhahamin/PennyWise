"""영수증 추출 테스트 — PIL로 합성 영수증 이미지 3종 생성 후 비전 추출 호출.

OPENAI_API_KEY가 없으면 mock 경로(confidence 낮음)임을 확인하는 용도.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow 필요: pip install Pillow")
    raise SystemExit(1)

from app.llm.provider import extract_receipt

OUT = Path(__file__).resolve().parent.parent / "data" / "samples"
OUT.mkdir(parents=True, exist_ok=True)

RECEIPTS = [
    ("receipt_starbucks.png", ["STARBUCKS 강남점", "2026-09-12", "아메리카노 Tall 4,500", "카페라떼 Tall 5,500", "합계 10,000원"]),
    ("receipt_emart.png", ["이마트 성수점", "2026-09-10", "삼겹살 18,900", "우유 3,200", "합계 22,100원"]),
    ("receipt_tilted_lowq.png", ["(기울어짐·저화질 가정) 김밥천국", "2026-09-08", "참치김밥 3,500", "라면 4,000", "합계 7,500원"]),
]

for fname, lines in RECEIPTS:
    img = Image.new("RGB", (420, 300), "white")
    d = ImageDraw.Draw(img)
    y = 20
    for ln in lines:
        d.text((20, y), ln, fill="black")
        y += 40
    if "tilted" in fname:
        img = img.rotate(8, expand=True, fillcolor="white")
        img = img.resize((210, 160)).resize((420, 300))  # 저화질 시뮬레이션
    img.save(OUT / fname)
    print("saved", fname)

print("\n--- 추출 테스트 ---")
for fname, _ in RECEIPTS:
    res = extract_receipt((OUT / fname).read_bytes())
    print(f"{fname}: merchant={res.get('merchant')} total={res.get('total_amount')} conf={res.get('confidence')}")
