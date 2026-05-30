import argparse
from pathlib import Path
import re
import sys
import sqlite3
import pandas as pd

# Ensure backend/src is in sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from pj_stock_backend.db.sqlite import get_connection, initialize_database
from pj_stock_backend.storage.csv_storage import load_dataframe_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-year")
    parser.add_argument("--report-code", default="11011")
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Sync every processed financial_statements CSV instead of a single report year.",
    )
    args = parser.parse_args()

    # Resolve project paths
    base_dir = Path(__file__).resolve().parents[2]
    processed_dir = base_dir / "data" / "processed"

    if not processed_dir.exists():
        print(f"Error: {processed_dir} does not exist.")
        sys.exit(1)

    # Scan for financial_statements_{year}_11011.csv files
    fin_pattern = re.compile(r"^financial_statements_(\d{4})_(\d{5})\.csv$")
    years_info = []
    
    for p in processed_dir.glob("financial_statements_*_*.csv"):
        m = fin_pattern.match(p.name)
        if m:
            year = m.group(1)
            report_code = m.group(2)
            years_info.append((year, report_code, p))

    if not years_info:
        print("No processed financial statement files found in data/processed.")
        sys.exit(1)

    if args.all_files:
        selected_years_info = years_info
    elif args.business_year:
        selected_years_info = [
            item
            for item in years_info
            if item[0] == args.business_year and item[1] == args.report_code
        ]
        if not selected_years_info:
            print(
                "No matching processed financial statement file found for "
                f"{args.business_year}_{args.report_code}."
            )
            sys.exit(1)
    else:
        matching_report_files = [
            item for item in years_info if item[1] == args.report_code
        ]
        selected_years_info = [max(matching_report_files, key=lambda item: item[0])]

    print(
        "Selected processed files: "
        f"{[p.name for _, _, p in sorted(selected_years_info)]}"
    )

    all_year_dfs = []

    for year, report_code, fin_path in sorted(selected_years_info):
        div_path = processed_dir / f"dividends_{year}_{report_code}.csv"
        
        print(f"Processing Year {year} (Report: {report_code})...")
        print(f"  Loading financials from {fin_path.name}...")
        
        # Load financials, mapping types to preserve string codes
        fin_df = load_dataframe_csv(str(fin_path), dtype={"corp_code": str, "stock_code": str})
        
        # Normalize codes
        fin_df["stock_code"] = fin_df["stock_code"].astype(str).str.zfill(6)
        fin_df["corp_code"] = fin_df["corp_code"].astype(str).str.zfill(8)
        fin_df["source_report_year"] = pd.to_numeric(
            fin_df["bsns_year"],
            errors="coerce",
        )

        # Resolve duplicates per fiscal period: prioritize CFS (Consolidated Financial Statements)
        # over OFS (Separate Financial Statements), while preserving current/prior/prior-prior years
        # from the same business report.
        fin_df["fs_priority"] = fin_df["fs_div"].map({"CFS": 1, "OFS": 2}).fillna(3)
        fin_df = fin_df.sort_values(["corp_code", "fiscal_period", "fs_priority"])
        fin_df = fin_df.drop_duplicates(
            subset=["corp_code", "bsns_year", "fiscal_period"],
            keep="first",
        )
        fin_df["fiscal_year"] = pd.to_numeric(
            fin_df["fiscal_period"].astype(str).str[:4],
            errors="coerce",
        )
        print(f"  Loaded {len(fin_df)} financial statement records.")

        # Load dividends
        div_merged = pd.DataFrame(columns=["corp_code", "fiscal_year"])
        if div_path.exists():
            print(f"  Loading dividends from {div_path.name}...")
            div_df = load_dataframe_csv(str(div_path), dtype={"corp_code": str})
            div_df["corp_code"] = div_df["corp_code"].astype(str).str.zfill(8)

            # ordinary stock vs aggregate values
            div_ord = div_df[div_df["stock_knd"] == "보통주"].copy()
            div_gen = div_df[div_df["stock_knd"] == "-"].copy()

            # ordinary features: cash_dividend_yield, cash_dividend_per_share, par_value
            ord_cols = ["corp_code", "fiscal_year", "cash_dividend_yield", "cash_dividend_per_share", "par_value"]
            ord_cols = [col for col in ord_cols if col in div_df.columns]
            
            div_ord_subset = div_ord[ord_cols].copy()
            div_gen_ord_backup = div_gen[ord_cols].copy()
            
            # Combine ordinary and fallback '-' ordinary properties, keeping '보통주' first
            div_ord_merged = pd.concat([div_ord_subset, div_gen_ord_backup], ignore_index=True)
            div_ord_merged = div_ord_merged.drop_duplicates(subset=["corp_code", "fiscal_year"], keep="first")
            
            # aggregate features: eps, cash_dividend_total, cash_dividend_payout_ratio
            gen_cols = ["corp_code", "fiscal_year", "eps", "cash_dividend_total", "cash_dividend_payout_ratio"]
            gen_cols = [col for col in gen_cols if col in div_df.columns]
            div_gen_subset = div_gen[gen_cols].copy()

            # merge dividend records on (corp_code, fiscal_year)
            div_merged = pd.merge(
                div_ord_merged,
                div_gen_subset,
                on=["corp_code", "fiscal_year"],
                how="outer"
            )
            div_merged = div_merged.drop_duplicates(subset=["corp_code", "fiscal_year"], keep="first")
            print(f"  Loaded {len(div_merged)} dividend records.")
        else:
            print(f"  Warning: No dividends file found at {div_path.name}. Proceeding without dividend info for {year}.")

        # Convert fiscal_year type to numeric so dividends match each financial fiscal period.
        if not div_merged.empty:
            div_merged["fiscal_year"] = pd.to_numeric(div_merged["fiscal_year"], errors="coerce")
        fin_df["bsns_year"] = pd.to_numeric(fin_df["bsns_year"], errors="coerce")

        # Merge Financials and Dividends
        print("  Merging financials and dividends...")
        if not div_merged.empty:
            merged = pd.merge(
                fin_df,
                div_merged,
                left_on=["corp_code", "fiscal_year"],
                right_on=["corp_code", "fiscal_year"],
                how="left"
            )
        else:
            merged = fin_df.copy()

        all_year_dfs.append(merged)

    if not all_year_dfs:
        print("No data to sync.")
        return

    # Combine all years
    print("Combining data for all years...")
    final_merged = pd.concat(all_year_dfs, ignore_index=True)
    final_merged["bsns_year"] = pd.to_numeric(final_merged["bsns_year"], errors="coerce")
    if "source_report_year" not in final_merged.columns:
        final_merged["source_report_year"] = final_merged["bsns_year"]
    final_merged["fiscal_period_sort"] = pd.to_numeric(
        final_merged["fiscal_period"].astype(str).str.replace(".", "", regex=False),
        errors="coerce",
    )
    final_merged["fs_priority"] = final_merged["fs_div"].map({"CFS": 1, "OFS": 2}).fillna(3)
    final_merged = (
        final_merged.sort_values(
            ["corp_code", "fiscal_period_sort", "source_report_year", "fs_priority"],
            ascending=[True, True, False, True],
        )
        .drop_duplicates(subset=["corp_code", "fiscal_period"], keep="first")
        .drop(columns=["fiscal_period_sort", "fs_priority"], errors="ignore")
    )
    final_merged["bsns_year"] = pd.to_numeric(
        final_merged["fiscal_period"].astype(str).str[:4],
        errors="coerce",
    )
    final_merged = final_merged.drop(columns=["fiscal_year", "source_report_year"], errors="ignore")

    # Define columns to save matching schema
    COLUMNS_TO_SAVE = [
        "corp_code", "stock_code", "bsns_year", "fs_div", "fs_nm", "currency", "fiscal_period",
        "current_assets", "non_current_assets", "total_assets", "current_liabilities",
        "non_current_liabilities", "total_liabilities", "total_equity", "revenue",
        "operating_income", "net_income", "debt_ratio", "current_ratio", "equity_ratio",
        "operating_margin", "net_margin", "par_value", "eps", "cash_dividend_yield",
        "cash_dividend_per_share", "cash_dividend_total", "cash_dividend_payout_ratio"
    ]

    for col in COLUMNS_TO_SAVE:
        if col not in final_merged.columns:
            final_merged[col] = None

    final_df = final_merged[COLUMNS_TO_SAVE].copy()

    # Convert float NaN values to Python None to insert as SQL NULLs
    rows = final_df.to_dict("records")
    cleaned_rows = []
    for row in rows:
        cleaned_row = {}
        for k, v in row.items():
            if pd.isna(v):
                cleaned_row[k] = None
            else:
                cleaned_row[k] = v
        cleaned_rows.append(cleaned_row)

    print("Recreating database table 'company_financials'...")
    with get_connection() as connection:
        connection.execute("drop table if exists company_financials")
        connection.commit()

    # Re-run schema initialization
    initialize_database()

    print(f"Inserting {len(cleaned_rows)} records into SQLite...")
    with get_connection() as connection:
        connection.executemany(
            """
            insert into company_financials (
                corp_code, stock_code, bsns_year, fs_div, fs_nm, currency, fiscal_period,
                current_assets, non_current_assets, total_assets, current_liabilities,
                non_current_liabilities, total_liabilities, total_equity, revenue,
                operating_income, net_income, debt_ratio, current_ratio, equity_ratio,
                operating_margin, net_margin, par_value, eps, cash_dividend_yield,
                cash_dividend_per_share, cash_dividend_total, cash_dividend_payout_ratio
            )
            values (
                :corp_code, :stock_code, :bsns_year, :fs_div, :fs_nm, :currency, :fiscal_period,
                :current_assets, :non_current_assets, :total_assets, :current_liabilities,
                :non_current_liabilities, :total_liabilities, :total_equity, :revenue,
                :operating_income, :net_income, :debt_ratio, :current_ratio, :equity_ratio,
                :operating_margin, :net_margin, :par_value, :eps, :cash_dividend_yield,
                :cash_dividend_per_share, :cash_dividend_total, :cash_dividend_payout_ratio
            )
            """,
            cleaned_rows
        )
        connection.commit()

    print("Successfully synced unified financials and dividends table into SQLite.")


if __name__ == "__main__":
    main()
