import re
from pathlib import Path
from pj_stock_backend.db.sqlite import get_connection
from pj_stock_backend.repositories import daily_price_repository
from pj_stock_backend.pipelines.stock_evaluation_pipeline import run_stock_evaluation_pipeline

def main():
    with get_connection() as db:
        # 1. Find the latest trade date in DB
        latest_base_date = daily_price_repository.get_latest_trade_date(db)
        if not latest_base_date:
            print("No daily price data found in DB. Please sync prices first.")
            return

        # 2. Scan processed directory for the latest financial statement year
        processed_dir = Path(__file__).resolve().parents[2] / "data" / "processed"
        csv_pattern = re.compile(r"^financial_statements_(\d{4})_11011\.csv$")
        years = []
        if processed_dir.exists():
            for p in processed_dir.glob("financial_statements_*_11011.csv"):
                m = csv_pattern.match(p.name)
                if m:
                    years.append(int(m.group(1)))

        if not years:
            print("No processed financial statement CSV found. Please collect financial data first.")
            return

        latest_year = max(years)
        print(f"Running evaluation: year={latest_year}, base_date={latest_base_date}")

        eval_count = run_stock_evaluation_pipeline(
            db,
            business_year=latest_year,
            base_date=latest_base_date,
        )
        print(f"Done! Evaluated {eval_count} rows across strategies.")

if __name__ == "__main__":
    main()
