import pytest

from pj_stock_backend.collectors.krx_collector import validate_market


def test_validate_market_accepts_kospi() -> None:
    assert validate_market("KOSPI") == "KOSPI"


def test_validate_market_accepts_kosdaq() -> None:
    assert validate_market("KOSDAQ") == "KOSDAQ"


def test_validate_market_normalizes_lowercase() -> None:
    assert validate_market("kospi") == "KOSPI"


def test_validate_market_rejects_unsupported_market() -> None:
    with pytest.raises(ValueError, match="Unsupported market"):
        validate_market("KONEX")
