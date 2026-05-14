# 개발 일지

## 2026-05-13

### 오늘 결정한 것
- 백엔드는 python + uv + FastAPI로 구성
- 프론트엔드는 React로 구성
- DB는 SQLite로 구성
- 초기 작업에는 csv로 데이터 관리

### 작업 내역

#### backend
1. 폴더 만들기 backend, frontend, data
2. gitignore 추가, README 추가
3. backend 폴더내에 가상환경 생성 및 uv 설치
4. fastapi, uvicorn, pandas, pydantic, pydantic-settings 설치
5. pytest, ruff 설치
6. fastapi 테스트 완료 
7. api, core 폴더 만들기
8. /health 라우터 파일 만들기
9. main.py에 라우터 연결
10. config 만들기
11. tests 폴더 만들기
12. /health 테스트 test_health.py
13. pytest 실행 uv run pytest
14. db 폴더 만들기
15. SQLite 연결 파일 만들기
16. SQLite 연결 테스트 만들기 test_sqlite.py
17. .env 파일, .env.example 파일 만들기
18. config.py에 setting 값 추가 dart_api_key, krx_api_key
19. schema 폴더 만들기
20. schema.sql 파일 만들기
- base_date       KRX 기준일
- stock_code      종목코드
- stock_name      종목명
- market          KOSPI / KOSDAQ
- security_group  주권/증권구분 등
- sector          업종/소속부 등
- listed_date     상장일
- listed_shares   상장주식수
21. 스키마 초기화 함수 만들기 initialize_database()
22. stocks 테이블 생성 init_db
23. test_sqlite.py에 initialize_database_creates_stocks_table 테스트 만들기
24. repository 폴더 만들기(CSV방식으로 변환)
25. stock_repository.py 파일 만들기(csv 방식으로 변환)


#### 데이터 수집 - 종목 목록 stocks.csv

1. collectors 폴더 만들기
2. KRX 상장 종목 목록 가져오기 krx_collector.py
- 수집된 컬럼 목록
'ISU_CD'(종목코드), 'ISU_SRT_CD'(단축종목코드), 'ISU_NM'(종목명), 'ISU_ABBRV'(종목약칭), 'ISU_ENG_NM'(종목영문명), 'LIST_DD'(상장일), 'MKT_TP_NM'(시장유형), 'SECUGRP_NM'(증권그룹명), 'SECT_TP_NM'(섹터명), 'KIND_STKCERT_TP_NM'(주식종류), 'PARVAL'(액면가), 'LIST_SHRS'(상장주식수)
3. 수집된 종목 목록 데이터 저장하기
4. storage 폴더 만들기
5. 수집 데이터 저장할 csv_storage.py 파일 만들기 
6. test_csv_storage.py 파일 만들기
7. fetch_krx_listed_stocks.py 로 data/raw/krx 폴더에 종목 목록 csv로 저장
8. 수집된 데이터 clean 하기 krx_stock_cleaner.py
9. test_krx_stock_cleaner.py 파일 만들기
10. clean_krx_listed_stocks.py 로 data/processed/stocks.csv 로 저장

#### 데이터 수집 - 주가 daily_prices_{date}.csv

1. krx_collector.py 내에 fetch_krx_daily_prices 만들기 
2. scripts 내에 fetch_krx_daily_prices.py 로 data/raw/krx/daily_prices_{base_date}_{market}.csv 로 저장
- 수집 목록
'BAS_DD'(기준일), 'ISU_CD'(종목코드), 'ISU_NM'(종목명), 'MKT_NM'(시장명), 'SECT_TP_NM'(섹터), 'TDD_CLSPRC'(종가), 'CMPPREVDD_PRC'(전일비), 'FLUC_RT'(등락률), 'TDD_OPNPRC'(시가), 'TDD_HGPRC'(고가), 'TDD_LWPRC'(저가), 'ACC_TRDVOL'(거래량), 'ACC_TRDVAL'(거래대금), 'MKTCAP'(시가총액), 'LIST_SHRS'(상장주식수)
3. clean 하기 krx_price_cleaner.py
4. test_krx_price_cleaner.py 파일 만들기
5. clean_krx_daily_prices.py 로 data/processed/daily_prices_{base_date}_{market}.csv 로 저장

#### 데이터 수집 - 재무제표