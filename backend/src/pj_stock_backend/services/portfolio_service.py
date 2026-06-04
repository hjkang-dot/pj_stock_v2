import sqlite3
import pandas as pd
import re
from pathlib import Path
from pj_stock_backend.pipelines.stock_evaluation_pipeline import run_stock_evaluation_pipeline
from pj_stock_backend.repositories import daily_price_repository


def get_evaluations_for_date(db: sqlite3.Connection, base_date: str, strategy_type: str = "DIVIDEND") -> pd.DataFrame:
    """Retrieve evaluated stocks for a specific date and strategy, running the evaluation pipeline if not present."""
    df = pd.read_sql_query(
        """
        SELECT e.*, s.stock_name, s.sector 
        FROM stock_evaluations e 
        JOIN stocks s ON e.stock_code = s.stock_code 
        WHERE e.base_date = ? AND e.strategy_type = ?
        """,
        db,
        params=[base_date, strategy_type]
    )
    if not df.empty:
        return df

    # Scan for the latest processed financial statements year in the data folder
    processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
    csv_pattern = re.compile(r"^financial_statements_(\d{4})_11011\.csv$")
    years = []
    if processed_dir.exists():
        for p in processed_dir.glob("financial_statements_*_11011.csv"):
            m = csv_pattern.match(p.name)
            if m:
                years.append(int(m.group(1)))
    
    if not years:
        latest_year = 2025
    else:
        latest_year = max(years)
        
    try:
        print(f"[portfolio_service] Running evaluation pipeline for {base_date}...")
        run_stock_evaluation_pipeline(db, business_year=latest_year, base_date=base_date)
    except Exception as e:
        print(f"[portfolio_service] Failed to run pipeline for {base_date}: {e}")
        return pd.DataFrame()
        
    return pd.read_sql_query(
        """
        SELECT e.*, s.stock_name, s.sector 
        FROM stock_evaluations e 
        JOIN stocks s ON e.stock_code = s.stock_code 
        WHERE e.base_date = ? AND e.strategy_type = ?
        """,
        db,
        params=[base_date, strategy_type]
    )


def initialize_portfolio(db: sqlite3.Connection, initial_balance: float, strategy_type: str = "DIVIDEND") -> dict:
    """Clear portfolio tables for the given strategy and enter initial positions based on the latest available trade date."""
    cursor = db.cursor()
    cursor.execute("DELETE FROM ud_portfolio_status WHERE strategy_type = ?", (strategy_type,))
    cursor.execute("DELETE FROM ud_portfolio_holdings WHERE strategy_type = ?", (strategy_type,))
    cursor.execute("DELETE FROM ud_portfolio_history WHERE strategy_type = ?", (strategy_type,))
    cursor.execute("DELETE FROM ud_portfolio_transactions WHERE strategy_type = ?", (strategy_type,))
    db.commit()

    # Get latest trade date from daily_prices
    latest_trade_date = daily_price_repository.get_latest_trade_date(db)
    if not latest_trade_date:
        return {"status": "error", "message": "No price data in database to initialize portfolio."}

    # Get evaluations for the latest date
    evals = get_evaluations_for_date(db, latest_trade_date, strategy_type)
    if evals.empty:
        return {"status": "error", "message": f"Failed to get evaluations for {latest_trade_date}."}

    # Filter for total_score >= 70.0 and is_candidate = 1
    candidates = evals[(evals["total_score"] >= 70.0) & (evals["is_candidate"] == 1)].copy()
    
    # Sort candidates dynamically based on strategy type
    if strategy_type == "DIVIDEND":
        candidates = candidates.sort_values(
            by=["total_score", "dividend_yield", "market_cap"],
            ascending=[False, False, False]
        )
    else:
        candidates = candidates.sort_values(
            by=["total_score", "revenue_growth", "market_cap"],
            ascending=[False, False, False]
        )

    holdings_to_insert = []
    txs_to_insert = []

    for _, row in candidates.iterrows():
        stock_code = row["stock_code"]
        stock_name = row["stock_name"]
        close_price = row["close_price"]
        score = row["total_score"]
        
        quantity = 1
        buy_amount = close_price * quantity
        
        holdings_to_insert.append((
            stock_code,
            stock_name,
            latest_trade_date,
            close_price,
            quantity,
            close_price,
            buy_amount,
            0.0,  # holding_return
            score,
            None,  # exit_date
            None,  # exit_price
            None,  # score_at_exit
            "ACTIVE",
            strategy_type
        ))
        
        txs_to_insert.append((
            latest_trade_date,
            stock_code,
            stock_name,
            "BUY",
            close_price,
            quantity,
            buy_amount,
            score,
            strategy_type
        ))

    # Save holdings
    if holdings_to_insert:
        cursor.executemany(
            """
            INSERT INTO ud_portfolio_holdings (
                stock_code, stock_name, entry_date, entry_price, quantity,
                current_price, valuation, holding_return, score_at_entry,
                exit_date, exit_price, score_at_exit, status, strategy_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            holdings_to_insert
        )

    # Save transactions
    if txs_to_insert:
        cursor.executemany(
            """
            INSERT INTO ud_portfolio_transactions (
                trade_date, stock_code, stock_name, transaction_type,
                price, quantity, amount, score, strategy_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            txs_to_insert
        )

    total_asset = initial_balance
    cursor.execute(
        """
        INSERT INTO ud_portfolio_status (
            strategy_type, initial_balance, current_cash, current_valuation, total_asset,
            mdd, total_return, win_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (strategy_type, initial_balance, 0.0, total_asset, total_asset, 0.0, 0.0, 0.0)
    )

    # Save history
    cursor.execute(
        """
        INSERT INTO ud_portfolio_history (
            trade_date, strategy_type, cash, valuation, total_asset, daily_return, drawdown
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (latest_trade_date, strategy_type, 0.0, total_asset, total_asset, 0.0, 0.0)
    )

    db.commit()
    return {
        "status": "success", 
        "message": f"Portfolio initialized on {latest_trade_date} with {len(holdings_to_insert)} active holdings for {strategy_type}."
    }


def update_portfolio_to_latest(db: sqlite3.Connection, strategy_type: str = "DIVIDEND") -> dict:
    """Advance the virtual portfolio forward using any new trade dates since the last history record for the strategy."""
    cursor = db.cursor()
    cursor.execute("SELECT initial_balance, total_asset FROM ud_portfolio_status WHERE strategy_type = ? LIMIT 1", (strategy_type,))
    status_row = cursor.fetchone()
    if not status_row:
        return {"status": "error", "message": f"Portfolio has not been initialized for {strategy_type}. Please initialize it first."}
    
    initial_balance, last_total_asset = status_row[0], status_row[1]

    # Get last historical date recorded in history
    cursor.execute("SELECT max(trade_date) FROM ud_portfolio_history WHERE strategy_type = ?", (strategy_type,))
    last_hist_date_row = cursor.fetchone()
    if not last_hist_date_row or not last_hist_date_row[0]:
        return {"status": "error", "message": f"Portfolio history empty for {strategy_type}. Re-initialize needed."}
    
    last_hist_date = last_hist_date_row[0]

    # Find target dates in daily_prices that are after last_hist_date
    cursor.execute(
        "SELECT DISTINCT trade_date FROM daily_prices WHERE trade_date > ? ORDER BY trade_date ASC",
        (last_hist_date,)
    )
    target_dates = [r[0] for r in cursor.fetchall()]
    
    if not target_dates:
        return {"status": "success", "message": f"Portfolio for {strategy_type} is already up-to-date.", "processed_days": 0}

    processed_days = 0
    current_total_asset = last_total_asset

    for t_date in target_dates:
        # Load evaluations for t_date
        evals = get_evaluations_for_date(db, t_date, strategy_type)
        if evals.empty:
            continue

        # Convert to dict for quick lookups
        eval_dict = evals.set_index("stock_code").to_dict("index")

        # Load currently ACTIVE holdings before processing updates for today
        cursor.execute(
            """
            SELECT id, stock_code, stock_name, entry_date, entry_price, current_price, score_at_entry 
            FROM ud_portfolio_holdings
            WHERE status = 'ACTIVE' AND strategy_type = ?
            """,
            (strategy_type,)
        )
        holdings_before = [dict(r) for r in cursor.fetchall()]

        # 1. Calculate today's total_asset based on yesterday's active holdings' price change factor
        if not holdings_before:
            today_total_asset = current_total_asset
        else:
            ratios = []
            for hold in holdings_before:
                code = hold["stock_code"]
                price_yesterday = hold["current_price"]
                
                eval_info = eval_dict.get(code)
                if eval_info is not None:
                    price_today = eval_info["close_price"]
                else:
                    cursor.execute(
                        "SELECT close_price FROM daily_prices WHERE trade_date = ? AND stock_code = ?",
                        (t_date, code)
                    )
                    price_row = cursor.fetchone()
                    price_today = price_row[0] if price_row else price_yesterday
                
                ratio = price_today / price_yesterday
                ratios.append(ratio)
            
            avg_ratio = sum(ratios) / len(ratios)
            today_total_asset = current_total_asset * avg_ratio

        current_total_asset = today_total_asset

        # 2. Process exits (Sell)
        active_holdings_codes = []
        for hold in holdings_before:
            row_id = hold["id"]
            code = hold["stock_code"]
            entry_price = hold["entry_price"]

            eval_info = eval_dict.get(code)
            if eval_info is None:
                cursor.execute(
                    "SELECT close_price FROM daily_prices WHERE trade_date = ? AND stock_code = ?",
                    (t_date, code)
                )
                price_row = cursor.fetchone()
                curr_price = price_row[0] if price_row else hold["current_price"]
                score = 0.0
            else:
                curr_price = eval_info["close_price"]
                score = eval_info["total_score"]

            if score < 60.0 or eval_info is None:
                sell_amount = curr_price * 1
                holding_ret = ((curr_price - entry_price) / entry_price) * 100
                
                cursor.execute(
                    """
                    UPDATE ud_portfolio_holdings
                    SET current_price = ?, valuation = ?, holding_return = ?, 
                        exit_date = ?, exit_price = ?, score_at_exit = ?, status = 'CLOSED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (curr_price, sell_amount, holding_ret, t_date, curr_price, score, row_id)
                )
                
                cursor.execute(
                    """
                    INSERT INTO ud_portfolio_transactions (
                        trade_date, stock_code, stock_name, transaction_type,
                        price, quantity, amount, score, strategy_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (t_date, code, hold["stock_name"], "SELL", curr_price, 1, sell_amount, score, strategy_type)
                )
            else:
                val = curr_price * 1
                holding_ret = ((curr_price - entry_price) / entry_price) * 100
                
                cursor.execute(
                    """
                    UPDATE ud_portfolio_holdings
                    SET current_price = ?, valuation = ?, holding_return = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (curr_price, val, holding_ret, row_id)
                )
                
                active_holdings_codes.append(code)

        # 3. Process entries (Buy)
        new_candidates = evals[
            (evals["total_score"] >= 70.0) & 
            (evals["is_candidate"] == 1) & 
            (~evals["stock_code"].isin(active_holdings_codes))
        ].copy()

        # Sort dynamically based on strategy type
        if strategy_type == "DIVIDEND":
            new_candidates = new_candidates.sort_values(
                by=["total_score", "dividend_yield", "market_cap"],
                ascending=[False, False, False]
            )
        else:
            new_candidates = new_candidates.sort_values(
                by=["total_score", "revenue_growth", "market_cap"],
                ascending=[False, False, False]
            )

        for _, row in new_candidates.iterrows():
            code = row["stock_code"]
            name = row["stock_name"]
            close_price = row["close_price"]
            score = row["total_score"]

            qty = 1
            buy_amount = close_price * qty

            cursor.execute(
                """
                INSERT INTO ud_portfolio_holdings (
                    stock_code, stock_name, entry_date, entry_price, quantity,
                    current_price, valuation, holding_return, score_at_entry,
                    exit_date, exit_price, score_at_exit, status, strategy_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, name, t_date, close_price, qty, close_price, buy_amount, 0.0, score, None, None, None, "ACTIVE", strategy_type)
            )

            cursor.execute(
                """
                INSERT INTO ud_portfolio_transactions (
                    trade_date, stock_code, stock_name, transaction_type,
                    price, quantity, amount, score, strategy_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (t_date, code, name, "BUY", close_price, qty, buy_amount, score, strategy_type)
            )

        # 4. Record history for t_date
        daily_return = ((current_total_asset - initial_balance) / initial_balance) * 100

        cursor.execute("SELECT max(total_asset) FROM ud_portfolio_history WHERE strategy_type = ?", (strategy_type,))
        hist_peak_row = cursor.fetchone()
        hist_peak = hist_peak_row[0] if (hist_peak_row and hist_peak_row[0]) else initial_balance
        peak_asset = max(hist_peak, current_total_asset)
        drawdown = ((peak_asset - current_total_asset) / peak_asset) * 100

        cursor.execute(
            """
            INSERT INTO ud_portfolio_history (
                trade_date, strategy_type, cash, valuation, total_asset, daily_return, drawdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (t_date, strategy_type, 0.0, current_total_asset, current_total_asset, daily_return, drawdown)
        )
        
        cursor.execute(
            """
            UPDATE ud_portfolio_status
            SET current_cash = ?, current_valuation = ?, total_asset = ?, total_return = ?, updated_at = CURRENT_TIMESTAMP
            WHERE strategy_type = ?
            """,
            (0.0, current_total_asset, current_total_asset, daily_return, strategy_type)
        )
        
        processed_days += 1

    # 5. Final summary metrics updates: MDD & Win Rate
    cursor.execute("SELECT max(drawdown) FROM ud_portfolio_history WHERE strategy_type = ?", (strategy_type,))
    mdd_row = cursor.fetchone()
    mdd = mdd_row[0] if (mdd_row and mdd_row[0]) else 0.0

    cursor.execute(
        """
        SELECT count(*), sum(case when holding_return > 0 then 1 else 0 end) 
        FROM ud_portfolio_holdings 
        WHERE status = 'CLOSED' AND strategy_type = ?
        """,
        (strategy_type,)
    )
    win_row = cursor.fetchone()
    total_closed = win_row[0] if win_row else 0
    won_closed = win_row[1] if (win_row and win_row[1]) else 0
    
    win_rate = (won_closed / total_closed * 100) if total_closed > 0 else 0.0

    cursor.execute(
        """
        UPDATE ud_portfolio_status
        SET mdd = ?, win_rate = ?, updated_at = CURRENT_TIMESTAMP
        WHERE strategy_type = ?
        """,
        (mdd, win_rate, strategy_type)
    )

    db.commit()

    return {
        "status": "success",
        "message": f"Successfully updated portfolio through {processed_days} trading days for {strategy_type}.",
        "processed_days": processed_days
    }
