import argparse

from pj_stock_backend.pipelines.krx_daily_price_pipeline import (
    parse_base_date,
    run_krx_daily_price_pipeline,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-date", default="today")
    args = parser.parse_args()

    base_date = parse_base_date(args.base_date)
    run_krx_daily_price_pipeline(base_date)


if __name__ == "__main__":
    main()
