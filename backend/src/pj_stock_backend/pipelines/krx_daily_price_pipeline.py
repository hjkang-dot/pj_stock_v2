from datetime import date
from pathlib import Path

import pandas as pd

from pj_stock_backend.cleaners.krx_price_cleaner import clean_daily_prices
from pj_stock_backend.collectors.krx_collector import Market, fetch_daily_prices
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


MARKETS: tuple[Market, ...] = ("KOSPI", "KOSDAQ")


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
