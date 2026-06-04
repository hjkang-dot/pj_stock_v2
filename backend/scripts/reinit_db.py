import sqlite3
from pathlib import Path
from pj_stock_backend.db.sqlite import get_database_path, get_connection, initialize_database

def main():
    database_path = get_database_path()
    print(f"Connecting to database to re-initialize: {database_path}")
    
    tables_to_drop = [
        "stock_evaluations",
        "ud_portfolio_status",
        "ud_portfolio_holdings",
        "ud_portfolio_history",
        "ud_portfolio_transactions"
    ]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in tables_to_drop:
            print(f"Dropping table {table} if exists...")
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        
    print("Initializing database with new schema...")
    initialize_database()
    print("Database reinitialization complete!")

if __name__ == "__main__":
    main()
