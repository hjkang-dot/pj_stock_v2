from pathlib import Path

import pandas as pd


def save_dataframe_csv(dataframe: pd.DataFrame, path: str | Path) -> Path:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    dataframe.to_csv(csv_path, index=False, encoding="utf-8-sig")

    return csv_path


def load_dataframe_csv(
    path: str | Path,
    dtype: str | dict[str, str] | None = None,
) -> pd.DataFrame:
    csv_path = Path(path)

    return pd.read_csv(csv_path, encoding="utf-8-sig", dtype=dtype)

