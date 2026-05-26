from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from pj_stock_backend.core.config import settings
from pj_stock_backend.db.sqlite import get_connection
from pj_stock_backend.pipelines.krx_daily_price_pipeline import (
    parse_base_date,
    parse_date_range,
    run_krx_daily_price_db_sync,
)


def test_parse_base_date_accepts_yyyymmdd() -> None:
    assert parse_base_date("20260518") == "20260518"


def test_parse_base_date_rejects_invalid_date_format() -> None:
    with pytest.raises(ValueError, match="YYYYMMDD"):
        parse_base_date("2026-05-18")


def test_parse_date_range_defaults_to_recent_year() -> None:
    assert parse_date_range(
        start_date=None,
        end_date="today",
        days=365,
        today=date(2026, 5, 26),
    ) == ("20250527", "20260526")


def test_parse_date_range_accepts_explicit_dates() -> None:
    assert parse_date_range(
        start_date="20260520",
        end_date="20260522",
        days=365,
    ) == ("20260520", "20260522")


def test_run_krx_daily_price_db_sync_upserts_cleaned_prices(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        settings,
        "database_url",
        f"sqlite:///{tmp_path / 'app.db'}",
    )

    def fake_fetcher(market: str, base_date: str) -> pd.DataFrame:
        if market == "KOSDAQ":
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "BAS_DD": base_date,
                    "ISU_CD": "005930",
                    "ISU_NM": "Samsung Electronics",
                    "MKT_NM": market,
                    "SECT_TP_NM": "Common Stock",
                    "TDD_CLSPRC": "74,000",
                    "CMPPREVDD_PRC": "+1,200",
                    "FLUC_RT": "+1.65",
                    "TDD_OPNPRC": "72,800",
                    "TDD_HGPRC": "74,500",
                    "TDD_LWPRC": "72,500",
                    "ACC_TRDVOL": "12,345,678",
                    "ACC_TRDVAL": "912,345,678,900",
                    "MKTCAP": "441,234,567,890,000",
                    "LIST_SHRS": "5,969,782,550",
                }
            ]
        )

    saved_rows = run_krx_daily_price_db_sync(
        start_date="20260522",
        end_date="20260522",
        fetcher=fake_fetcher,
    )

    connection = get_connection()
    try:
        row = connection.execute(
            """
            select trade_date, stock_code, close_price, trading_value
            from daily_prices
            where trade_date = '20260522'
              and stock_code = '005930'
            """
        ).fetchone()
    finally:
        connection.close()

    assert saved_rows == 1
    assert dict(row) == {
        "trade_date": "20260522",
        "stock_code": "005930",
        "close_price": 74000,
        "trading_value": 912345678900,
    }
