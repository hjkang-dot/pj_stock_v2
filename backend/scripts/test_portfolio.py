from pj_stock_backend.db.sqlite import get_connection
from pj_stock_backend.services import portfolio_service

def test_strategy(strategy_type):
    print(f"\n--- Testing Strategy: {strategy_type} ---")
    with get_connection() as db:
        # 1. Initialize
        print("Initializing portfolio...")
        init_res = portfolio_service.initialize_portfolio(db, 100000000.0, strategy_type)
        print("Init Result:", init_res)
        
        # 2. Check holdings
        cursor = db.cursor()
        cursor.execute("SELECT count(*) FROM ud_portfolio_holdings WHERE strategy_type = ?", (strategy_type,))
        holdings_count = cursor.fetchone()[0]
        print(f"Holdings count in DB: {holdings_count}")
        
        # 3. Update (should say up-to-date since we initialized on the latest trade date)
        print("Updating portfolio...")
        update_res = portfolio_service.update_portfolio_to_latest(db, strategy_type)
        print("Update Result:", update_res)

def main():
    test_strategy("DIVIDEND")
    test_strategy("GROWTH")

if __name__ == "__main__":
    main()
