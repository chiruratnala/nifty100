import pytest
import pandas as pd
from src.analytics.cashflow_kpis import (
    compute_fcf,
    compute_capex_intensity,
    compute_fcf_conversion,
    compute_5yr_cfo_quality,
    classify_capital_allocation_pattern,
)

def test_1_fcf_normal_and_negative():
    # CFO 1000, CFI -400 -> FCF = 600
    assert compute_fcf(1000.0, -400.0) == 600.0
    # CFO 200, CFI -500 -> FCF = -300 (negative allowed)
    assert compute_fcf(200.0, -500.0) == -300.0
    assert compute_fcf(None, -500.0) is None

def test_2_capex_intensity_thresholds():
    # 2% -> Asset Light
    val1, label1 = compute_capex_intensity(-20.0, 1000.0)
    assert val1 == 2.0
    assert label1 == "Asset Light"

    # 5% -> Moderate
    val2, label2 = compute_capex_intensity(-50.0, 1000.0)
    assert val2 == 5.0
    assert label2 == "Moderate"

    # 10% -> Capital Intensive
    val3, label3 = compute_capex_intensity(-100.0, 1000.0)
    assert val3 == 10.0
    assert label3 == "Capital Intensive"

def test_3_capex_intensity_zero_sales():
    val, label = compute_capex_intensity(-50.0, 0.0)
    assert val is None
    assert label is None

def test_4_fcf_conversion_normal_and_zero_op():
    # FCF 500, Operating Profit 1000 -> 50.0%
    assert compute_fcf_conversion(500.0, 1000.0) == 50.0
    # Operating Profit <= 0 -> returns None
    assert compute_fcf_conversion(500.0, 0.0) is None
    assert compute_fcf_conversion(500.0, -200.0) is None

def test_5_cfo_quality_scores():
    df_high = pd.DataFrame({
        "year": [f"202{i}-03" for i in range(5)],
        "cfo": [120.0] * 5,
        "pat": [100.0] * 5
    })
    score_high, label_high = compute_5yr_cfo_quality(df_high)
    assert score_high == 1.2
    assert label_high == "High Quality"

    df_accrual = pd.DataFrame({
        "year": [f"202{i}-03" for i in range(5)],
        "cfo": [30.0] * 5,
        "pat": [100.0] * 5
    })
    score_acc, label_acc = compute_5yr_cfo_quality(df_accrual)
    assert score_acc == 0.3
    assert label_acc == "Accrual Risk"

def test_6_cfo_quality_negative_pat():
    df_neg = pd.DataFrame({
        "year": [f"202{i}-03" for i in range(5)],
        "cfo": [50.0] * 5,
        "pat": [-20.0] * 5
    })
    score, label = compute_5yr_cfo_quality(df_neg)
    assert score is None
    assert label == "Accrual Risk"

def test_7_capital_allocation_patterns():
    # (+, -, -) with standard quality -> Reinvestor
    assert classify_capital_allocation_pattern(500, -200, -100, 1.0)[3] == "Reinvestor"
    # (+, -, -) with high quality -> Shareholder Returns
    assert classify_capital_allocation_pattern(500, -200, -100, 1.5)[3] == "Shareholder Returns"
    # (+, +, -) -> Liquidating Assets
    assert classify_capital_allocation_pattern(500, 200, -100)[3] == "Liquidating Assets"
    # (-, +, +) -> Distress Signal
    assert classify_capital_allocation_pattern(-500, 200, 100)[3] == "Distress Signal"
    # (-, -, +) -> Growth Funded by Debt
    assert classify_capital_allocation_pattern(-500, -200, 100)[3] == "Growth Funded by Debt"

def test_8_capital_allocation_rare_patterns():
    # (+, +, +) -> Cash Accumulator
    assert classify_capital_allocation_pattern(100, 100, 100)[3] == "Cash Accumulator"
    # (-, -, -) -> Pre-Revenue
    assert classify_capital_allocation_pattern(-100, -100, -100)[3] == "Pre-Revenue"
    # (+, -, +) -> Mixed
    assert classify_capital_allocation_pattern(100, -100, 100)[3] == "Mixed"
