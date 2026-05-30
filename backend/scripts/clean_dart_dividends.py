import argparse

from pj_stock_backend.cleaners.dart_dividend_cleaner import clean_dividends
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-year", default="2025")
    parser.add_argument("--report-code", default="11011")
    args = parser.parse_args()

    business_year = args.business_year
    report_code = args.report_code

    raw_path = "../data/raw/dart/" f"dividends_{business_year}_{report_code}.csv"
    output_path = "../data/processed/" f"dividends_{business_year}_{report_code}.csv"

    raw = load_dataframe_csv(
        raw_path,
        dtype={
            "rcept_no": str,
            "corp_code": str,
            "corp_name": str,
        },
    )
    cleaned = clean_dividends(raw)

    saved_path = save_dataframe_csv(cleaned, output_path)

    print(f"raw rows: {len(raw)}")
    print(f"cleaned rows: {len(cleaned)}")
    print(f"saved: {saved_path}")
    print(cleaned.head())
    print(cleaned.columns.tolist())


if __name__ == "__main__":
    main()
