import pytest
from src.analytics.ratios import (
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_net_debt,
    compute_asset_turnover,
)

def test_1_de_normal_and_zero_borrowings():
    # Zero borrowings must return 0.0, not None
    de, flag = compute_debt_to_equity(0.0, 100.0, 900.0)
    assert de == 0.0
    assert flag is False

    # Normal D/E
    de_norm, flag_norm = compute_debt_to_equity(500.0, 100.0, 900.0)
    assert de_norm == 0.5
    assert flag_norm is False

def test_2_de_negative_equity_returns_none():
    de, flag = compute_debt_to_equity(500.0, 100.0, -200.0)
    assert de is None
    assert flag is False

def test_3_de_high_leverage_flag_non_financials():
    # D/E = 6.0 > 5.0 in Industrials -> High leverage flag True
    de, flag = compute_debt_to_equity(6000.0, 100.0, 900.0, broad_sector="Industrials")
    assert de == 6.0
    assert flag is True

def test_4_de_financials_carve_out_suppresses_flag():
    # D/E = 8.0 > 5.0 in Financials -> High leverage flag False
    de, flag = compute_debt_to_equity(8000.0, 100.0, 900.0, broad_sector="Financials")
    assert de == 8.0
    assert flag is False

def test_5_icr_zero_interest_debt_free():
    # Zero interest returns (None, "Debt Free", False)
    icr, label, warning = compute_interest_coverage(operating_profit=500.0, other_income=50.0, interest=0.0)
    assert icr is None
    assert label == "Debt Free"
    assert warning is False

def test_6_icr_solvency_warning_flag():
    # EBIT = 100, Interest = 80 -> ICR = 1.25 (< 1.5) -> Solvency Risk
    icr, label, warning = compute_interest_coverage(operating_profit=90.0, other_income=10.0, interest=80.0)
    assert icr == 1.25
    assert label == "Solvency Risk"
    assert warning is True

def test_7_net_debt_normal_and_cash_rich():
    # Debt 1000, Investments 200 -> Net Debt 800
    assert compute_net_debt(1000.0, 200.0) == 800.0

    # Debt 200, Investments 1000 -> Net Debt -800 (Cash Rich)
    assert compute_net_debt(200.0, 1000.0) == -800.0

def test_8_asset_turnover_normal_and_zero_assets():
    # Sales 1000, Total Assets 500 -> 2.0
    assert compute_asset_turnover(1000.0, 500.0) == 2.0
    assert compute_asset_turnover(1000.0, 0.0) is None
    assert compute_asset_turnover(1000.0, -100.0) is None
