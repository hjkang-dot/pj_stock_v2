from pj_stock_backend.collectors.dart_collector import fetch_financial_statement
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


def main() -> None:
    corp_code = "00126380"
    business_year = "2025"
    report_code = "11011"

    financial_statement = fetch_financial_statement(
        corp_code=corp_code,
        business_year=business_year,
        report_code=report_code,
    )
    output_path = (
        "../data/raw/dart/"
        f"financial_statement_{business_year}_{report_code}_{corp_code}.csv"
    )

    saved_path = save_dataframe_csv(financial_statement, output_path)

    print(f"rows: {len(financial_statement)}")
    print(f"saved: {saved_path}")
    print(financial_statement.head())
    print(financial_statement.columns.tolist())


if __name__ == "__main__":
    main()
