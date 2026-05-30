from pathlib import Path
import sqlite3
import pandas as pd

from pj_stock_backend.repositories import stock_repository, daily_price_repository
from pj_stock_backend.storage.csv_storage import load_dataframe_csv
from pj_stock_backend.strategies.undervalued_dividend_strategy import screen_undervalued_dividend_stocks


def run_stock_evaluation_pipeline(
    connection: sqlite3.Connection,
    *,
    business_year: int,
    base_date: str,
) -> int:
    """Run undervalued dividend scoring for all stocks based on a specific base_date and business_year, saving results to SQLite."""
    print(f"[eval_pipeline] Starting evaluation for Year {business_year} as of Date {base_date}...")
    
    # 1. Resolve project paths
    curr = Path(__file__).resolve()
    base_dir = None
    for p in curr.parents:
        if p.name == "pj_stock_v2":
            base_dir = p
            break
    if base_dir is None:
        base_dir = curr.parents[4]
        
    processed_dir = base_dir / "data" / "processed"
    
    fin_paths = [processed_dir / f"financial_statements_{y}_11011.csv" for y in [business_year, business_year - 1]]
    div_paths = [processed_dir / f"dividends_{y}_11011.csv" for y in [business_year, business_year - 1]]
    
    # Base files for the target business_year must exist
    if not fin_paths[0].exists() or not div_paths[0].exists():
        print(f"[eval_pipeline] Error: CSV files for Year {business_year} do not exist in processed directory: {processed_dir}")
        return 0
        
    fin_dfs = []
    div_dfs = []
    for p in fin_paths:
        if p.exists():
            fin_dfs.append(load_dataframe_csv(str(p), dtype={"corp_code": str, "stock_code": str}))
    for p in div_paths:
        if p.exists():
            div_dfs.append(load_dataframe_csv(str(p), dtype={"corp_code": str, "stock_code": str}))
            
    financial_statements = pd.concat(fin_dfs, ignore_index=True) if fin_dfs else pd.DataFrame()
    dividends = pd.concat(div_dfs, ignore_index=True) if div_dfs else pd.DataFrame()

    # Normalize corp_code to 8 digits (DART API can omit leading zeros in some endpoints)
    if not financial_statements.empty:
        financial_statements["corp_code"] = financial_statements["corp_code"].astype(str).str.strip().str.zfill(8)
    if not dividends.empty:
        dividends["corp_code"] = dividends["corp_code"].astype(str).str.strip().str.zfill(8)
    
    # 2. Get daily prices for base_date from DB
    daily_prices = daily_price_repository.get_daily_prices(
        connection,
        start_date=base_date,
        end_date=base_date
    )
    
    if daily_prices.empty:
        print(f"[eval_pipeline] Error: No daily prices found in DB for Date {base_date}.")
        return 0
        
    # 3. Load stocks from DB
    stocks_df = pd.read_sql_query(
        "select stock_code, stock_name, market, sector, listed_date from stocks where is_active = 1",
        connection
    )
    
    if stocks_df.empty:
        print("[eval_pipeline] Error: No active stocks found in DB.")
        return 0
        
    # 4. Run strategy calculations
    screened = screen_undervalued_dividend_stocks(
        financial_statements=financial_statements,
        dividends=dividends,
        daily_prices=daily_prices,
        stocks=stocks_df,
        as_of_year=business_year
    )
    
    if screened.empty:
        print("[eval_pipeline] Warning: Strategy output is empty.")
        return 0
        
    # Add business_year and base_date columns before saving
    screened["business_year"] = business_year
    screened["base_date"] = base_date
    
    # Map boolean to integer for SQLite compatibility
    screened["is_candidate"] = screened["is_candidate"].astype(int)
    
    # 5. Insert into DB
    count = stock_repository.upsert_stock_evaluations(connection, screened)
    print(f"[eval_pipeline] Successfully upserted {count} stock evaluations.")
    return count
