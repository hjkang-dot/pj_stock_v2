# PJ Stock V2

국내 주식 데이터를 수집하고 정제한 뒤, SQLite DB와 웹 화면에서 종목 목록, 시세, 재무/배당 정보, 저평가 배당주 평가 순위를 조회하는 프로젝트입니다.

백엔드는 FastAPI와 SQLite를 사용하고, 프론트엔드는 Vite + React로 구성되어 있습니다. 데이터 수집은 KRX/DART API 키가 필요합니다.

## 프로젝트 구조

```text
pj_stock_v2/
├─ backend/
│  ├─ scripts/                 # 데이터 수집, 정제, DB 적재 스크립트
│  ├─ src/pj_stock_backend/    # FastAPI 앱, DB, repository, pipeline 코드
│  └─ tests/                   # 백엔드 테스트
├─ data/
│  ├─ raw/                     # 원천 데이터 저장 위치
│  └─ processed/               # 정제 데이터 저장 위치
├─ docs/
├─ frontend/                   # Vite + React 프론트엔드
└─ README.md
```

## 요구 사항

- Python 3.14 이상
- [uv](https://docs.astral.sh/uv/)
- Node.js, npm
- KRX Open API 인증키
- DART Open API 인증키

## 1. 백엔드 설치

```powershell
cd backend
uv sync --dev
```

환경 변수 파일을 준비합니다.

```powershell
Copy-Item .env.example .env
```

`backend/.env`에 API 키를 입력합니다.

```env
APP_NAME=PJ Stock Backend
ENVIRONMENT=local
DATABASE_URL=sqlite:///../data/app.db

DART_API_KEY='발급받은_DART_API_KEY'
KRX_API_KEY='발급받은_KRX_API_KEY'
```

SQLite 스키마는 백엔드 실행 시 자동 초기화되지만, 수동으로 만들 수도 있습니다.

```powershell
uv run python scripts/init_db.py
```

## 2. 데이터 수집 및 정제

아래 명령은 모두 `backend` 디렉터리에서 실행합니다. 스크립트가 `../data/...` 경로를 기준으로 파일을 읽고 쓰기 때문입니다.

### KRX 상장 종목 수집

```powershell
uv run python scripts/fetch_krx_listed_stocks.py
uv run python scripts/clean_krx_listed_stocks.py
```

정제 결과:

```text
data/processed/stocks.csv
```

### DART 기업 코드 수집

```powershell
uv run python scripts/fetch_dart_corp_codes.py
uv run python scripts/clean_dart_corp_codes.py
```

정제 결과:

```text
data/processed/dart_corp_codes.csv
```

### DART 재무제표/배당 정보 수집

먼저 적은 수의 기업으로 테스트합니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/clean_dart_financial_statements.py --business-year 2025 --report-code 11011
uv run python scripts/clean_dart_dividends.py --business-year 2025 --report-code 11011
```

전체 기업을 수집하려면 `--limit 0`을 사용합니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 0 --sleep-seconds 1
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 0 --sleep-seconds 1
```

주요 인자:

- `--business-year`: 사업연도입니다. 기본값은 `2025`입니다.
- `--report-code`: DART 보고서 코드입니다. 보통 사업보고서인 `11011`을 사용합니다.
- `--limit`: 수집할 기업 수입니다. `0`이면 전체 기업을 대상으로 합니다.
- `--sleep-seconds`: 기업별 API 요청 사이 대기 시간입니다.

DART 보고서 코드:

```text
11013: 1분기보고서
11012: 반기보고서
11014: 3분기보고서
11011: 사업보고서
```

### KRX 일별 시세 DB 동기화

최근 365일을 기준으로 DB에 없는 거래일 데이터를 동기화합니다.

```powershell
uv run python scripts/sync_krx_daily_prices_to_db.py
```

기간을 지정하려면 다음처럼 실행합니다.

```powershell
uv run python scripts/sync_krx_daily_prices_to_db.py --start-date 20250101 --end-date 20251231
uv run python scripts/sync_krx_daily_prices_to_db.py --days 30
```

### CSV 데이터를 SQLite DB에 적재

상장 종목과 DART 기업 코드를 DB에 적재합니다.

```powershell
uv run python scripts/sync_krx_listed_stocks_to_db.py
```

정제된 재무제표와 배당 정보를 합쳐 `company_financials` 테이블에 적재합니다.

```powershell
uv run python scripts/sync_financials_to_db.py
```

## 3. 저평가 배당주 후보 산출

정제 CSV와 DB에 적재된 일별 시세를 이용해 후보 종목 CSV를 생성합니다.

```powershell
uv run python scripts/screen_undervalued_dividend_stocks.py --business-year 2025 --report-code 11011 --base-date 20260522 --minimum-total-score 60 --top 30
```

결과 파일:

```text
data/processed/undervalued_dividend_candidates_2025_20260522.csv
```

## 4. 백엔드 실행

```powershell
cd backend
uv run uvicorn pj_stock_backend.main:app --reload
```

기본 주소:

```text
http://localhost:8000
```

헬스체크:

```text
GET http://localhost:8000/health
```

Swagger 문서:

```text
http://localhost:8000/docs
```

주요 API:

```text
GET  /api/stocks
GET  /api/stocks?search=삼성&market=KOSPI&page=1&size=50
GET  /api/stocks/{stock_code}/prices?limit=100
GET  /api/stocks/{stock_code}/financials
GET  /api/stocks/{stock_code}/evaluation
GET  /api/stocks/rankings?is_candidate=1&page=1&size=15
POST /api/stocks/sync-prices
```

`POST /api/stocks/sync-prices`는 최근 1년 중 누락된 거래일을 최대 15일씩 동기화하고, 가능한 경우 최신 재무 데이터 기준으로 평가 점수도 다시 계산합니다.

## 5. 프론트엔드 실행

새 터미널에서 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

기본 주소:

```text
http://localhost:5173
```

프론트엔드는 기본적으로 `http://localhost:8000`의 백엔드 API를 호출합니다. 백엔드를 먼저 실행해 두면 실제 DB 데이터를 볼 수 있고, 일부 화면은 백엔드 응답이 없을 때 목업 데이터로 표시됩니다.

## 6. 전체 실행 예시

처음 실행할 때는 아래 순서로 진행하면 됩니다.

```powershell
# 1) 백엔드 준비
cd backend
uv sync --dev
Copy-Item .env.example .env
# backend/.env에 DART_API_KEY, KRX_API_KEY 입력
uv run python scripts/init_db.py

# 2) 종목/기업 코드 수집 및 정제
uv run python scripts/fetch_krx_listed_stocks.py
uv run python scripts/clean_krx_listed_stocks.py
uv run python scripts/fetch_dart_corp_codes.py
uv run python scripts/clean_dart_corp_codes.py

# 3) 재무/배당 데이터 수집 및 정제
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/clean_dart_financial_statements.py --business-year 2025 --report-code 11011
uv run python scripts/clean_dart_dividends.py --business-year 2025 --report-code 11011

# 4) DB 적재
uv run python scripts/sync_krx_listed_stocks_to_db.py
uv run python scripts/sync_financials_to_db.py
uv run python scripts/sync_krx_daily_prices_to_db.py --days 30

# 5) 백엔드 실행
uv run uvicorn pj_stock_backend.main:app --reload
```

프론트엔드는 별도 터미널에서 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

## 7. 테스트와 검사

백엔드 테스트:

```powershell
cd backend
uv run pytest
```

프론트엔드 린트:

```powershell
cd frontend
npm run lint
```

프론트엔드 빌드:

```powershell
cd frontend
npm run build
```

## 참고

- `data/raw/`, `data/processed/`, `.env`, SQLite DB 파일은 Git에 포함하지 않는 것이 좋습니다.
- DART 전체 수집은 시간이 오래 걸릴 수 있으므로 처음에는 `--limit 10`처럼 작은 값으로 테스트하세요.
- API 요청 실패가 잦으면 `--sleep-seconds` 값을 늘리세요.
- 이 프로젝트의 평가 결과는 투자 판단을 돕기 위한 데이터 분석 결과이며, 매수/매도 추천이 아닙니다.
