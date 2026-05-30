import sqlite3

import pandas as pd


DAILY_PRICE_COLUMNS = [
    "trade_date",
    "stock_code",
    "stock_name",
    "market",
    "section",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "price_change",
    "change_rate",
    "volume",
    "trading_value",
    "market_cap",
    "listed_shares",
]


def upsert_daily_prices(
    connection: sqlite3.Connection,
    daily_prices: pd.DataFrame,
) -> int:
    if daily_prices.empty:
        return 0

    rows = daily_prices[DAILY_PRICE_COLUMNS].to_dict("records")
    connection.executemany(
        """
        insert into daily_prices (
            trade_date,
            stock_code,
            stock_name,
            market,
            section,
            open_price,
            high_price,
            low_price,
            close_price,
            price_change,
            change_rate,
            volume,
            trading_value,
            market_cap,
            listed_shares
        )
        values (
            :trade_date,
            :stock_code,
            :stock_name,
            :market,
            :section,
            :open_price,
            :high_price,
            :low_price,
            :close_price,
            :price_change,
            :change_rate,
            :volume,
            :trading_value,
            :market_cap,
            :listed_shares
        )
        on conflict(trade_date, stock_code) do update set
            stock_name = excluded.stock_name,
            market = excluded.market,
            section = excluded.section,
            open_price = excluded.open_price,
            high_price = excluded.high_price,
            low_price = excluded.low_price,
            close_price = excluded.close_price,
            price_change = excluded.price_change,
            change_rate = excluded.change_rate,
            volume = excluded.volume,
            trading_value = excluded.trading_value,
            market_cap = excluded.market_cap,
            listed_shares = excluded.listed_shares,
            last_synced_at = current_timestamp,
            updated_at = current_timestamp
        """,
        rows,
    )
    connection.commit()

    return len(rows)


def get_daily_prices(
    connection: sqlite3.Connection,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    stock_code: str | None = None,
    limit: int | None = None,
    descending: bool = False,
) -> pd.DataFrame:
    conditions = []
    params = {}

    if start_date is not None:
        conditions.append("trade_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("trade_date <= :end_date")
        params["end_date"] = end_date
    if stock_code is not None:
        conditions.append("stock_code = :stock_code")
        params["stock_code"] = stock_code

    where_clause = ""
    if conditions:
        where_clause = "where " + " and ".join(conditions)

    order_dir = "desc" if descending else "asc"
    limit_clause = ""
    if limit is not None:
        limit_clause = "limit :limit"
        params["limit"] = limit

    return pd.read_sql_query(
        f"""
        select {", ".join(DAILY_PRICE_COLUMNS)}
        from daily_prices
        {where_clause}
        order by trade_date {order_dir}
        {limit_clause}
        """,
        connection,
        params=params,
    )


def get_existing_trade_dates(connection: sqlite3.Connection, start_date: str) -> set[str]:
    """Retrieve unique trade_dates from daily_prices since start_date."""
    cursor = connection.cursor()
    cursor.execute(
        "select distinct trade_date from daily_prices where trade_date >= :start_date",
        {"start_date": start_date}
    )
    return {row[0] for row in cursor.fetchall() if row[0]}


def get_closed_market_dates(connection: sqlite3.Connection, start_date: str) -> set[str]:
    """Retrieve trade_dates from market_closed_dates since start_date."""
    cursor = connection.cursor()
    cursor.execute(
        "select trade_date from market_closed_dates where trade_date >= :start_date",
        {"start_date": start_date}
    )
    return {row[0] for row in cursor.fetchall() if row[0]}


def insert_closed_market_date(connection: sqlite3.Connection, trade_date: str) -> None:
    """Insert a trade_date into market_closed_dates to mark it as holiday/closed."""
    cursor = connection.cursor()
    cursor.execute(
        "insert or ignore into market_closed_dates (trade_date) values (:trade_date)",
        {"trade_date": trade_date}
    )
    connection.commit()


def get_latest_trade_date(connection: sqlite3.Connection) -> str | None:
    """Retrieve the most recent trade_date present in the daily_prices table."""
    cursor = connection.cursor()
    cursor.execute("select max(trade_date) from daily_prices")
    row = cursor.fetchone()
    if row and row[0]:
        return row[0]
    return None

