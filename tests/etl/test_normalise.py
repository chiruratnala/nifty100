"""
Unit Tests for normalize_year()
Module: tests/etl/test_normalise.py
"""

import numpy as np

from src.etl.normalise import normalize_year


def test_norm_01_plain_string_year():
    assert normalize_year("2024") == "2024"


def test_norm_02_integer_year():
    assert normalize_year(2023) == "2023"


def test_norm_03_float_year():
    assert normalize_year(2022.0) == "2022"


def test_norm_04_fy_prefix_4_digit():
    assert normalize_year("FY2023") == "2023"


def test_norm_05_fy_prefix_2_digit():
    assert normalize_year("FY24") == "2024"


def test_norm_06_fy_space_separated():
    assert normalize_year("FY 2021") == "2021"


def test_norm_07_fy_hyphenated():
    assert normalize_year("FY-22") == "2022"


def test_norm_08_iso_yyyy_mm():
    assert normalize_year("2024-03") == "2024-03"


def test_norm_09_iso_yyyy_mm_dd():
    assert normalize_year("2023-03-31") == "2023-03"


def test_norm_10_dmy_format():
    assert normalize_year("31-03-2022") == "2022-03"


def test_norm_11_slash_separated_dmy():
    assert normalize_year("31/03/2021") == "2021-03"


def test_norm_12_month_name_and_4digit():
    assert normalize_year("March 2024") == "2024"


def test_norm_13_abbreviated_month_and_2digit():
    assert normalize_year("Mar-23") == "2023"


def test_norm_14_apostrophe_2digit():
    assert normalize_year("'24") == "2024"


def test_norm_15_whitespace_padded():
    assert normalize_year("   2020   ") == "2020"


def test_norm_16_none_input():
    assert normalize_year(None) is None


def test_norm_17_nan_float_input():
    assert normalize_year(np.nan) is None


def test_norm_18_empty_and_dash_strings():
    assert normalize_year("") is None
    assert normalize_year("-") is None


def test_norm_19_embedded_in_sentence():
    assert normalize_year("Annual Report 2022 Financials") == "2022"


def test_norm_20_unparseable_garbage():
    assert normalize_year("Q3_Unchecked_Text") is None
    assert normalize_year("abcdef") is None
