from pj_stock_backend.collectors.dart_collector import fetch_corp_codes
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


def main() -> None:
    corp_codes = fetch_corp_codes()
    output_path = "../data/raw/dart/corp_codes.csv"

    saved_path = save_dataframe_csv(corp_codes, output_path)

    print(f"rows: {len(corp_codes)}")
    print(f"saved: {saved_path}")
    print(corp_codes.head())
    print(corp_codes.columns.tolist())


if __name__ == "__main__":
    main()
