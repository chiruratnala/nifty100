import pytest
import pandas as pd
from src.etl.normaliser import normalize_ticker, normalize_year


# ============================================================
# normalize_ticker() — 20 tests
# ============================================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("tcs", "TCS"),
        (" TCS", "TCS"),
        ("TCS ", "TCS"),
        (" TCS ", "TCS"),
        ("hdfcbank", "HDFCBANK"),
        (" HDFCbank ", "HDFCBANK"),
        ("reliance", "RELIANCE"),
        (" RELIANCE ", "RELIANCE"),
        ("infy", "INFY"),
        ("  infy", "INFY"),
        ("infy  ", "INFY"),
        ("  infy  ", "INFY"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        (" BAJAJ-AUTO ", "BAJAJ-AUTO"),
        ("M&M", "M&M"),
        (" m&m ", "M&M"),
        ("ITC", "ITC"),
        ("itc", "ITC"),
        ("SBIN", "SBIN"),
        (" sbin ", "SBIN"),
    ],
)
def test_normalize_ticker(value, expected):
    assert normalize_ticker(value) == expected


# ============================================================
# normalize_year() — 20 tests
# ============================================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("Mar-23", "2023-03"),
        ("Mar 23", "2023-03"),
        ("March-2023", "2023-03"),
        ("2023", "2023-03"),
        ("FY23", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("2023-03", "2023-03"),
        ("Mar-24", "2024-03"),
        ("Mar 24", "2024-03"),
        ("March-2024", "2024-03"),
        ("FY24", "2024-03"),
        ("Dec-23", "2023-12"),
        ("Jun-24", "2024-06"),
        ("Sep-24", "2024-09"),
        ("Sep-23", "2023-09"),
        ("Mar-2019", "2019-03"),
        ("Dec-2020", "2020-12"),
        ("Jun-2021", "2021-06"),
        ("2022-03", "2022-03"),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected
