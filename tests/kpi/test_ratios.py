"""
Unit Tests for Financial KPI Ratios & Edge Cases
Module: tests/kpi/test_ratios.py
"""

from src.kpi.ratios import (
    check_leverage_flag,
    check_opm_crosscheck,
    compute_cagr,
    compute_cfo_quality_score,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_roe,
)


# 1-3: ROE Tests
def test_roe_positive_equity():
    assert compute_roe(150.0, 1000.0) == 15.0


def test_roe_negative_equity_returns_none():
    assert compute_roe(50.0, -200.0) is None


def test_roe_zero_equity_returns_none():
    assert compute_roe(50.0, 0.0) is None


# 4-6: D/E Tests
def test_de_debt_free_company_returns_zero():
    assert compute_debt_to_equity(0.0, 5000.0) == 0.0


def test_de_standard_leverage():
    assert compute_debt_to_equity(250.0, 500.0) == 0.50


def test_de_negative_equity_returns_none():
    assert compute_debt_to_equity(100.0, -50.0) is None


# 7-9: ICR Tests
def test_icr_zero_interest_returns_none():
    assert compute_interest_coverage(500.0, 0.0) is None


def test_icr_normal_coverage():
    assert compute_interest_coverage(1000.0, 200.0) == 5.0


def test_icr_ebit_loss():
    assert compute_interest_coverage(-100.0, 50.0) == -2.0


# 10-12: Non-financial D/E > 5 Flag
def test_de_flag_triggers_for_non_financial_over_5():
    assert check_leverage_flag(5.8, "Capital Goods") is True
    assert check_leverage_flag(6.2, "Consumer Staples") is True


def test_de_flag_exempt_for_financial_institutions():
    assert check_leverage_flag(8.5, "Financial Services") is False
    assert check_leverage_flag(7.2, "Banks") is False


def test_de_flag_false_when_under_5():
    assert check_leverage_flag(2.1, "Industrials") is False


# 13-16: CAGR Mechanics & Flags
def test_cagr_normal_growth():
    cagr, flag = compute_cagr(100.0, 161.05, 5)
    assert cagr == 10.0
    assert flag == "NORMAL"


def test_cagr_turnaround_flag():
    cagr, flag = compute_cagr(-50.0, 150.0, 5)
    assert cagr is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss_flag():
    cagr, flag = compute_cagr(120.0, -30.0, 5)
    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_chronic_loss():
    cagr, flag = compute_cagr(-40.0, -10.0, 5)
    assert cagr is None
    assert flag == "CHRONIC_LOSS"


# 17-18: OPM Cross-Check
def test_opm_crosscheck_divergence_flag():
    # Reported 25% vs Calculated (100 / 1000) = 10% -> Divergence of 15% > 1.0%
    assert check_opm_crosscheck(25.0, 1000.0, 100.0) is True


def test_opm_crosscheck_within_tolerance():
    # Reported 20.0% vs Calculated (201 / 1000) = 20.1% -> Diff 0.1% <= 1.0%
    assert check_opm_crosscheck(20.0, 1000.0, 201.0) is False


# 19-20: CFO Quality Score
def test_cfo_quality_score_full_marks():
    # CFO (120) >= PAT (100) and CFO (120) >= 0.7 * EBITDA (150 * 0.7 = 105)
    score = compute_cfo_quality_score(120.0, 150.0, 100.0)
    assert score == 100.0


def test_cfo_quality_score_zero():
    # Negative CFO returns 0.0
    score = compute_cfo_quality_score(-20.0, 100.0, 50.0)
    assert score == 0.0
