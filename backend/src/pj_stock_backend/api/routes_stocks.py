import math
from typing import Any
import sqlite3

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from pj_stock_backend.db.sqlite import get_db
from pj_stock_backend.repositories import stock_repository

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class StockItem(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    security_group: str | None = None
    sector: str | None = None
    listed_date: str | None = None
    listed_shares: int | None = None
    is_active: int


class StockListResponse(BaseModel):
    items: list[StockItem]
    total: int
    page: int
    size: int
    pages: int


@router.get("", response_model=StockListResponse)
def list_stocks(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search query for stock code, name, or sector"),
    market: str | None = Query(None, description="Filter by market (e.g. KOSPI, KOSDAQ)"),
    db: sqlite3.Connection = Depends(get_db),
) -> Any:
    """Retrieve a list of KOSPI/KOSDAQ stocks with pagination and search."""
    offset = (page - 1) * size

    # Fetch total matching count
    total = stock_repository.count_stocks(
        db,
        market=market,
        is_active=1,
        search=search,
    )

    # Fetch paginated rows
    stocks_df = stock_repository.get_stocks(
        db,
        market=market,
        is_active=1,
        search=search,
        limit=size,
        offset=offset,
    )

    # Replace NaN with None so Pydantic validation passes
    import pandas as pd
    stocks_df = stocks_df.where(pd.notnull(stocks_df), None)

    items = stocks_df.to_dict("records")
    pages = math.ceil(total / size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
