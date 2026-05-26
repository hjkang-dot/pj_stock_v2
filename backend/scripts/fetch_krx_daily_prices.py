from pj_stock_backend.collectors.krx_collector import fetch_daily_prices
from pj_stock_backend.storage.csv_storage import save_dataframe_csv


def main() -> None:
    base_date = "20260522"

    for market in ["KOSPI", "KOSDAQ"]:
        prices = fetch_daily_prices(market, base_date)
        output_path = f"../data/raw/krx/daily_prices_{base_date}_{market}.csv"

        saved_path = save_dataframe_csv(prices, output_path)

        print(f"\n[{market}] rows={len(prices)}")
        print(f"saved: {saved_path}")
        print(prices.head())
        print(prices.columns.tolist())


if __name__ == "__main__":
    main()
