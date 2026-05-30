import sqlite3
import pandas as pd

STOCK_COLUMNS = [
    "stock_code",
    "stock_name",
    "market",
    "security_group",
    "sector",
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
            :listed_date,
            :listed_shares,
            :is_active
        )
        on conflict(stock_code) do update set
            stock_name = excluded.stock_name,
            market = excluded.market,
            security_group = excluded.security_group,
            sector = excluded.sector,
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
