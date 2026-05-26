import pandas as pd

from pj_stock_backend.cleaners.krx_price_cleaner import clean_daily_prices
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv


def main() -> None:
    base_date = "20260522"

    raw_paths = [
        f"../data/raw/krx/daily_prices_{base_date}_KOSPI.csv",
        f"../data/raw/krx/daily_prices_{base_date}_KOSDAQ.csv",
    ]

    raw_dataframes = [
        load_dataframe_csv(path, dtype={"ISU_CD": str})
        for path in raw_paths
    ]

    raw_combined = pd.concat(raw_dataframes, ignore_index=True)
    cleaned = clean_daily_prices(raw_combined)

    output_path = f"../data/processed/daily_prices_{base_date}.csv"
    saved_path = save_dataframe_csv(cleaned, output_path)

    print(f"raw rows: {len(raw_combined)}")
    print(f"cleaned rows: {len(cleaned)}")
    print(f"saved: {saved_path}")
    print(cleaned.head())
    print(cleaned.columns.tolist())


if __name__ == "__main__":
    main()
