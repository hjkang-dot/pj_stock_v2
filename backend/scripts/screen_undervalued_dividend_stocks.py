import argparse

from pj_stock_backend.db.sqlite import get_connection
from pj_stock_backend.repositories.daily_price_repository import get_daily_prices
from pj_stock_backend.storage.csv_storage import load_dataframe_csv, save_dataframe_csv
from pj_stock_backend.strategies.undervalued_dividend_strategy import (
    screen_undervalued_dividend_stocks,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-year", default="2025")
    parser.add_argument("--report-code", default="11011")
    parser.add_argument("--base-date", default="20260522")
    parser.add_argument("--minimum-total-score", type=float, default=60.0)
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    financial_statements = load_dataframe_csv(
        f"../data/processed/financial_statements_{args.business_year}_{args.report_code}.csv",
        dtype={"corp_code": str, "stock_code": str},
    )
    dividends = load_dataframe_csv(
        f"../data/processed/dividends_{args.business_year}_{args.report_code}.csv",
        dtype={"corp_code": str, "stock_code": str},
    )
    with get_connection() as connection:
        daily_prices = get_daily_prices(
            connection,
            start_date=args.base_date,
            end_date=args.base_date,
        )

    if daily_prices.empty:
        msg = (
            f"No daily prices found in DB for {args.base_date}. "
            "Run scripts/sync_krx_daily_prices_to_db.py first."
        )
        raise ValueError(msg)

    stocks = load_dataframe_csv(
        "../data/processed/stocks.csv",
        dtype={"stock_code": str, "listed_date": str},
    )

    screened = screen_undervalued_dividend_stocks(
        financial_statements,
        dividends,
        daily_prices,
        stocks,
        minimum_total_score=args.minimum_total_score,
    )
    candidates = screened[screened["is_candidate"]].head(args.top)

    output_path = (
        "../data/processed/"
        f"undervalued_dividend_candidates_{args.business_year}_{args.base_date}.csv"
    )
    saved_path = save_dataframe_csv(candidates, output_path)

    print(f"screened rows: {len(screened)}")
    print(f"candidate rows: {len(candidates)}")
    print(f"saved: {saved_path}")
    print(candidates.head(args.top))


if __name__ == "__main__":
    main()
