from pj_stock_backend.collectors.krx_collector import fetch_listed_stocks
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


def main() -> None:
    base_date = "20260512"

    for market in ["KOSPI", "KOSDAQ"]:
        stocks = fetch_listed_stocks(market, base_date)
        output_path = f"../data/raw/krx/listed_stocks_{base_date}_{market}.csv"

        saved_path = save_dataframe_csv(stocks, output_path)

        print(f"\n[{market}] rows={len(stocks)}")
        print(f"saved: {saved_path}")
        print(stocks.head())
        print(stocks.columns.tolist())


if __name__ == "__main__":
    main()
