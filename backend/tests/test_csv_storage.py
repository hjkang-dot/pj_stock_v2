import pandas as pd

from pj_stock_backend.storage.csv_storage import (
    load_dataframe_csv,
    save_dataframe_csv,
)


def test_save_and_load_dataframe_csv(tmp_path) -> None:
    dataframe = pd.DataFrame(
        [
            {
                "stock_code": "005930",
                "stock_name": "Samsung Electronics",
                "market": "KOSPI",
            }
        ]
    )
    csv_path = tmp_path / "stocks.csv"

    saved_path = save_dataframe_csv(dataframe, csv_path)
    loaded_dataframe = load_dataframe_csv(saved_path, dtype={"stock_code": "string"})

    assert saved_path == csv_path
    assert loaded_dataframe.to_dict("records") == dataframe.to_dict("records")
