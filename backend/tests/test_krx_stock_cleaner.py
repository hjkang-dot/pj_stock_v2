import pandas as pd

from pj_stock_backend.cleaners.krx_stock_cleaner import clean_listed_stocks


def test_clean_listed_stocks_renames_and_formats_columns() -> None:
    raw_dataframe = pd.DataFrame(
        [
            {
                "ISU_SRT_CD": "5930",
                "ISU_ABBRV": " Samsung Electronics ",
                "ISU_NM": " Samsung Electronics Common Stock ",
                "MKT_TP_NM": "KOSPI",
                "SECUGRP_NM": "Stock",
                "SECT_TP_NM": "Common Stock",
                "LIST_DD": "19750611",
                "LIST_SHRS": "5,969,782,550",
            }
        ]
    )

    cleaned = clean_listed_stocks(raw_dataframe)

    assert cleaned.to_dict("records") == [
        {
            "stock_code": "005930",
            "stock_name": "Samsung Electronics",
            "full_stock_name": "Samsung Electronics Common Stock",
            "market": "KOSPI",
            "security_group": "Stock",
            "sector": "Common Stock",
            "listed_date": "19750611",
            "listed_shares": 5969782550,
        }
    ]
