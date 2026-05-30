import re

import pandas as pd


# DART API는 기업 유형 및 보고 주기에 따라 계정명이 달라질 수 있어
# 동일한 항목에 대해 복수의 계정명을 모두 매핑합니다.
ACCOUNT_COLUMNS = {
    # 자산 항목
    "유동자산": "current_assets",
    "비유동자산": "non_current_assets",
    "자산총계": "total_assets",
    # 부채 항목
    "유동부채": "current_liabilities",
    "비유동부채": "non_current_liabilities",
    "부채총계": "total_liabilities",
    # 자본 항목
    "자본총계": "total_equity",
    # 손익 항목 - 매출액 (금융/보험사는 '영업수익' 사용)
    "매출액": "revenue",
    "수익(매출액)": "revenue",
    "영업수익": "revenue",
    # 손익 항목 - 영업이익
    "영업이익": "operating_income",
    "영업이익(손실)": "operating_income",
    # 손익 항목 - 당기순이익 (연간/반기/분기 및 손실 표기 모두 처리)
    "당기순이익": "net_income",
    "당기순이익(손실)": "net_income",
    "반기순이익": "net_income",
    "반기순이익(손실)": "net_income",
    "분기순이익": "net_income",
    "분기순이익(손실)": "net_income",
    # 지배지분 당기순이익 (연결재무제표에서 별도 표기되는 경우)
    "당기순이익(손실)(지배지분)": "net_income",
    "당기순이익(지배지분)": "net_income",
    # 금융지주/은행용 이자수익 (매출액 누락 시 fallback)
    "이자수익": "interest_income",
}

PERIOD_COLUMNS = [
    ("thstrm_dt", "thstrm_amount"),
    ("frmtrm_dt", "frmtrm_amount"),
    ("bfefrmtrm_dt", "bfefrmtrm_amount"),
]

BASE_COLUMNS = [
    "rcept_no",
    "reprt_code",
    "bsns_year",
    "corp_code",
    "stock_code",
    "fs_div",
    "fs_nm",
    "currency",
    "fiscal_period",
]

OUTPUT_COLUMNS = [
    *BASE_COLUMNS,
    "current_assets",
    "non_current_assets",
    "total_assets",
    "current_liabilities",
    "non_current_liabilities",
    "total_liabilities",
    "total_equity",
    "revenue",
    "operating_income",
    "net_income",
    "debt_ratio",
    "current_ratio",
    "equity_ratio",
    "operating_margin",
    "net_margin",
]


def clean_financial_statement(dataframe: pd.DataFrame) -> pd.DataFrame:
    cfs = dataframe[dataframe["fs_div"].astype(str).str.strip() == "CFS"].copy()
    rows = []

    for _, row in cfs.iterrows():
        account_name = _to_text(row.get("account_nm", ""))
        output_column = ACCOUNT_COLUMNS.get(account_name)

        if output_column is None:
            continue

        for date_column, amount_column in PERIOD_COLUMNS:
            fiscal_period = _format_fiscal_period(row.get(date_column, ""))

            if not fiscal_period:
                continue

            rows.append(
                {
                    "rcept_no": _to_text(row.get("rcept_no", "")),
                    "reprt_code": _to_text(row.get("reprt_code", "")),
                    "bsns_year": _to_text(row.get("bsns_year", "")),
                    "corp_code": _to_text(row.get("corp_code", "")).zfill(8),
                    "stock_code": _to_text(row.get("stock_code", "")).zfill(6),
                    "fs_div": _to_text(row.get("fs_div", "")),
                    "fs_nm": _to_text(row.get("fs_nm", "")),
                    "currency": _to_text(row.get("currency", "")),
                    "fiscal_period": fiscal_period,
                    "account_column": output_column,
                    "amount": _to_int(row.get(amount_column, "")),
                }
            )

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    long_dataframe = pd.DataFrame(rows)
    wide = (
        long_dataframe.pivot_table(
            index=BASE_COLUMNS,
            columns="account_column",
            values="amount",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    for column in ACCOUNT_COLUMNS.values():
      if column not in wide.columns:
        wide[column] = pd.NA

    # 금융/지주사를 위해 매출액(revenue)이 누락(NaN)되었고 이자수익(interest_income)이 있는 경우 대체 적용
    if "revenue" in wide.columns and "interest_income" in wide.columns:
      wide["revenue"] = wide["revenue"].fillna(wide["interest_income"])

    wide["debt_ratio"] = _safe_ratio_column(
        wide["total_liabilities"],
        wide["total_equity"],
    )
    wide["current_ratio"] = _safe_ratio_column(
        wide["current_assets"],
        wide["current_liabilities"],
    )
    wide["equity_ratio"] = _safe_ratio_column(
        wide["total_equity"],
        wide["total_assets"],
    )
    wide["operating_margin"] = _safe_ratio_column(
        wide["operating_income"],
        wide["revenue"],
    )
    wide["net_margin"] = _safe_ratio_column(
        wide["net_income"],
        wide["revenue"],
    )

    return wide[OUTPUT_COLUMNS].sort_values(["stock_code", "fiscal_period"])


def _format_fiscal_period(value: object) -> str:
    matches = re.findall(r"\d{4}\.\d{2}", str(value))

    if not matches:
        return ""

    return matches[-1]


def _safe_ratio_column(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    ratio = numerator / denominator * 100
    ratio = ratio.where(denominator.notna() & (denominator != 0))

    return ratio.round(2)


def _to_int(value: object) -> int | None:
    text = _to_text(value)
    normalized = (
        text.replace(",", "")
        .replace("(", "-")
        .replace(")", "")
        .replace(" ", "")
    )

    # 빈 값은 0이 아닌 None으로 반환하여 실제 0과 구분
    if normalized in {"", "-"}:
        return None

    try:
        return int(normalized)
    except ValueError:
        return None


def _to_text(value: object) -> str:
    if pd.isna(value):
        return ""

    return str(value).strip()
