from datetime import date

from pj_stock_backend.collectors.krx_collector import fetch_listed_stocks


def main() -> None:
    base_date = "20260512"

    for market in ["KOSPI", "KOSDAQ"]:
        stocks = fetch_listed_stocks(market, base_date)

        print(f"\n[{market}] rows={len(stocks)}")
        print(stocks.head())
        print(stocks.columns.tolist())


if __name__ == "__main__":
    main()
