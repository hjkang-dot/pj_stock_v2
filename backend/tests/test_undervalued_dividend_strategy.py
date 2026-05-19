import pandas as pd

from pj_stock_backend.strategies.undervalued_dividend_strategy import (
    screen_undervalued_dividend_stocks,
)


def test_screen_undervalued_dividend_stocks_ranks_candidates() -> None:
    financial_statements = pd.DataFrame(
        [
            _financial_row(
                "001",
                "000001",
                "2023.12",
                revenue=80_000_000_000,
                operating_income=8_000_000_000,
            ),
            _financial_row(
                "001",
                "000001",
                "2024.12",
                revenue=90_000_000_000,
                operating_income=10_000_000_000,
            ),
            {
                "corp_code": "001",
                "stock_code": "000001",
                "fiscal_period": "2025.12",
                "revenue": 100_000_000_000,
                "total_equity": 100_000_000_000,
                "market_cap": 50_000_000_000,
                "net_income": 10_000_000_000,
                "operating_income": 12_000_000_000,
                "equity_ratio": 70.0,
                "debt_ratio": 40.0,
                "current_ratio": 180.0,
                "net_margin": 12.0,
                "operating_margin": 15.0,
            },
            _financial_row(
                "002",
                "000002",
                "2024.12",
                revenue=110_000_000_000,
                operating_income=1_000_000_000,
            ),
            {
                "corp_code": "002",
                "stock_code": "000002",
                "fiscal_period": "2025.12",
                "revenue": 100_000_000_000,
                "total_equity": 20_000_000_000,
                "market_cap": 200_000_000_000,
                "net_income": -1_000_000_000,
                "operating_income": -500_000_000,
                "equity_ratio": 10.0,
                "debt_ratio": 500.0,
                "current_ratio": 60.0,
                "net_margin": -1.0,
                "operating_margin": -1.0,
            },
        ]
    )
    dividends = pd.DataFrame(
        [
            _dividend_row("001", "000001", 2023, 450),
            _dividend_row("001", "000001", 2024, 480),
            _dividend_row("001", "000001", 2025, 500),
            _dividend_row("002", "000002", 2025, 0),
        ]
    )
    daily_prices = pd.DataFrame(
        [
            {
                "stock_code": "000001",
                "stock_name": "Good Dividend",
                "market": "KOSPI",
                "close_price": 10_000,
                "market_cap": 50_000_000_000,
                "trading_value": 2_000_000_000,
            },
            {
                "stock_code": "000002",
                "stock_name": "Weak Stock",
                "market": "KOSDAQ",
                "close_price": 20_000,
                "market_cap": 200_000_000_000,
                "trading_value": 100_000_000,
            },
        ]
    )
    stocks = pd.DataFrame(
        [
            {"stock_code": "000001", "listed_date": "20000101"},
            {"stock_code": "000002", "listed_date": "20240101"},
        ]
    )

    screened = screen_undervalued_dividend_stocks(
        financial_statements,
        dividends,
        daily_prices,
        stocks,
        as_of_year=2026,
    )

    assert screened.iloc[0]["stock_code"] == "000001"
    assert screened.iloc[0]["is_candidate"]
    assert screened.iloc[0]["per"] == 5.0
    assert screened.iloc[0]["pbr"] == 0.5
    assert screened.iloc[0]["dividend_yield"] == 5.0
    assert screened.iloc[0]["dividend_years"] == 3
    assert "000002" not in screened["stock_code"].to_list()


def _financial_row(
    corp_code: str,
    stock_code: str,
    fiscal_period: str,
    revenue: int,
    operating_income: int,
) -> dict[str, object]:
    return {
        "corp_code": corp_code,
        "stock_code": stock_code,
        "fiscal_period": fiscal_period,
        "revenue": revenue,
        "total_equity": 100_000_000_000,
        "market_cap": 50_000_000_000,
        "net_income": 10_000_000_000,
        "operating_income": operating_income,
        "equity_ratio": 70.0,
        "debt_ratio": 40.0,
        "current_ratio": 180.0,
        "net_margin": 12.0,
        "operating_margin": 15.0,
    }


def _dividend_row(
    corp_code: str,
    stock_code: str,
    fiscal_year: int,
    cash_dividend_per_share: int,
) -> dict[str, object]:
    return {
        "corp_code": corp_code,
        "corp_name": f"Corp {corp_code}",
        "stock_code": stock_code,
        "fiscal_year": fiscal_year,
        "cash_dividend_yield": pd.NA,
        "cash_dividend_payout_ratio": 30.0,
        "cash_dividend_per_eps_ratio": 30.0,
        "cash_dividend_per_share": cash_dividend_per_share,
        "cash_dividend_total": cash_dividend_per_share * 1_000_000,
    }
