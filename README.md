# PJ Stock V2

국내 주식 시장에서 **저평가 배당주 후보**를 찾기 위한 데이터 수집/정제 프로젝트입니다.

현재 프로젝트는 KRX와 DART 데이터를 가져와 CSV로 저장하고, 후보 선별에 필요한 재무/배당/시세 데이터를 정제하는 단계까지 구현되어 있습니다. 최종 후보를 자동으로 점수화하고 랭킹으로 뽑는 전용 스크립트는 아직 없으므로, 지금은 정제된 CSV를 기준으로 PER, PBR, 배당수익률, 부채비율, 이익률 등을 조합해 후보를 분석하는 흐름으로 사용합니다.

## 프로젝트 구조

```text
pj_stock_v2/
├── backend/
│   ├── scripts/                 # 데이터 수집/정제 실행 스크립트
│   ├── src/pj_stock_backend/    # 수집기, 정제기, 저장소 코드
│   └── tests/                   # 테스트 코드
├── data/
│   ├── raw/                     # 원천 데이터 저장 위치, Git 제외
│   └── processed/               # 정제 데이터 저장 위치, Git 제외
├── docs/
├── frontend/                    # 아직 초기 상태
└── README.md
```

## 요구 사항

- Python 3.14 이상
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- KRX Open API 인증키
- DART Open API 인증키

## 설치

```powershell
cd backend
uv sync --dev
```

## 환경 변수

`backend/.env` 파일을 만들고 API 키를 설정합니다.

```env
APP_NAME=PJ Stock Backend
ENVIRONMENT=local
DATABASE_URL=sqlite:///../data/app.db
DART_API_KEY=발급받은_DART_API_KEY
KRX_API_KEY=발급받은_KRX_API_KEY
```

`DART_API_KEY`가 없으면 DART 기업 코드, 재무제표, 배당 정보 수집이 실패합니다. `KRX_API_KEY`가 없으면 KRX 상장 종목과 일별 시세 수집이 실패합니다.

## 저평가 배당주 후보 추출 플로우

모든 명령은 `backend` 디렉터리에서 실행합니다. 스크립트 내부 경로가 `../data/...` 기준으로 작성되어 있으므로, 다른 위치에서 실행하면 파일 저장 위치가 예상과 달라질 수 있습니다.

전체 흐름은 다음 순서로 진행합니다.

```text
1. KRX 상장 종목 수집
2. KRX 일별 시세 수집
3. DART 기업 코드 수집
4. DART 기업 코드 정제
5. DART 재무제표 수집
6. DART 배당 정보 수집
7. KRX/DART 원천 데이터 정제
8. 정제 CSV를 조합해 저평가 배당주 후보 필터링
```

## 1. KRX 상장 종목 수집

```powershell
uv run python scripts/fetch_krx_listed_stocks.py
```

수집 대상:

- KOSPI
- KOSDAQ

현재 기준일은 스크립트 안에 `20260512`로 고정되어 있습니다.

생성 파일:

```text
../data/raw/krx/listed_stocks_20260512_KOSPI.csv
../data/raw/krx/listed_stocks_20260512_KOSDAQ.csv
```

이 데이터는 종목 코드, 종목명, 시장 구분, 섹터, 상장 주식 수 등을 확인하는 데 사용합니다.

## 2. KRX 일별 시세 수집

```powershell
uv run python scripts/fetch_krx_daily_prices.py
```

수집 대상:

- KOSPI
- KOSDAQ

현재 기준일은 스크립트 안에 `20260512`로 고정되어 있습니다.

생성 파일:

```text
../data/raw/krx/daily_prices_20260512_KOSPI.csv
../data/raw/krx/daily_prices_20260512_KOSDAQ.csv
```

이 데이터는 현재가, 등락률, 거래량, 거래대금, 시가총액, 상장 주식 수를 확인하는 데 사용합니다. 저평가 여부를 계산할 때 시가총액과 현재가가 핵심 입력값이 됩니다.

## 3. DART 기업 코드 수집

```powershell
uv run python scripts/fetch_dart_corp_codes.py
```

생성 파일:

```text
../data/raw/dart/corp_codes.csv
```

DART API는 회사별 `corp_code`를 기준으로 재무제표와 배당 정보를 조회합니다. 이 파일은 KRX 종목 코드와 DART 회사 코드를 연결하기 위한 기본 데이터입니다.

## 4. DART 기업 코드 정제

```powershell
uv run python scripts/clean_dart_corp_codes.py
```

입력 파일:

```text
../data/raw/dart/corp_codes.csv
```

생성 파일:

```text
../data/processed/dart_corp_codes.csv
```

재무제표와 배당 정보를 여러 기업에 대해 반복 수집하려면 이 정제 파일이 먼저 필요합니다.

## 5. DART 재무제표 수집

```powershell
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 5 --sleep-seconds 0.2
```

입력 파일:

```text
../data/processed/dart_corp_codes.csv
```

생성 파일:

```text
../data/raw/dart/financial_statements_2025_11011.csv
```

### 재무제표 수집 인자

`--business-year`

조회할 사업연도입니다. 기본값은 `2025`입니다.

예를 들어 2024년 사업보고서 기준으로 후보를 보고 싶다면 다음처럼 실행합니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --business-year 2024
```

`--report-code`

DART 보고서 코드입니다. 기본값은 `11011`입니다.

자주 쓰는 값은 다음과 같습니다.

```text
11013: 1분기보고서
11012: 반기보고서
11014: 3분기보고서
11011: 사업보고서
```

저평가 배당주 후보를 안정적으로 뽑을 때는 보통 연간 실적이 담긴 `11011` 사업보고서를 먼저 사용합니다. 분기 데이터를 보고 싶다면 `11013`, `11012`, `11014`를 사용할 수 있지만, 배당 정보와 결산 기준이 맞지 않을 수 있으므로 비교 기준을 조심해야 합니다.

`--limit`

수집할 기업 수입니다. 기본값은 `5`입니다.

처음 실행할 때는 API 응답과 파일 저장이 정상인지 확인하기 위해 작은 값으로 테스트하는 것이 좋습니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --limit 10
```

전체 기업을 수집하려면 `0`을 사용합니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --limit 0
```

전체 수집은 오래 걸리고 DART 호출 제한에 영향을 받을 수 있습니다. 이미 저장된 파일이 있으면 스크립트가 기존 파일을 읽고 수집 완료된 종목은 건너뛰므로, 중간에 끊겨도 다시 실행할 수 있습니다.

`--sleep-seconds`

기업별 API 요청 사이에 기다릴 시간입니다. 기본값은 `0.2`초입니다.

요청 실패가 잦거나 호출 제한이 걱정되면 값을 늘립니다.

```powershell
uv run python scripts/fetch_dart_financial_statements.py --limit 0 --sleep-seconds 1
```

## 6. DART 배당 정보 수집

```powershell
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 5 --sleep-seconds 0.2
```

입력 파일:

```text
../data/processed/dart_corp_codes.csv
```

생성 파일:

```text
../data/raw/dart/dividends_2025_11011.csv
```

### 배당 정보 수집 인자

`--business-year`

조회할 사업연도입니다. 기본값은 `2025`입니다.

재무제표와 같은 연도를 사용하는 것이 좋습니다. 예를 들어 재무제표를 `2024`년으로 수집했다면 배당 정보도 `--business-year 2024`로 맞춥니다.

`--report-code`

DART 보고서 코드입니다. 기본값은 `11011`입니다.

배당 정보는 결산 기준 데이터가 중요하므로 보통 사업보고서인 `11011`을 사용합니다.

`--limit`

수집할 기업 수입니다. 기본값은 `5`입니다.

테스트 실행:

```powershell
uv run python scripts/fetch_dart_dividends.py --limit 10
```

전체 실행:

```powershell
uv run python scripts/fetch_dart_dividends.py --limit 0
```

`--sleep-seconds`

기업별 API 요청 사이의 대기 시간입니다. 기본값은 `0.2`초입니다.

전체 수집 시에는 호출 제한을 피하기 위해 값을 늘리는 것을 권장합니다.

```powershell
uv run python scripts/fetch_dart_dividends.py --limit 0 --sleep-seconds 1
```

## 7. 수집 데이터 정제

원천 데이터를 수집한 뒤 아래 정제 스크립트를 실행합니다.

```powershell
uv run python scripts/clean_krx_listed_stocks.py
uv run python scripts/clean_krx_daily_prices.py
uv run python scripts/clean_dart_financial_statements.py
uv run python scripts/clean_dart_dividends.py
```

생성 파일 예시:

```text
../data/processed/stocks.csv
../data/processed/daily_prices_20260512.csv
../data/processed/financial_statements_2025_11011.csv
../data/processed/dividends_2025_11011.csv
```

정제 후 주요 컬럼은 다음과 같습니다.

`daily_prices_20260512.csv`

- `stock_code`: 종목 코드
- `stock_name`: 종목명
- `market`: 시장 구분
- `close_price`: 종가
- `market_cap`: 시가총액
- `listed_shares`: 상장 주식 수
- `trading_value`: 거래대금

`financial_statements_2025_11011.csv`

- `stock_code`: 종목 코드
- `fiscal_period`: 결산 기간
- `total_assets`: 자산총계
- `total_liabilities`: 부채총계
- `total_equity`: 자본총계
- `revenue`: 매출액
- `operating_income`: 영업이익
- `net_income`: 당기순이익
- `debt_ratio`: 부채비율
- `current_ratio`: 유동비율
- `equity_ratio`: 자기자본비율
- `operating_margin`: 영업이익률
- `net_margin`: 순이익률

`dividends_2025_11011.csv`

- `corp_code`: DART 기업 코드
- `corp_name`: 기업명
- `fiscal_year`: 배당 기준 연도
- `eps`: 주당순이익
- `cash_dividend_yield`: 현금배당수익률
- `cash_dividend_per_share`: 주당 현금배당금
- `cash_dividend_payout_ratio`: 현금배당성향
- `cash_dividend_per_eps_ratio`: 주당배당금/EPS 비율

## 8. 후보 선별 기준

현재 자동 랭킹 스크립트는 없지만, 정제 CSV를 조합해 아래 기준으로 저평가 배당주 후보를 뽑을 수 있습니다.

### 기본 조인 키

- KRX 시세 데이터와 재무제표: `stock_code`
- DART 배당 데이터와 기업 코드: `corp_code`
- DART 기업 코드와 KRX 종목: `stock_code`

### 추천 필터 순서

1. 보통주 중심으로 필터링
2. 거래대금이 너무 낮은 종목 제외
3. 순이익이 양수인 기업만 유지
4. 자본총계가 양수인 기업만 유지
5. 배당수익률이 있는 기업만 유지
6. 부채비율이 과도하게 높은 기업 제외
7. PER, PBR, 배당수익률 기준으로 후보 정렬

### 계산 지표

PER:

```text
PER = 시가총액 / 당기순이익
```

PBR:

```text
PBR = 시가총액 / 자본총계
```

배당수익률:

```text
배당수익률 = DART cash_dividend_yield
```

배당성향:

```text
배당성향 = DART cash_dividend_payout_ratio
```

재무 안정성:

```text
부채비율 = total_liabilities / total_equity * 100
```

### 예시 후보 조건

아래 조건은 출발점으로 사용할 수 있는 예시입니다.

```text
net_income > 0
total_equity > 0
market_cap > 0
PER <= 10
PBR <= 1
cash_dividend_yield >= 3
debt_ratio <= 150
trading_value >= 1,000,000,000
```

조건을 너무 강하게 잡으면 후보가 거의 나오지 않을 수 있습니다. 처음에는 느슨하게 시작한 뒤, 업종별 특성과 경기 민감도를 보면서 조정하는 것이 좋습니다.

## 전체 실행 예시

소량 테스트:

```powershell
cd backend
uv sync --dev

# backend/.env 작성 후
uv run python scripts/fetch_krx_listed_stocks.py
uv run python scripts/fetch_krx_daily_prices.py
uv run python scripts/fetch_dart_corp_codes.py
uv run python scripts/clean_dart_corp_codes.py
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 10 --sleep-seconds 0.5
uv run python scripts/clean_krx_listed_stocks.py
uv run python scripts/clean_krx_daily_prices.py
uv run python scripts/clean_dart_financial_statements.py
uv run python scripts/clean_dart_dividends.py
```

전체 수집:

```powershell
uv run python scripts/fetch_dart_financial_statements.py --business-year 2025 --report-code 11011 --limit 0 --sleep-seconds 1
uv run python scripts/fetch_dart_dividends.py --business-year 2025 --report-code 11011 --limit 0 --sleep-seconds 1
```

## 테스트

```powershell
cd backend
uv run pytest
```

## 개발 참고

- `data/raw/`, `data/processed/`, `.env`, SQLite DB 파일은 Git에 포함되지 않습니다.
- KRX 수집 스크립트의 기준일은 현재 코드에 고정되어 있습니다.
- DART 수집 스크립트는 기존 결과 파일이 있으면 이어받기 방식으로 동작합니다.
- 최종 후보 자동 산출 스크립트는 아직 구현 전입니다.
- 이 프로젝트의 결과는 투자 판단을 돕기 위한 데이터 후보군이며, 매수/매도 추천이 아닙니다.
