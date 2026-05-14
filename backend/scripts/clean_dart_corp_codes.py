from pj_stock_backend.cleaners.dart_corp_cleaner import clean_corp_codes
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv


def main() -> None:
    raw_path = "../data/raw/dart/corp_codes.csv"
    output_path = "../data/processed/dart_corp_codes.csv"

    raw = load_dataframe_csv(
        raw_path,
        dtype={
            "corp_code": str,
            "corp_name": str,
            "stock_code": str,
            "modify_date": str,
        },
    )
    cleaned = clean_corp_codes(raw)

    saved_path = save_dataframe_csv(cleaned, output_path)

    print(f"raw rows: {len(raw)}")
    print(f"cleaned rows: {len(cleaned)}")
    print(f"saved: {saved_path}")
    print(cleaned.head())
    print(cleaned.columns.tolist())


if __name__ == "__main__":
    main()
