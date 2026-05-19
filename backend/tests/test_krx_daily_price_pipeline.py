import pytest

from pj_stock_backend.pipelines.krx_daily_price_pipeline import parse_base_date


def test_parse_base_date_accepts_yyyymmdd() -> None:
    assert parse_base_date("20260518") == "20260518"


def test_parse_base_date_rejects_invalid_date_format() -> None:
    with pytest.raises(ValueError, match="YYYYMMDD"):
        parse_base_date("2026-05-18")
