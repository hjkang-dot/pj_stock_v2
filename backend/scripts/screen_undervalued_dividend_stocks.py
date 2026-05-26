import argparse

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
    daily_prices = load_dataframe_csv(
        f"../data/processed/daily_prices_{args.base_date}.csv",
        dtype={"stock_code": str},
    )
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
