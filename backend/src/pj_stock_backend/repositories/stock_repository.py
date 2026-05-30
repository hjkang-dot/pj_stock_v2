import sqlite3
import pandas as pd

STOCK_COLUMNS = [
    "stock_code",
    "stock_name",
    "market",
    "security_group",
    "sector",
    "dart_corp_code",
    "listed_date",
    "listed_shares",
    "is_active",
]


def upsert_stocks(
    connection: sqlite3.Connection,
    stocks: pd.DataFrame,
) -> int:
    """Insert or update stock details in the database."""
    if stocks.empty:
        return 0

    df = stocks.copy()
    
    # Map CSV column names to DB column names if necessary
    # stocks.csv headers: ['ISU_SRT_CD', 'ISU_ABBR_NM', 'MKT_NM', 'SECUGRP_NM', 'SECT_TP_NM', 'LIST_DD', 'LIST_SHRS']
    rename_map = {
        "ISU_SRT_CD": "stock_code",
        "ISU_ABBR_NM": "stock_name",
        "MKT_NM": "market",
        "SECUGRP_NM": "security_group",
        "SECT_TP_NM": "sector",
        "LIST_DD": "listed_date",
        "LIST_SHRS": "listed_shares",
    }
    df = df.rename(columns=rename_map)

    # Ensure all required columns exist
    for col in STOCK_COLUMNS:
        if col not in df.columns:
            if col == "is_active":
                df[col] = 1
            else:
                df[col] = None

    # Cast listed_shares to numeric, handle NaN
    if "listed_shares" in df.columns:
        df["listed_shares"] = pd.to_numeric(df["listed_shares"], errors="coerce").fillna(0).astype("int64")

    rows = df[STOCK_COLUMNS].to_dict("records")
    connection.executemany(
        """
        insert into stocks (
            stock_code,
            stock_name,
            market,
            security_group,
            sector,
            dart_corp_code,
            listed_date,
            listed_shares,
            is_active
        )
        values (
            :stock_code,
            :stock_name,
            :market,
            :security_group,
            :sector,
            :dart_corp_code,
            :listed_date,
            :listed_shares,
            :is_active
        )
        on conflict(stock_code) do update set
            stock_name = excluded.stock_name,
            market = excluded.market,
            security_group = excluded.security_group,
            sector = excluded.sector,
            dart_corp_code = excluded.dart_corp_code,
            listed_date = excluded.listed_date,
            listed_shares = excluded.listed_shares,
            is_active = excluded.is_active,
            last_synced_at = current_timestamp,
            updated_at = current_timestamp
        """,
        rows,
    )
    connection.commit()

    return len(rows)


def get_stocks(
    connection: sqlite3.Connection,
    *,
    market: str | None = None,
    is_active: int | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """Retrieve stocks with filtering, search, and pagination."""
    conditions = []
    params = {}

    if market is not None:
        conditions.append("market = :market")
        params["market"] = market
    if is_active is not None:
        conditions.append("is_active = :is_active")
        params["is_active"] = is_active
    if search is not None and search.strip() != "":
        conditions.append("(stock_code like :search or stock_name like :search or sector like :search)")
        params["search"] = f"%{search}%"

    where_clause = ""
    if conditions:
        where_clause = "where " + " and ".join(conditions)

    query = f"""
        select {", ".join(STOCK_COLUMNS)}
        from stocks
        {where_clause}
        order by stock_name
        limit :limit offset :offset
    """
    params["limit"] = limit
    params["offset"] = offset

    return pd.read_sql_query(query, connection, params=params)


def count_stocks(
    connection: sqlite3.Connection,
    *,
    market: str | None = None,
    is_active: int | None = None,
    search: str | None = None,
) -> int:
    """Count the total number of stocks matching the filter conditions."""
    conditions = []
    params = {}

    if market is not None:
        conditions.append("market = :market")
        params["market"] = market
    if is_active is not None:
        conditions.append("is_active = :is_active")
        params["is_active"] = is_active
    if search is not None and search.strip() != "":
        conditions.append("(stock_code like :search or stock_name like :search or sector like :search)")
        params["search"] = f"%{search}%"

    where_clause = ""
    if conditions:
        where_clause = "where " + " and ".join(conditions)

    cursor = connection.cursor()
    cursor.execute(
        f"select count(*) from stocks {where_clause}",
        params
    )
    result = cursor.fetchone()
    return result[0] if result else 0


def get_company_financials(
    connection: sqlite3.Connection,
    stock_code: str,
) -> pd.DataFrame:
    """Retrieve financial history for a specific stock code ordered by fiscal period."""
    query = """
        select *
        from company_financials
        where stock_code = :stock_code
        order by fiscal_period
    """
    return pd.read_sql_query(query, connection, params={"stock_code": stock_code})


def upsert_stock_evaluations(
    connection: sqlite3.Connection,
    evaluations: pd.DataFrame,
) -> int:
    """Insert or update strategy evaluations for all stocks."""
    if evaluations.empty:
        return 0

    rows = evaluations.to_dict("records")
    cleaned_rows = []
    for r in rows:
        cleaned = {}
        for k, v in r.items():
            if pd.isna(v):
                cleaned[k] = None
            else:
                cleaned[k] = v
        cleaned_rows.append(cleaned)

    cursor = connection.cursor()
    cursor.executemany(
        """
        insert into stock_evaluations (
            stock_code, business_year, base_date, close_price, market_cap, net_income,
            total_equity, debt_ratio, current_ratio, roe, per, pbr, dividend_yield, cash_dividend_per_share,
            payout_ratio, dividend_years, dividend_decrease_count, revenue_growth, operating_income_growth, eps_growth,
            financial_stability_score, growth_score, undervaluation_score, shareholder_return_score,
            market_governance_score, total_score, is_candidate
        )
        values (
            :stock_code, :business_year, :base_date, :close_price, :market_cap, :net_income,
            :total_equity, :debt_ratio, :current_ratio, :roe, :per, :pbr, :dividend_yield, :cash_dividend_per_share,
            :payout_ratio, :dividend_years, :dividend_decrease_count, :revenue_growth, :operating_income_growth, :eps_growth,
            :financial_stability_score, :growth_score, :undervaluation_score, :shareholder_return_score,
            :market_governance_score, :total_score, :is_candidate
        )
        on conflict(stock_code, business_year, base_date) do update set
            close_price = excluded.close_price,
            market_cap = excluded.market_cap,
            net_income = excluded.net_income,
            total_equity = excluded.total_equity,
            debt_ratio = excluded.debt_ratio,
            current_ratio = excluded.current_ratio,
            roe = excluded.roe,
            per = excluded.per,
            pbr = excluded.pbr,
            dividend_yield = excluded.dividend_yield,
            cash_dividend_per_share = excluded.cash_dividend_per_share,
            payout_ratio = excluded.payout_ratio,
            dividend_years = excluded.dividend_years,
            dividend_decrease_count = excluded.dividend_decrease_count,
            revenue_growth = excluded.revenue_growth,
            operating_income_growth = excluded.operating_income_growth,
            eps_growth = excluded.eps_growth,
            financial_stability_score = excluded.financial_stability_score,
            growth_score = excluded.growth_score,
            undervaluation_score = excluded.undervaluation_score,
            shareholder_return_score = excluded.shareholder_return_score,
            market_governance_score = excluded.market_governance_score,
            total_score = excluded.total_score,
            is_candidate = excluded.is_candidate,
            updated_at = current_timestamp
        """,
        cleaned_rows
    )
    connection.commit()
    return len(cleaned_rows)


def get_latest_stock_evaluation(
    connection: sqlite3.Connection,
    stock_code: str,
) -> dict | None:
    """Fetch the latest evaluation details for a given stock code."""
    cursor = connection.cursor()
    cursor.execute(
        """
        select *
        from stock_evaluations
        where stock_code = :stock_code
        order by base_date desc, business_year desc
        limit 1
        """,
        {"stock_code": stock_code}
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def get_evaluated_stocks(
    connection: sqlite3.Connection,
    *,
    market: str | None = None,
    is_candidate: int | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """Retrieve active stocks joined with their latest evaluation, sorted by total_score descending."""
    conditions = ["s.is_active = 1", "e.rn = 1"]
    params = {}

    if market is not None:
        conditions.append("s.market = :market")
        params["market"] = market
    if is_candidate is not None:
        conditions.append("e.is_candidate = :is_candidate")
        params["is_candidate"] = is_candidate
    if search is not None and search.strip() != "":
        conditions.append("(s.stock_code like :search or s.stock_name like :search or s.sector like :search)")
        params["search"] = f"%{search}%"

    where_clause = "where " + " and ".join(conditions)

    query = f"""
        with latest_eval as (
            select *,
                   row_number() over (partition by stock_code order by base_date desc, business_year desc) as rn
            from stock_evaluations
        )
        select s.stock_code, s.stock_name, s.market, s.sector,
               e.business_year, e.base_date, e.close_price, e.market_cap,
               e.roe, e.per, e.pbr, e.dividend_yield, e.dividend_years,
               e.current_ratio, e.revenue_growth, e.operating_income_growth, e.eps_growth,
               e.financial_stability_score, e.growth_score, e.undervaluation_score,
               e.shareholder_return_score, e.market_governance_score,
               e.total_score, e.is_candidate
        from stocks s
        join latest_eval e on s.stock_code = e.stock_code
        {where_clause}
        order by e.total_score desc, s.stock_name asc
        limit :limit offset :offset
    """
    params["limit"] = limit
    params["offset"] = offset

    return pd.read_sql_query(query, connection, params=params)


def count_evaluated_stocks(
    connection: sqlite3.Connection,
    *,
    market: str | None = None,
    is_candidate: int | None = None,
    search: str | None = None,
) -> int:
    """Count the total number of evaluated stocks matching the filter conditions."""
    conditions = ["s.is_active = 1", "e.rn = 1"]
    params = {}

    if market is not None:
        conditions.append("s.market = :market")
        params["market"] = market
    if is_candidate is not None:
        conditions.append("e.is_candidate = :is_candidate")
        params["is_candidate"] = is_candidate
    if search is not None and search.strip() != "":
        conditions.append("(s.stock_code like :search or s.stock_name like :search or s.sector like :search)")
        params["search"] = f"%{search}%"

    where_clause = "where " + " and ".join(conditions)

    query = f"""
        with latest_eval as (
            select stock_code,
                   row_number() over (partition by stock_code order by base_date desc, business_year desc) as rn
            from stock_evaluations
        )
        select count(*)
        from stocks s
        join latest_eval e on s.stock_code = e.stock_code
        {where_clause}
    """
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    return result[0] if result else 0

