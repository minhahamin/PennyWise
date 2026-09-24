# 💰 PennyWise — 개인 재무 관리 AI 에이전트

은행/카드 거래내역(CSV)이나 영수증 사진을 올리면, LLM이 지출을 분류·분석해서
**예산 초과 알림**과 **데이터 기반 절약 팁**을 제공하는 풀스택 서비스입니다.

| | |
|---|---|
| Backend | Python, FastAPI, LangGraph, LangChain, Pandas, SQLite |
| LLM | 텍스트 분류용 모델(`gpt-4o-mini`) + 비전 모델(영수증 OCR/분석) |
| Frontend | React(Vite), TypeScript, Recharts |
| 배포 | Docker Compose(로컬) / Railway(운영) |

## 운영 배포 (Railway — 프로젝트 `pennyWise`)

- 홈페이지: https://pennywise-production-9cf8.up.railway.app (서비스 `pennyWise`)
- API: https://pennywise-api-production.up.railway.app (서비스 `pennywise-api`, `/health`)
- DB: 별도 DB 서비스 없이 SQLite를 볼륨(`/data`, 5GB)에 저장 — 재배포에도 데이터 유지
- 빌드: 백엔드/프론트 모두 Nixpacks (`backend/Procfile`, `frontend`는 `Dockerfile.local` 지정)
  - ⚠️ `Dockerfile`이라는 이름 그대로 두면 Railpack prepare 단계에서 무응답 실패하므로
    로컬 Compose용은 `Dockerfile.local`로 분리하고 Compose에서 `dockerfile:`로 지정
- 프론트 빌드 시 `VITE_API_BASE`가 번들에 주입되므로 API 도메인 변경 시 프론트 재배포 필요
- IaC 스냅샷: `.railway/railway.ts` (참고용, 실제 적용은 CLI로 수행)

## 아키텍처

```
                 ┌──────────────┐      ┌────────────────────┐
  CSV 업로드 ──▶ │  FastAPI     │      │  LangGraph         │
  영수증 이미지─▶ │  /upload/*   │────▶ │  normalize →       │
                 │  /report/*   │      │  classify →        │
  React(Vite) ◀─ │  /budget     │◀──── │  trend → budget →  │
  Recharts 대시보드│  /alerts     │      │  tips → report     │
                 └──────────────┘      └────────────────────┘
                        │                       │
                        ▼                       ▼
                 SQLite(거래/예산/캐시)   OpenAI(gpt-4o-mini)
                                        + 규칙 기반 폴백(키 없어도 데모 가능)
```

**LangGraph 노드**: `[입력 정규화] → [카테고리 분류] → [패턴 분석] → [예산 체크] → [절약 팁 생성] → [리포트 종합]`
(`backend/app/graph/workflow.py` — 업로드 파이프라인 + 월 리포트 파이프라인 2종)

**비용 최적화**:
- 규칙 기반(가맹점 키워드) 우선 분류 → 실패 시에만 LLM 호출
- 가맹점별 `MerchantCache`로 재분류 방지 + 퍼지매칭으로 유사 가맹점 재활용
- CSV는 `BATCH_SIZE` 단위로 하나의 프롬프트에 묶어 배치 분류

## ERD

```
Transaction ──1:*── MerchantCache (merchant_normalized → category, hits)
     │
     └──1:*── Feedback (transaction_id → corrected_category, 캐시 갱신용)
Budget (category, year, month UNIQUE → budgeted_amount)
```

`Transaction`: id, date, merchant, amount, category, subcategory, confidence,
source(csv|receipt), receipt_image_path, memo

## 빠른 시작 (로컬)

```bash
# 1) 백엔드
cd backend && cp .env.example .env   # OPENAI_API_KEY 입력 (없어도 휴리스틱 모드로 동작)
pip install -r requirements.txt && uvicorn app.main:app --reload  # :8000

# 2) 프론트엔드
cd frontend && npm install && npm run dev  # :5173

# 3) Docker Compose
docker compose up --build  # api :8000, web :5173
```

데모 데이터: `data/samples/card_kookmin_3months.csv` 등 3종 포맷(가상 3개월치 177건)을
업로드 탭에 드래그하면 자동 컬럼 매핑 → 분류 → 리포트가 생성됩니다.

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/upload/csv` | CSV 업로드 (자동 컬럼 매핑, LLM 헤더 추론 폴백) |
| POST | `/upload/receipt` | 영수증 이미지 → 비전 LLM 구조화 추출 + 중복 체크 |
| GET | `/transactions` | 거래 조회 (기간·카테고리·검색·`needs_review`) |
| PATCH | `/transactions/{id}` | 카테고리 수동 수정 → Feedback 축적 + 캐시 갱신 |
| GET | `/report/monthly/{y}/{m}` | 월 리포트 (LangGraph 종합 결과) |
| POST | `/budget` | 카테고리별 예산 설정 |
| GET | `/alerts` | 예산 초과/임박 알림 |

## 평가/검증

```bash
python scripts/generate_sample_data.py  # 샘플 CSV 3종 + 라벨 테스트셋 생성
python scripts/evaluate_classifier.py   # 분류 정확도 측정 → 100/100 = 100.0%
python scripts/sample_receipt_test.py   # 합성 영수증 3종 추출 테스트
python tests/test_core.py               # 중복감지/매핑/리포트 그래프 → ALL PASSED
```

> 규칙 기반 분류기는 주요 가맹점에 대해 100%이며, 미등록 가맹점(롱테일)은
> LLM 배치 분류 + 사용자 수정 피드백(`MerchantCache`)으로 커버합니다.

## 프로젝트 구조

```
PennyWise/
├── backend/app/          # main, config, database, models, schemas
│   ├── api/              # uploads, transactions, reports
│   ├── services/         # csv_mapper, categorizer, dedup, analytics
│   ├── graph/            # LangGraph state + workflow
│   └── llm/              # provider(OpenAI+휴리스틱), prompts
├── frontend/src/         # pages(Dashboard/Transactions/Upload/Insights)
├── scripts/              # 샘플데이터 생성, 정확도 평가, 영수증 테스트
├── tests/test_core.py
└── docker-compose.yml
```
