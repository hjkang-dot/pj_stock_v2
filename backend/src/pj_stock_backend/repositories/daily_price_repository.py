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

    return pd.read_sql_query(
        f"""
        select {", ".join(DAILY_PRICE_COLUMNS)}
        from daily_prices
        {where_clause}
        order by trade_date, stock_code
        """,
        connection,
        params=params,
    )
