import pytest
import pandas as pd
from src.analytics.cagr import (
    compute_cagr,
    calculate_series_cagr,
    compute_company_cagrs,
    FLAG_NORMAL,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
)

def test_1_cagr_normal_positive_growth():
    # 100 to 200 over 3 years -> 25.99%
    val, flag = compute_cagr(100.0, 200.0, 3)
    assert val == 25.99
    assert flag == FLAG_NORMAL

def test_2_cagr_normal_positive_decline():
    # 200 to 100 over 3 years -> -20.63%
    val, flag = compute_cagr(200.0, 100.0, 3)
    assert val == -20.63
    assert flag == FLAG_NORMAL

def test_3_cagr_decline_to_loss():
    # Positive start (500) to Negative end (-100) -> DECLINE_TO_LOSS
    val, flag = compute_cagr(500.0, -100.0, 3)
    assert val is None
    assert flag == FLAG_DECLINE_TO_LOSS

def test_4_cagr_turnaround():
    # Negative start (-200) to Positive end (300) -> TURNAROUND
    val, flag = compute_cagr(-200.0, 300.0, 5)
    assert val is None
    assert flag == FLAG_TURNAROUND

def test_5_cagr_both_negative():
    # Negative start (-500) to Negative end (-200) -> BOTH_NEGATIVE
    val, flag = compute_cagr(-500.0, -200.0, 3)
    assert val is None
    assert flag == FLAG_BOTH_NEGATIVE

def test_6_cagr_zero_base():
    # Start = 0 -> ZERO_BASE
    val, flag = compute_cagr(0.0, 500.0, 5)
    assert val is None
    assert flag == FLAG_ZERO_BASE

def test_7_cagr_insufficient_periods_or_invalid():
    # Period <= 0 or None values
    val1, flag1 = compute_cagr(100.0, 200.0, 0)
    assert val1 is None
    assert flag1 == FLAG_INSUFFICIENT

    val2, flag2 = compute_cagr(None, 200.0, 3)
    assert val2 is None
    assert flag2 == FLAG_INSUFFICIENT

def test_8_series_cagr_insufficient_data():
    # DataFrame with only 2 rows cannot compute 3Y CAGR (needs 4 points)
    df = pd.DataFrame({
        "year": ["2023-03", "2024-03"],
        "sales": [100.0, 150.0]
    })
    val, flag = calculate_series_cagr(df, "sales", 3)
    assert val is None
    assert flag == FLAG_INSUFFICIENT

def test_9_series_cagr_exact_points():
    # 4 rows -> Exactly 3 periods
    df = pd.DataFrame({
        "year": ["2021-03", "2022-03", "2023-03", "2024-03"],
        "sales": [1000.0, 1100.0, 1210.0, 1331.0]
    })
    val, flag = calculate_series_cagr(df, "sales", 3)
    assert val == 10.0
    assert flag == FLAG_NORMAL

def test_10_company_cagrs_multi_window():
    years = [f"201{i}-03" for i in range(4, 10)] + [f"202{i}-03" for i in range(0, 5)]  # 11 years
    df = pd.DataFrame({
        "year": years,
        "sales": [100.0 * (1.10 ** i) for i in range(11)],
        "net_profit": [10.0 * (1.12 ** i) for i in range(11)],
        "eps": [5.0 * (1.08 ** i) for i in range(11)]
    })
    res = compute_company_cagrs(df)
    assert res["revenue_cagr_3yr"] == 10.0
    assert res["revenue_cagr_3yr_flag"] == FLAG_NORMAL
    assert res["pat_cagr_5yr"] == 12.0
    assert res["pat_cagr_5yr_flag"] == FLAG_NORMAL
    assert res["eps_cagr_10yr"] == 8.0
    assert res["eps_cagr_10yr_flag"] == FLAG_NORMAL
