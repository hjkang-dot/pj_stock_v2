import sqlite3

import pandas as pd

from pj_stock_backend.repositories.daily_price_repository import (
    get_daily_prices,
    upsert_daily_prices,
)


def test_upsert_daily_prices_inserts_and_updates_rows() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        create table daily_prices (
            id integer primary key autoincrement,
            trade_date text not null,
            stock_code text not null,
            stock_name text not null,
            market text not null,
            section text,
            open_price integer not null,
            high_price integer not null,
            low_price integer not null,
            close_price integer not null,
            price_change integer not null,
            change_rate real not null,
            volume integer not null,
            trading_value integer not null,
            market_cap integer not null,
            listed_shares integer not null,
            last_synced_at text not null default current_timestamp,
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp,
            unique (trade_date, stock_code)
        );
        """
    )

    first = _daily_price_dataframe(close_price=74000)
    second = _daily_price_dataframe(close_price=75000)

    assert upsert_daily_prices(connection, first) == 1
    assert upsert_daily_prices(connection, second) == 1

    rows = get_daily_prices(connection)

    assert len(rows) == 1
    assert rows.iloc[0]["close_price"] == 75000


def _daily_price_dataframe(close_price: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "20260522",
                "stock_code": "005930",
                "stock_name": "Samsung Electronics",
                "market": "KOSPI",
                "section": "Common Stock",
                "open_price": 72800,
                "high_price": 74500,
                "low_price": 72500,
                "close_price": close_price,
                "price_change": 1200,
                "change_rate": 1.65,
                "volume": 12345678,
                "trading_value": 912345678900,
                "market_cap": 441234567890000,
                "listed_shares": 5969782550,
            }
        ]
    )
