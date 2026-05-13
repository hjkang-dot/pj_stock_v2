# 개발 일지

## 2026-05-13

### 오늘 결정한 것
- 백엔드는 python + uv + FastAPI로 구성
- 프론트엔드는 React로 구성
- DB는 SQLite로 구성

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

#### 데이터 수집

1. collectors 폴더 만들기
2. KRX 상장 종목 목록 가져오기 krx_collector.py

