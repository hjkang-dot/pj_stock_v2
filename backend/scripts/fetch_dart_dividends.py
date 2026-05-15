import argparse
from pathlib import Path
import time

import pandas as pd
import requests

from pj_stock_backend.collectors.dart_collector import fetch_dividend_info
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-year", default="2025")
    parser.add_argument("--report-code", default="11011")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    args = parser.parse_args()

    corp_codes = load_dataframe_csv(
        "../data/processed/dart_corp_codes.csv",
        dtype={
            "corp_code": str,
            "corp_name": str,
            "stock_code": str,
            "modify_date": str,
        },
    )

    if args.limit > 0:
        corp_codes = corp_codes.head(args.limit)

    output_path = Path(
        "../data/raw/dart/" f"dividends_{args.business_year}_{args.report_code}.csv"
    )
    dividends = []
    completed_stock_codes: set[str] = set()

    if output_path.exists():
        existing = load_dataframe_csv(output_path, dtype={"stock_code": str})
        dividends.append(existing)
        completed_stock_codes = set(existing["stock_code"].dropna().astype(str))
        print(f"resume from existing file: {output_path} rows={len(existing)}")

    for index, row in corp_codes.iterrows():
        corp_code = row["corp_code"]
        stock_code = row["stock_code"]
        corp_name = row["corp_name"]

        if stock_code in completed_stock_codes:
            print(f"[skip] {stock_code} {corp_name}: already saved")
            continue

        try:
            dividend = fetch_dividend_info(
                corp_code=corp_code,
                business_year=args.business_year,
                report_code=args.report_code,
            )
        except ValueError as error:
            print(f"[skip] {stock_code} {corp_name}: {error}")
            continue
        except requests.RequestException as error:
            print(f"[skip] {stock_code} {corp_name}: network error: {error}")
            continue

        dividends.append(dividend)
        completed_stock_codes.add(stock_code)
        combined = pd.concat(dividends, ignore_index=True)
        save_dataframe_csv(combined, output_path)

        print(
            f"[{index + 1}/{len(corp_codes)}] "
            f"{stock_code} {corp_name}: rows={len(dividend)} saved"
        )
        time.sleep(args.sleep_seconds)

    if dividends:
        combined = pd.concat(dividends, ignore_index=True)
    else:
        combined = pd.DataFrame()

    saved_path = save_dataframe_csv(combined, output_path)

    print(f"companies: {len(corp_codes)}")
    print(f"rows: {len(combined)}")
    print(f"saved: {saved_path}")
    print(combined.head())
    print(combined.columns.tolist())


if __name__ == "__main__":
    main()
