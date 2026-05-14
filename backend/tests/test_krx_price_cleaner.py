import pandas as pd

from pj_stock_backend.cleaners.krx_price_cleaner import clean_daily_prices


def test_clean_daily_prices_renames_and_formats_columns() -> None:
    raw_dataframe = pd.DataFrame(
        [
            {
                "BAS_DD": "20260512",
                "ISU_CD": "005930",
                "ISU_NM": " Samsung Electronics ",
                "MKT_NM": "KOSPI",
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

    cleaned = clean_daily_prices(raw_dataframe)

    assert cleaned.to_dict("records") == [
        {
            "trade_date": "20260512",
            "stock_code": "005930",
            "stock_name": "Samsung Electronics",
            "market": "KOSPI",
            "section": "Common Stock",
            "open_price": 72800,
            "high_price": 74500,
            "low_price": 72500,
            "close_price": 74000,
            "price_change": 1200,
            "change_rate": 1.65,
            "volume": 12345678,
            "trading_value": 912345678900,
            "market_cap": 441234567890000,
            "listed_shares": 5969782550,
        }
    ]
