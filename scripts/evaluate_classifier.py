"""카테고리 분류 정확도 측정: 규칙+캐시 분류기 vs 수동 라벨."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.llm.provider import heuristic_classify

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples" / "labeled_test.json"

def main():
    if not SAMPLES.exists():
        print("먼저 python scripts/generate_sample_data.py 실행 필요");
        return
    data = json.loads(SAMPLES.read_text(encoding="utf-8"))
    ok, total = 0, len(data)
    misses = []
    for row in data:
        pred = heuristic_classify(row["merchant"])["category"]
        # 식비/카페, 구독 세부 등은 관대하게 평가하지 않고 정확 일치로 측정
        if pred == row["expected"]:
            ok += 1
        else:
            misses.append((row["merchant"], row["expected"], pred))
    print(f"정확도: {ok}/{total} = {ok/total:.1%}")
    print("오분류 예시 (최대 10):")
    for m in misses[:10]:
        print(f"  {m[0]}: 정답={m[1]} 예측={m[2]}")

if __name__ == "__main__":
    main()
