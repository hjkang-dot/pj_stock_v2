from pathlib import Path
import sys

# Ensure backend/src is in sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from pj_stock_backend.db.sqlite import get_connection, initialize_database
from pj_stock_backend.repositories.stock_repository import upsert_stocks
from pj_stock_backend.storage.csv_storage import load_dataframe_csv


def main() -> None:
    # Resolve the file path to be safe.
    base_dir = Path(__file__).resolve().parents[2]
    csv_path = base_dir / "data" / "processed" / "stocks.csv"

    if not csv_path.exists():
        print(f"Error: {csv_path} does not exist. Please run clean_krx_listed_stocks.py first.")
        sys.exit(1)

    # Drop existing stocks table to ensure it gets recreated with the latest columns (like is_active)
    print("Dropping existing 'stocks' table to ensure up-to-date schema...")
    with get_connection() as connection:
        connection.execute("drop table if exists stocks")
        connection.commit()

    # Ensure database tables exist
    initialize_database()

    print(f"Loading stocks from {csv_path}...")
    stocks_df = load_dataframe_csv(str(csv_path), dtype={"stock_code": str})

    # Load and map DART corp codes
    corp_codes_path = base_dir / "data" / "processed" / "dart_corp_codes.csv"
    import pandas as pd
    if corp_codes_path.exists():
        print(f"Loading DART corp codes from {corp_codes_path}...")
        corp_codes_df = load_dataframe_csv(str(corp_codes_path), dtype={"stock_code": str, "corp_code": str})
        
        # Normalize code formats
        stocks_df["stock_code"] = stocks_df["stock_code"].astype(str).str.zfill(6)
        corp_codes_df["stock_code"] = corp_codes_df["stock_code"].astype(str).str.zfill(6)
        corp_codes_df["corp_code"] = corp_codes_df["corp_code"].astype(str).str.zfill(8)

        # Merge KRX listed stocks with DART codes
        merged_df = pd.merge(
            stocks_df,
            corp_codes_df[["stock_code", "corp_code"]],
            on="stock_code",
            how="left"
        )
        
        # Map corp_code to database field dart_corp_code
        merged_df = merged_df.rename(columns={"corp_code": "dart_corp_code"})
            
        stocks_df = merged_df
        print("DART corp codes mapped successfully.")
    else:
        print(f"Warning: {corp_codes_path} not found. Stocks will be synced without DART corp codes.")
        stocks_df["dart_corp_code"] = None

    with get_connection() as connection:
        count = upsert_stocks(connection, stocks_df)

    print(f"Successfully synced {count} stocks from CSV to SQLite database.")


if __name__ == "__main__":
    main()
