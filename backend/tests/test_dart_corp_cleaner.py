import pandas as pd

from pj_stock_backend.cleaners.dart_corp_cleaner import clean_corp_codes


def test_clean_corp_codes_keeps_only_listed_companies() -> None:
    raw_dataframe = pd.DataFrame(
        [
            {
                "corp_code": "00126380",
                "corp_name": " Samsung Electronics ",
                "stock_code": "5930",
                "modify_date": "20240501",
            },
            {
                "corp_code": "00000001",
                "corp_name": "Unlisted Company",
                "stock_code": "",
                "modify_date": "20240501",
            },
        ]
    )

    cleaned = clean_corp_codes(raw_dataframe)

    assert cleaned.to_dict("records") == [
        {
            "corp_code": "00126380",
            "corp_name": "Samsung Electronics",
            "stock_code": "005930",
            "modify_date": "20240501",
        }
    ]
