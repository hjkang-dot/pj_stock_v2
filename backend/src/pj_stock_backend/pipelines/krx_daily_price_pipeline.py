from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from pj_stock_backend.cleaners.krx_price_cleaner import clean_daily_prices
from pj_stock_backend.collectors.krx_collector import Market, fetch_daily_prices
from pj_stock_backend.db.sqlite import get_connection, initialize_database
from pj_stock_backend.repositories.daily_price_repository import upsert_daily_prices
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


MARKETS: tuple[Market, ...] = ("KOSPI", "KOSDAQ")
DailyPriceFetcher = Callable[[Market, str], pd.DataFrame]


def run_krx_daily_price_pipeline(base_date: str) -> Path:
    raw_dataframes = []

    for market in MARKETS:
        prices = fetch_daily_prices(market, base_date)
        raw_path = f"../data/raw/krx/daily_prices_{base_date}_{market}.csv"
        saved_raw_path = save_dataframe_csv(prices, raw_path)

        raw_dataframes.append(prices)

        print(f"[fetch:{market}] rows={len(prices)} saved={saved_raw_path}")

    raw_combined = pd.concat(raw_dataframes, ignore_index=True)
    cleaned = clean_daily_prices(raw_combined)

    processed_path = f"../data/processed/daily_prices_{base_date}.csv"
    saved_processed_path = save_dataframe_csv(cleaned, processed_path)

    print(f"[clean] raw rows={len(raw_combined)} cleaned rows={len(cleaned)}")
    print(f"saved: {saved_processed_path}")
    print(cleaned.head())
    print(cleaned.columns.tolist())

    return saved_processed_path


def parse_base_date(value: str) -> str:
    if value == "today":
        return date.today().strftime("%Y%m%d")

    normalized_value = value.strip()

    if len(normalized_value) != 8 or not normalized_value.isdigit():
        msg = "--base-date must be YYYYMMDD or today"
        raise ValueError(msg)

    return normalized_value


def parse_date_range(
    *,
    start_date: str | None,
    end_date: str | None,
    days: int | None,
    today: date | None = None,
) -> tuple[str, str]:
    today = today or date.today()

    parsed_end_date = _parse_date_value(end_date or "today", today=today)
    if start_date is not None:
        parsed_start_date = _parse_date_value(start_date, today=today)
    else:
        day_count = days or 365
        if day_count <= 0:
            msg = "--days must be greater than 0"
            raise ValueError(msg)
        parsed_start_date = parsed_end_date - timedelta(days=day_count - 1)

    if parsed_start_date > parsed_end_date:
        msg = "--start-date must be before or equal to --end-date"
        raise ValueError(msg)

    return (
        parsed_start_date.strftime("%Y%m%d"),
        parsed_end_date.strftime("%Y%m%d"),
    )


def iter_calendar_dates(start_date: str, end_date: str) -> list[str]:
    current = _parse_date_value(start_date)
    end = _parse_date_value(end_date)

    dates = []
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    return dates


def run_krx_daily_price_db_sync(
    *,
    start_date: str,
    end_date: str,
    fetcher: DailyPriceFetcher = fetch_daily_prices,
) -> int:
    initialize_database()
    total_saved_rows = 0

    with get_connection() as connection:
        for base_date in iter_calendar_dates(start_date, end_date):
            raw_dataframes = []

            for market in MARKETS:
                prices = fetcher(market, base_date)
                raw_dataframes.append(prices)
                print(f"[fetch:{base_date}:{market}] rows={len(prices)}")

            non_empty_dataframes = [
                dataframe for dataframe in raw_dataframes if not dataframe.empty
            ]
            if not non_empty_dataframes:
                print(f"[skip:{base_date}] no rows")
                continue

            raw_combined = pd.concat(non_empty_dataframes, ignore_index=True)
            cleaned = clean_daily_prices(raw_combined)
            saved_rows = upsert_daily_prices(connection, cleaned)
            total_saved_rows += saved_rows
            print(f"[upsert:{base_date}] rows={saved_rows}")

    print(f"total upserted rows: {total_saved_rows}")

    return total_saved_rows


def _parse_date_value(value: str, *, today: date | None = None) -> date:
    if value == "today":
        return today or date.today()

    normalized_value = value.strip()

    if len(normalized_value) != 8 or not normalized_value.isdigit():
        msg = "date must be YYYYMMDD or today"
        raise ValueError(msg)

    try:
        return date(
            int(normalized_value[:4]),
            int(normalized_value[4:6]),
            int(normalized_value[6:8]),
        )
    except ValueError as error:
        msg = "date must be a valid YYYYMMDD date or today"
        raise ValueError(msg) from error
