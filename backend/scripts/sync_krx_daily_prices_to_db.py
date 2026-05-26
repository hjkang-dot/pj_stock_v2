import argparse

from pj_stock_backend.pipelines.krx_daily_price_pipeline import (
    parse_date_range,
    run_krx_daily_price_db_sync,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date")
    parser.add_argument("--end-date", default="today")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    start_date, end_date = parse_date_range(
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days,
    )
    run_krx_daily_price_db_sync(start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    main()
