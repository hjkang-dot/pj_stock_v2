import pandas as pd

from pj_stock_backend.cleaners.dart_financial_cleaner import clean_financial_statement


def test_clean_financial_statement_builds_one_row_per_stock_and_period() -> None:
    raw_dataframe = pd.DataFrame(
        [
            _financial_row("CFS", "자산총계", "100,000", "90,000", "80,000"),
            _financial_row("CFS", "부채총계", "40,000", "30,000", "20,000"),
            _financial_row("CFS", "자본총계", "60,000", "60,000", "60,000"),
            _financial_row("CFS", "매출액", "200,000", "180,000", "160,000"),
            _financial_row("CFS", "영업이익", "20,000", "18,000", "16,000"),
            _financial_row("CFS", "당기순이익(손실)", "10,000", "9,000", "8,000"),
            _financial_row("OFS", "자산총계", "1", "1", "1"),
        ]
    )

    cleaned = clean_financial_statement(raw_dataframe)

    assert len(cleaned) == 3

    current = cleaned[cleaned["fiscal_period"] == "2024.12"].iloc[0]

    assert current["stock_code"] == "005930"
    assert current["fs_div"] == "CFS"
    assert current["total_assets"] == 100000
    assert current["total_liabilities"] == 40000
    assert current["total_equity"] == 60000
    assert current["revenue"] == 200000
    assert current["operating_income"] == 20000
    assert current["net_income"] == 10000
    assert current["debt_ratio"] == 66.67
    assert current["equity_ratio"] == 60.0
    assert current["operating_margin"] == 10.0
    assert current["net_margin"] == 5.0


def _financial_row(
    fs_div: str,
    account_name: str,
    current_amount: str,
    previous_amount: str,
    before_previous_amount: str,
) -> dict[str, str]:
    return {
        "rcept_no": "20250311001085",
        "reprt_code": "11011",
        "bsns_year": "2024",
        "corp_code": "00126380",
        "stock_code": "5930",
        "fs_div": fs_div,
        "fs_nm": "Consolidated Financial Statements",
        "account_nm": account_name,
        "thstrm_dt": "2024.12.31",
        "thstrm_amount": current_amount,
        "frmtrm_dt": "2023.12.31",
        "frmtrm_amount": previous_amount,
        "bfefrmtrm_dt": "2022.12.31",
        "bfefrmtrm_amount": before_previous_amount,
        "currency": "KRW",
    }
