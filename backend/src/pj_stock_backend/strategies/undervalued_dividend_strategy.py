from datetime import date

import pandas as pd


OUTPUT_COLUMNS = [
    "stock_code",
    "stock_name",
    "market",
    "close_price",
    "market_cap",
    "net_income",
    "total_equity",
    "debt_ratio",
    "roe",
    "per",
    "pbr",
    "dividend_yield",
    "cash_dividend_per_share",
    "payout_ratio",
    "dividend_years",
    "dividend_decrease_count",
    "financial_stability_score",
    "undervaluation_score",
    "shareholder_return_score",
    "market_governance_score",
    "total_score",
    "is_candidate",
]


def screen_undervalued_dividend_stocks(
    financial_statements: pd.DataFrame,
    dividends: pd.DataFrame,
    daily_prices: pd.DataFrame,
    stocks: pd.DataFrame,
    *,
    minimum_total_score: float = 60.0,
    as_of_year: int | None = None,
) -> pd.DataFrame:
    """Score stocks for an undervalued dividend strategy."""
    as_of_year = as_of_year or date.today().year

    growth_stock_codes = _revenue_and_operating_income_growth_stock_codes(
        financial_statements,
    )
    latest_financials = _latest_financials(financial_statements)
    latest_financials = latest_financials[
        latest_financials["stock_code"].isin(growth_stock_codes)
    ].copy()
    latest_dividends = _latest_dividends(dividends)
    dividend_years = _dividend_years(dividends)
    dividend_decrease_counts = _dividend_decrease_counts(dividends)

    screened = (
        latest_financials.merge(latest_dividends, on="corp_code", how="left")
        .merge(dividend_years, on="corp_code", how="left")
        .merge(dividend_decrease_counts, on="corp_code", how="left")
        .merge(daily_prices, on="stock_code", how="inner", suffixes=("", "_price"))
        .merge(stocks[["stock_code", "listed_date"]], on="stock_code", how="left")
    )

    screened["stock_name"] = screened["stock_name"].fillna(screened["corp_name"])
    screened["dividend_years"] = screened["dividend_years"].fillna(0).astype("int64")
    screened["dividend_decrease_count"] = (
        screened["dividend_decrease_count"].fillna(0).astype("int64")
    )

    screened["roe"] = _safe_ratio(screened["net_income"], screened["total_equity"]) * 100
    screened["per"] = _safe_ratio(screened["market_cap"], screened["net_income"])
    screened["pbr"] = _safe_ratio(screened["market_cap"], screened["total_equity"])
    screened["dividend_yield"] = screened["cash_dividend_yield"]
    calculated_yield = _safe_ratio(
        screened["cash_dividend_per_share"],
        screened["close_price"],
    ) * 100
    screened["dividend_yield"] = screened["dividend_yield"].fillna(calculated_yield)
    screened["payout_ratio"] = screened["cash_dividend_payout_ratio"].fillna(
        screened["cash_dividend_per_eps_ratio"],
    )
    screened["listed_years"] = as_of_year - pd.to_numeric(
        screened["listed_date"].astype(str).str[:4],
        errors="coerce",
    )

    screened["financial_stability_score"] = screened.apply(
        _score_financial_stability,
        axis=1,
    )
    screened["undervaluation_score"] = screened.apply(_score_undervaluation, axis=1)
    screened["shareholder_return_score"] = screened.apply(
        _score_shareholder_return,
        axis=1,
    )
    screened["market_governance_score"] = screened.apply(
        _score_market_governance,
        axis=1,
    )

    screened["total_score"] = (
        screened["financial_stability_score"]
        + screened["undervaluation_score"]
        + screened["shareholder_return_score"]
        + screened["market_governance_score"]
    ).round(2)
    screened["is_candidate"] = (
        (screened["total_score"] >= minimum_total_score)
        & (screened["net_income"] > 0)
        & (screened["total_equity"] > 0)
        & (screened["market_cap"] > 0)
        & (screened["cash_dividend_per_share"] > 0)
    )

    return (
        screened[OUTPUT_COLUMNS]
        .sort_values(
            ["is_candidate", "total_score", "dividend_yield", "market_cap"],
            ascending=[False, False, False, False],
        )
        .reset_index(drop=True)
    )


def _latest_financials(financial_statements: pd.DataFrame) -> pd.DataFrame:
    financials = financial_statements.copy()
    financials["fiscal_period_sort"] = pd.to_numeric(
        financials["fiscal_period"].astype(str).str.replace(".", "", regex=False),
        errors="coerce",
    )

    return (
        financials.sort_values(["stock_code", "fiscal_period_sort"])
        .groupby("stock_code", as_index=False)
        .tail(1)
        .drop(columns=["fiscal_period_sort"])
    )


def _revenue_and_operating_income_growth_stock_codes(
    financial_statements: pd.DataFrame,
) -> set[str]:
    financials = financial_statements.copy()
    financials["fiscal_period_sort"] = pd.to_numeric(
        financials["fiscal_period"].astype(str).str.replace(".", "", regex=False),
        errors="coerce",
    )
    financials["revenue"] = pd.to_numeric(financials["revenue"], errors="coerce")
    financials["operating_income"] = pd.to_numeric(
        financials["operating_income"],
        errors="coerce",
    )

    growth_stock_codes = set()

    for stock_code, group in financials.groupby("stock_code"):
        comparable = group.sort_values("fiscal_period_sort")[
            ["revenue", "operating_income"]
        ].dropna()

        if len(comparable) < 2:
            continue

        revenue_growing = (comparable["revenue"].diff().dropna() > 0).all()
        operating_income_growing = (
            comparable["operating_income"].diff().dropna() > 0
        ).all()

        if revenue_growing and operating_income_growing:
            growth_stock_codes.add(stock_code)

    return growth_stock_codes


def _latest_dividends(dividends: pd.DataFrame) -> pd.DataFrame:
    dividend_data = dividends.copy()
    dividend_data["fiscal_year"] = pd.to_numeric(
        dividend_data["fiscal_year"],
        errors="coerce",
    )
    if "stock_code" in dividend_data.columns:
        dividend_data = dividend_data.drop(columns=["stock_code"])

    return (
        dividend_data.sort_values(["corp_code", "fiscal_year"])
        .groupby("corp_code", as_index=False)
        .tail(1)
    )


def _dividend_years(dividends: pd.DataFrame) -> pd.DataFrame:
    dividend_data = dividends.copy()
    if "stock_code" in dividend_data.columns:
        dividend_data = dividend_data.drop(columns=["stock_code"])
    dividend_data["has_cash_dividend"] = (
        pd.to_numeric(dividend_data["cash_dividend_per_share"], errors="coerce").fillna(0)
        > 0
    ) | (
        pd.to_numeric(dividend_data["cash_dividend_total"], errors="coerce").fillna(0) > 0
    )

    return (
        dividend_data[dividend_data["has_cash_dividend"]]
        .groupby("corp_code", as_index=False)["fiscal_year"]
        .nunique()
        .rename(columns={"fiscal_year": "dividend_years"})
    )


def _dividend_decrease_counts(dividends: pd.DataFrame) -> pd.DataFrame:
    dividend_data = dividends.copy()
    if "stock_code" in dividend_data.columns:
        dividend_data = dividend_data.drop(columns=["stock_code"])

    dividend_data["fiscal_year"] = pd.to_numeric(
        dividend_data["fiscal_year"],
        errors="coerce",
    )
    dividend_data["cash_dividend_per_share"] = pd.to_numeric(
        dividend_data["cash_dividend_per_share"],
        errors="coerce",
    ).fillna(0)

    rows = []
    for corp_code, group in dividend_data.groupby("corp_code"):
        dividend_history = group.sort_values("fiscal_year")["cash_dividend_per_share"]
        decrease_count = int((dividend_history.diff().dropna() < 0).sum())
        rows.append(
            {
                "corp_code": corp_code,
                "dividend_decrease_count": decrease_count,
            }
        )

    return pd.DataFrame(rows)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    ratio = numerator / denominator

    return ratio.where(denominator.notna() & (denominator > 0))


def _score_financial_stability(row: pd.Series) -> int:
    score = 0
    score += _range_score(row["roe"], [(15, 12), (10, 9), (5, 6), (0, 3)], 0)
    score += _inverse_range_score(row["debt_ratio"], [(100, 8), (200, 5), (400, 2)])

    return min(score, 20)


def _score_undervaluation(row: pd.Series) -> int:
    score = 0
    score += _inverse_range_score(row["per"], [(6, 15), (10, 12), (15, 8), (25, 4)])
    score += _inverse_range_score(row["pbr"], [(0.6, 15), (1.0, 12), (1.5, 8), (2.5, 4)])

    return min(score, 30)


def _score_shareholder_return(row: pd.Series) -> int:
    score = 0
    score += _payout_score(row["payout_ratio"])
    score += _range_score(row["dividend_years"], [(3, 15), (2, 10), (1, 5)], 0)
    score -= min(int(row["dividend_decrease_count"]) * 5, 15)

    return max(min(score, 30), 0)


def _score_market_governance(row: pd.Series) -> int:
    score = 5 if row["market"] == "KOSPI" else 3
    score += _range_score(
        row["market_cap"],
        [(1_000_000_000_000, 5), (300_000_000_000, 4), (100_000_000_000, 2)],
        1,
    )
    score += _range_score(
        row["trading_value"],
        [(5_000_000_000, 5), (1_000_000_000, 4), (300_000_000, 2)],
        1,
    )
    score += _range_score(row["listed_years"], [(10, 5), (5, 4), (3, 2)], 1)

    return min(score, 20)


def _range_score(value: object, thresholds: list[tuple[float, int]], default: int) -> int:
    numeric_value = _to_float(value)

    if numeric_value is None:
        return default

    for threshold, score in thresholds:
        if numeric_value >= threshold:
            return score

    return default


def _inverse_range_score(value: object, thresholds: list[tuple[float, int]]) -> int:
    numeric_value = _to_float(value)

    if numeric_value is None or numeric_value <= 0:
        return 0

    for threshold, score in thresholds:
        if numeric_value <= threshold:
            return score

    return 0


def _payout_score(value: object) -> int:
    payout_ratio = _to_float(value)

    if payout_ratio is None or payout_ratio <= 0:
        return 0
    if 20 <= payout_ratio <= 60:
        return 15
    if 10 <= payout_ratio <= 80:
        return 10

    return 5


def _positive(value: object) -> bool:
    numeric_value = _to_float(value)

    return numeric_value is not None and numeric_value > 0


def _to_float(value: object) -> float | None:
    if pd.isna(value):
        return None

    return float(value)
