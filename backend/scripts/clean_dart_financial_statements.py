from pj_stock_backend.cleaners.dart_financial_cleaner import (
    clean_financial_statement,
)
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv


def main() -> None:
    business_year = "2025"
    report_code = "11011"

    raw_path = (
        "../data/raw/dart/"
        f"financial_statements_{business_year}_{report_code}.csv"
    )
    output_path = (
        "../data/processed/"
        f"financial_statements_{business_year}_{report_code}.csv"
    )

    raw = load_dataframe_csv(
        raw_path,
        dtype={
            "rcept_no": str,
            "reprt_code": str,
            "bsns_year": str,
            "corp_code": str,
            "stock_code": str,
        },
    )
    cleaned = clean_financial_statement(raw)

    saved_path = save_dataframe_csv(cleaned, output_path)

    print(f"raw rows: {len(raw)}")
    print(f"cleaned rows: {len(cleaned)}")
    print(f"saved: {saved_path}")
    print(cleaned.head())
    print(cleaned.columns.tolist())


if __name__ == "__main__":
    main()
