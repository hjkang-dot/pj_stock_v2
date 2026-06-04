import math
import random
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from pj_stock_backend.db.sqlite import get_db, reset_company_financials_table
from pj_stock_backend.repositories import stock_repository, daily_price_repository
from pj_stock_backend.pipelines.krx_daily_price_pipeline import run_krx_daily_price_db_sync

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class StockItem(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    security_group: str | None = None
    sector: str | None = None
    dart_corp_code: str | None = None
    listed_date: str | None = None
    listed_shares: int | None = None
    is_active: int


class StockListResponse(BaseModel):
    items: list[StockItem]
    total: int
    page: int
    size: int
    pages: int


class ResetDatabaseResponse(BaseModel):
    status: str
    message: str
    database_path: str


class SyncFinancialsResponse(BaseModel):
    status: str
    message: str
    business_year: str
    report_code: str
    limit: int
    output: str


@router.post("/reset-db", response_model=ResetDatabaseResponse)
def reset_stock_database() -> Any:
    """Drop and recreate only the company_financials table."""
    database_path = reset_company_financials_table()

    return {
        "status": "success",
        "message": "company_financials table has been reset.",
        "database_path": str(database_path),
    }


@router.post("/sync-financials", response_model=SyncFinancialsResponse)
def sync_company_financials(
    business_year: str = Query("2025", description="DART business year"),
    report_code: str = Query("11011", description="DART report code"),
    limit: int = Query(10, ge=0, description="Number of companies to collect. 0 means all."),
    sleep_seconds: float = Query(0.5, ge=0, description="Delay between DART API calls"),
) -> Any:
    """Collect DART financial/dividend data, clean CSVs, and sync company_financials."""
    backend_dir = Path(__file__).resolve().parents[3]
    commands = [
        [
            sys.executable,
            "scripts/fetch_dart_financial_statements.py",
            "--business-year",
            business_year,
            "--report-code",
            report_code,
            "--limit",
            str(limit),
            "--sleep-seconds",
            str(sleep_seconds),
        ],
        [
            sys.executable,
            "scripts/fetch_dart_dividends.py",
            "--business-year",
            business_year,
            "--report-code",
            report_code,
            "--limit",
            str(limit),
            "--sleep-seconds",
            str(sleep_seconds),
        ],
        [
            sys.executable,
            "scripts/clean_dart_financial_statements.py",
            "--business-year",
            business_year,
            "--report-code",
            report_code,
        ],
        [
            sys.executable,
            "scripts/clean_dart_dividends.py",
            "--business-year",
            business_year,
            "--report-code",
            report_code,
        ],
        [
            sys.executable,
            "scripts/sync_financials_to_db.py",
            "--business-year",
            business_year,
            "--report-code",
            report_code,
        ],
    ]

    logs = []
    for command in commands:
        logs.append(f"$ {' '.join(command)}")
        try:
            completed = subprocess.run(
                command,
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=60 * 60,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            output = "\n".join([*logs, str(error)])[-8000:]
            print(output)
            raise HTTPException(
                status_code=504,
                detail={
                    "message": "company_financials sync timed out.",
                    "output": output,
                },
            ) from error

        if completed.stdout:
            logs.append(completed.stdout)
        if completed.stderr:
            logs.append(completed.stderr)
        if completed.returncode != 0:
            output = "\n".join(logs)[-8000:]
            print(output)
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Failed to sync company_financials.",
                    "business_year": business_year,
                    "report_code": report_code,
                    "limit": limit,
                    "output": output,
                },
            )

    return {
        "status": "success",
        "message": "company_financials has been collected and synced.",
        "business_year": business_year,
        "report_code": report_code,
        "limit": limit,
        "output": "\n".join(logs)[-8000:],
    }


@router.get("", response_model=StockListResponse)
def list_stocks(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search query for stock code, name, or sector"),
    market: str | None = Query(None, description="Filter by market (e.g. KOSPI, KOSDAQ)"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve a list of KOSPI/KOSDAQ stocks with pagination and search."""
    offset = (page - 1) * size

    # Fetch total matching count
    total = stock_repository.count_stocks(
        db,
        market=market,
        is_active=1,
        search=search,
    )

    # Fetch paginated rows
    stocks_df = stock_repository.get_stocks(
        db,
        market=market,
        is_active=1,
        search=search,
        limit=size,
        offset=offset,
    )

    import pandas as pd
    raw_items = stocks_df.to_dict("records")
    items = []
    for item in raw_items:
        # Replaces NaN (float) values with Python None to satisfy Pydantic validators
        cleaned = {k: (None if pd.isna(v) else v) for k, v in item.items()}
        items.append(cleaned)
    pages = math.ceil(total / size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


class FinancialReportItem(BaseModel):
    corp_code: str
    stock_code: str | None
    bsns_year: int
    fs_div: str | None
    fs_nm: str | None
    currency: str | None
    fiscal_period: str | None
    current_assets: float | None
    non_current_assets: float | None
    total_assets: float | None
    current_liabilities: float | None
    non_current_liabilities: float | None
    total_liabilities: float | None
    total_equity: float | None
    revenue: float | None
    operating_income: float | None
    net_income: float | None
    debt_ratio: float | None
    current_ratio: float | None
    equity_ratio: float | None
    operating_margin: float | None
    net_margin: float | None
    par_value: float | None
    eps: float | None
    cash_dividend_yield: float | None
    cash_dividend_per_share: float | None
    cash_dividend_total: float | None
    cash_dividend_payout_ratio: float | None


@router.get("/{stock_code}/financials", response_model=list[FinancialReportItem])
def get_stock_financials(
    stock_code: str,
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Get all annual financial reports and dividend history for a specific stock."""
    df = stock_repository.get_company_financials(db, stock_code)
    
    # Replace NaN values with None for proper Pydantic serialization
    import pandas as pd
    df = df.where(pd.notnull(df), None)
    
    return df.to_dict("records")
class DailyPriceItem(BaseModel):
    trade_date: str
    stock_code: str
    stock_name: str
    market: str
    section: str | None = None
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    price_change: int
    change_rate: float
    volume: int
    trading_value: int | None = None
    market_cap: int | None = None
    listed_shares: int | None = None


def generate_mock_prices(stock_code: str, limit: int) -> list[dict[str, Any]]:
    # Simple deterministic random based on stock_code to keep mock values consistent
    seed_val = sum(ord(c) for c in stock_code)
    rng = random.Random(seed_val)
    
    # Start price around 10,000 to 100,000
    base_price = rng.randint(100, 1000) * 100
    
    # Generate business days (skipping weekends)
    dates = []
    curr_date = datetime.now()
    while len(dates) < limit:
        if curr_date.weekday() < 5:
            dates.append(curr_date.strftime("%Y%m%d"))
        curr_date -= timedelta(days=1)
        
    dates.reverse() # Sort chronologically
    
    mock_list = []
    last_close = base_price
    for d in dates:
        # random walk change (-3.5% to +3.5%)
        change_pct = rng.uniform(-0.035, 0.035)
        close_price = int(last_close * (1 + change_pct))
        # Round close to nearest 10 won or 100 won for KRW aesthetic
        if close_price > 1000:
            close_price = (close_price // 50) * 50
        
        open_price = int(last_close)
        if open_price > 1000:
            open_price = (open_price // 50) * 50
            
        high_price = int(max(open_price, close_price) * (1 + rng.uniform(0, 0.025)))
        low_price = int(min(open_price, close_price) * (1 - rng.uniform(0, 0.025)))
        
        if open_price > 1000:
            high_price = (high_price // 50) * 50
            low_price = (low_price // 50) * 50
        
        # ensure sanity
        if low_price > open_price or low_price > close_price:
            low_price = min(open_price, close_price)
        if high_price < open_price or high_price < close_price:
            high_price = max(open_price, close_price)
            
        volume = rng.randint(50000, 1500000)
        price_change = close_price - open_price
        change_rate = (price_change / open_price) * 100 if open_price > 0 else 0
        
        mock_list.append({
            "trade_date": d,
            "stock_code": stock_code,
            "stock_name": f"Mock {stock_code}",
            "market": "MOCK",
            "section": "Mock Section",
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "price_change": price_change,
            "change_rate": round(change_rate, 2),
            "volume": volume,
            "trading_value": volume * close_price,
            "market_cap": volume * close_price * 10,
            "listed_shares": volume * 10
        })
        last_close = close_price
        
    return mock_list


@router.get("/{stock_code}/prices", response_model=list[DailyPriceItem])
def get_stock_prices(
    stock_code: str,
    limit: int = Query(100, ge=1, le=500, description="Number of trading days to retrieve"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Get historical daily prices for a stock code to plot candle chart."""
    normalized_code = stock_code.zfill(6)
    
    # Try fetching from DB
    df = daily_price_repository.get_daily_prices(
        db,
        stock_code=normalized_code,
        limit=limit,
        descending=True
    )
    
    if df.empty:
        # Fallback to mock data generator
        return generate_mock_prices(normalized_code, limit)
        
    # Reverse to chronological order (asc)
    df = df.iloc[::-1]
    
    # Replace NaN values with None for proper Pydantic serialization
    import pandas as pd
    df = df.where(pd.notnull(df), None)
    
    return df.to_dict("records")


@router.post("/sync-prices")
def sync_stock_prices(
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Scan past 365 weekdays, identify missing date gaps, sync up to 15 missing days, and mark holidays/closed days."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    start_date = yesterday - timedelta(days=365)
    
    start_date_str = start_date.strftime("%Y%m%d")
    
    # 1. Generate all weekdays in past 365 days
    candidate_dates = []
    curr = start_date
    while curr <= yesterday:
        if curr.weekday() < 5: # Monday=0, Friday=4
            candidate_dates.append(curr.strftime("%Y%m%d"))
        curr += timedelta(days=1)
        
    candidate_set = set(candidate_dates)
    
    # 2. Query already synced dates and confirmed holiday dates
    existing_set = daily_price_repository.get_existing_trade_dates(db, start_date_str)
    closed_set = daily_price_repository.get_closed_market_dates(db, start_date_str)
    
    # 3. Find gap dates
    missing_dates = sorted(list(candidate_set - existing_set - closed_set))
    
    total_upserted = 0
    processed_dates = []
    remaining_count = 0
    
    if missing_dates:
        # 4. Cap batch to 15 days to prevent HTTP request timeouts
        BATCH_SIZE = 15
        dates_to_sync = missing_dates[:BATCH_SIZE]
        
        for d in dates_to_sync:
            print(f"Syncing daily prices for gap date: {d}...")
            try:
                upserted = run_krx_daily_price_db_sync(start_date=d, end_date=d)
                processed_dates.append(d)
                if upserted == 0:
                    # No records fetched means the market was officially closed/holiday. Mark it.
                    daily_price_repository.insert_closed_market_date(db, d)
                    print(f"Date {d} successfully marked as CLOSED/HOLIDAY.")
                else:
                    total_upserted += upserted
            except Exception as err:
                print(f"Failed to sync date {d}: {err}")
                return {
                    "status": "error",
                    "message": f"Failed on date {d}: {str(err)}",
                    "upserted_rows": total_upserted,
                    "processed_dates": processed_dates,
                    "remaining_missing_count": len(missing_dates) - len(processed_dates)
                }
        remaining_count = len(missing_dates) - len(processed_dates)

    if not processed_dates:
        message = "All weekdays in the past year are fully synced or verified closed."
    else:
        message = f"Successfully processed {len(processed_dates)} dates."
    
    return {
        "status": "success",
        "message": message,
        "upserted_rows": total_upserted,
        "processed_dates": processed_dates,
        "remaining_missing_count": remaining_count,
    }


@router.post("/evaluate")
def run_stock_evaluation(
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Run the investment scoring pipeline using the latest available price date and financial data."""
    import re
    from pathlib import Path
    from pj_stock_backend.pipelines.stock_evaluation_pipeline import run_stock_evaluation_pipeline

    # 1. Find the latest trade date in DB
    latest_base_date = daily_price_repository.get_latest_trade_date(db)
    if not latest_base_date:
        return {
            "status": "error",
            "message": "No daily price data found in DB. Please sync prices first.",
            "evaluation_rows": 0,
        }

    # 2. Scan processed directory for the latest financial statement year
    processed_dir = Path(__file__).resolve().parents[4] / "data" / "processed"
    csv_pattern = re.compile(r"^financial_statements_(\d{4})_11011\.csv$")
    years = []
    if processed_dir.exists():
        for p in processed_dir.glob("financial_statements_*_11011.csv"):
            m = csv_pattern.match(p.name)
            if m:
                years.append(int(m.group(1)))

    if not years:
        return {
            "status": "error",
            "message": "No processed financial statement CSV found. Please collect financial data first.",
            "evaluation_rows": 0,
        }

    latest_year = max(years)
    print(f"[evaluate] Running evaluation: year={latest_year}, base_date={latest_base_date}")

    try:
        eval_count = run_stock_evaluation_pipeline(
            db,
            business_year=latest_year,
            base_date=latest_base_date,
        )
    except Exception as err:
        print(f"[evaluate] Evaluation pipeline failed: {err}")
        return {
            "status": "error",
            "message": f"Evaluation pipeline failed: {str(err)}",
            "evaluation_rows": 0,
        }

    return {
        "status": "success",
        "message": f"Scored {eval_count} stocks based on {latest_year} financials as of {latest_base_date}.",
        "business_year": latest_year,
        "base_date": latest_base_date,
        "evaluation_rows": eval_count,
    }


class StockEvaluationItem(BaseModel):
    stock_code: str
    business_year: int
    base_date: str
    strategy_type: str | None = None
    close_price: int | None = None
    market_cap: int | None = None
    net_income: float | None = None
    total_equity: float | None = None
    debt_ratio: float | None = None
    current_ratio: float | None = None
    roe: float | None = None
    per: float | None = None
    pbr: float | None = None
    dividend_yield: float | None = None
    cash_dividend_per_share: float | None = None
    payout_ratio: float | None = None
    dividend_years: int | None = None
    dividend_decrease_count: int | None = None
    revenue_growth: float | None = None
    operating_income_growth: float | None = None
    eps_growth: float | None = None
    financial_stability_score: float | None = None
    growth_score: float | None = None
    undervaluation_score: float | None = None
    shareholder_return_score: float | None = None
    market_governance_score: float | None = None
    total_score: float | None = None
    is_candidate: int | None = None


@router.get("/{stock_code}/evaluation", response_model=StockEvaluationItem | None)
def get_stock_evaluation(
    stock_code: str,
    strategy_type: str = Query("DIVIDEND"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Get the latest investment strategy scores and valuation metrics for a stock and strategy."""
    normalized_code = stock_code.zfill(6)
    eval_dict = stock_repository.get_latest_stock_evaluation(db, normalized_code, strategy_type)
    
    if not eval_dict:
        return None
        
    import pandas as pd
    # Replace NaN values with None for proper Pydantic serialization
    cleaned = {k: (None if pd.isna(v) else v) for k, v in eval_dict.items()}
    return cleaned


class EvaluatedStockItem(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    sector: str | None = None
    business_year: int
    base_date: str
    close_price: int | None = None
    market_cap: int | None = None
    roe: float | None = None
    per: float | None = None
    pbr: float | None = None
    dividend_yield: float | None = None
    dividend_years: int | None = None
    current_ratio: float | None = None
    revenue_growth: float | None = None
    operating_income_growth: float | None = None
    eps_growth: float | None = None
    financial_stability_score: float | None = None
    growth_score: float | None = None
    undervaluation_score: float | None = None
    shareholder_return_score: float | None = None
    market_governance_score: float | None = None
    total_score: float | None = None
    is_candidate: int | None = None


class EvaluatedStockListResponse(BaseModel):
    items: list[EvaluatedStockItem]
    total: int
    page: int
    size: int
    pages: int


@router.get("/rankings", response_model=EvaluatedStockListResponse)
def list_evaluated_stock_rankings(
    strategy_type: str = Query("DIVIDEND"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(15, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search query for stock code, name, or sector"),
    market: str | None = Query(None, description="Filter by market (e.g. KOSPI, KOSDAQ)"),
    is_candidate: int | None = Query(None, description="Filter by candidate status (1 for candidate, 0 for not)"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve evaluated stocks sorted by total score descending with pagination and filters."""
    offset = (page - 1) * size

    total = stock_repository.count_evaluated_stocks(
        db,
        strategy_type=strategy_type,
        market=market,
        is_candidate=is_candidate,
        search=search,
    )

    df = stock_repository.get_evaluated_stocks(
        db,
        strategy_type=strategy_type,
        market=market,
        is_candidate=is_candidate,
        search=search,
        limit=size,
        offset=offset,
    )

    # Replace NaN values with None for proper Pydantic serialization
    import pandas as pd
    records = df.to_dict("records")
    cleaned_items = []
    for r in records:
        cleaned_items.append({k: (None if pd.isna(v) else v) for k, v in r.items()})

    pages = math.ceil(total / size) if total > 0 else 1

    return {
        "items": cleaned_items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
