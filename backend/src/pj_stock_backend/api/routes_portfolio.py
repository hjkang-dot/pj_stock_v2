import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from pj_stock_backend.db.sqlite import get_db
from pj_stock_backend.services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class PortfolioInitializeRequest(BaseModel):
    initial_balance: float = 100000000.0
    strategy_type: str = "DIVIDEND"


class PortfolioSummaryResponse(BaseModel):
    initial_balance: float
    current_cash: float
    current_valuation: float
    total_asset: float
    mdd: float
    total_return: float
    win_rate: float
    updated_at: str


class PortfolioHoldingItem(BaseModel):
    id: int | None = None
    stock_code: str
    stock_name: str
    entry_date: str
    entry_price: float
    quantity: int
    current_price: float
    valuation: float
    holding_return: float
    score_at_entry: float | None = None
    updated_at: str
    exit_date: str | None = None
    exit_price: float | None = None
    score_at_exit: float | None = None
    status: str = "ACTIVE"


class PortfolioHistoryItem(BaseModel):
    trade_date: str
    cash: float
    valuation: float
    total_asset: float
    daily_return: float
    drawdown: float


class PortfolioTransactionItem(BaseModel):
    id: int
    trade_date: str
    stock_code: str
    stock_name: str
    transaction_type: str
    price: float
    quantity: int
    amount: float
    score: float | None = None
    created_at: str


@router.post("/initialize")
def initialize_virtual_portfolio(
    request: PortfolioInitializeRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Clear portfolio history and initialize with fresh cash on the latest available trade date."""
    res = portfolio_service.initialize_portfolio(db, request.initial_balance, request.strategy_type)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/update")
def update_virtual_portfolio(
    strategy_type: str = Query("DIVIDEND"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Manually step the portfolio forward using any new trade dates since the last check."""
    res = portfolio_service.update_portfolio_to_latest(db, strategy_type)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.get("/summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(
    strategy_type: str = Query("DIVIDEND"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve the overall stats of the portfolio (balance, return, MDD, win rate)."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT initial_balance, current_cash, current_valuation, total_asset,
               mdd, total_return, win_rate, updated_at
        FROM ud_portfolio_status
        WHERE strategy_type = ?
        LIMIT 1
        """,
        (strategy_type,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Portfolio not initialized yet.")
        
    return {
        "initial_balance": row[0],
        "current_cash": row[1],
        "current_valuation": row[2],
        "total_asset": row[3],
        "mdd": row[4],
        "total_return": row[5],
        "win_rate": row[6],
        "updated_at": row[7],
    }


@router.get("/holdings", response_model=list[PortfolioHoldingItem])
def get_portfolio_holdings(
    strategy_type: str = Query("DIVIDEND"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve all mock investment stock holding and trade records, ordered by return rate descending."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, stock_code, stock_name, entry_date, entry_price, quantity,
               current_price, valuation, holding_return, score_at_entry, updated_at,
               exit_date, exit_price, score_at_exit, status
        FROM ud_portfolio_holdings
        WHERE strategy_type = ?
        ORDER BY holding_return DESC
        """,
        (strategy_type,)
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "stock_code": r[1],
            "stock_name": r[2],
            "entry_date": r[3],
            "entry_price": r[4],
            "quantity": r[5],
            "current_price": r[6],
            "valuation": r[7],
            "holding_return": r[8],
            "score_at_entry": r[9],
            "updated_at": r[10],
            "exit_date": r[11],
            "exit_price": r[12],
            "score_at_exit": r[13],
            "status": r[14],
        }
        for r in rows
    ]

class HoldingChartPoint(BaseModel):
    trade_date: str
    close_price: float
    return_rate: float


@router.get("/holding/{holding_id}/chart", response_model=list[HoldingChartPoint])
def get_holding_chart(
    holding_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve day-by-day price and return rate history of a specific trade holding from entry to exit."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT stock_code, entry_date, exit_date, entry_price
        FROM ud_portfolio_holdings
        WHERE id = ?
        """,
        (holding_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Holding record not found.")

    stock_code, entry_date, exit_date, entry_price = row[0], row[1], row[2], row[3]

    if not exit_date:
        cursor.execute("SELECT max(trade_date) FROM daily_prices")
        latest_date_row = cursor.fetchone()
        end_date = latest_date_row[0] if (latest_date_row and latest_date_row[0]) else entry_date
    else:
        end_date = exit_date

    cursor.execute(
        """
        SELECT trade_date, close_price
        FROM daily_prices
        WHERE stock_code = ? AND trade_date >= ? AND trade_date <= ?
        ORDER BY trade_date ASC
        """,
        (stock_code, entry_date, end_date)
    )
    rows = cursor.fetchall()

    points = []
    for r in rows:
        t_date = r[0]
        close_price = float(r[1])
        return_rate = ((close_price - entry_price) / entry_price) * 100
        points.append({
            "trade_date": t_date,
            "close_price": close_price,
            "return_rate": return_rate
        })
    
    return points


@router.get("/history", response_model=list[PortfolioHistoryItem])
def get_portfolio_history(
    strategy_type: str = Query("DIVIDEND"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve the day-by-day asset history for plotting."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT trade_date, cash, valuation, total_asset, daily_return, drawdown
        FROM ud_portfolio_history
        WHERE strategy_type = ?
        ORDER BY trade_date ASC
        """,
        (strategy_type,)
    )
    rows = cursor.fetchall()
    return [
        {
            "trade_date": r[0],
            "cash": r[1],
            "valuation": r[2],
            "total_asset": r[3],
            "daily_return": r[4],
            "drawdown": r[5],
        }
        for r in rows
    ]


@router.get("/transactions", response_model=list[PortfolioTransactionItem])
def get_portfolio_transactions(
    strategy_type: str = Query("DIVIDEND"),
    limit: int = Query(50, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve transaction logs for the portfolio."""
    cursor = db.cursor()
    cursor.execute(
        f"""
        SELECT id, trade_date, stock_code, stock_name, transaction_type,
               price, quantity, amount, score, created_at
        FROM ud_portfolio_transactions
        WHERE strategy_type = ?
        ORDER BY trade_date DESC, id DESC
        LIMIT {limit}
        """,
        (strategy_type,)
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "trade_date": r[1],
            "stock_code": r[2],
            "stock_name": r[3],
            "transaction_type": r[4],
            "price": r[5],
            "quantity": r[6],
            "amount": r[7],
            "score": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]
