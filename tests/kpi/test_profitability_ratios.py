import pytest
from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_roe,
    compute_roce,
    compute_roa,
)

def test_1_npm_normal():
    # Net Profit: 1500, Sales: 10000 -> 15.0%
    assert compute_net_profit_margin(1500.0, 10000.0) == 15.0

def test_2_npm_zero_or_negative_sales():
    assert compute_net_profit_margin(500.0, 0.0) is None
    assert compute_net_profit_margin(500.0, -100.0) is None
    assert compute_net_profit_margin(500.0, None) is None

def test_3_opm_normal_match():
    opm, warning = compute_operating_profit_margin(
        operating_profit=250.0, sales=1000.0, source_opm=25.0, company_id="TEST", year="2024-03"
    )
    assert opm == 25.0
    assert warning is None

def test_4_opm_crosscheck_mismatch_logged():
    opm, warning = compute_operating_profit_margin(
        operating_profit=250.0, sales=1000.0, source_opm=20.0, company_id="TEST", year="2024-03"
    )
    assert opm == 25.0
    assert warning is not None
    assert "OPM Mismatch" in warning

def test_5_roe_normal():
    # PAT: 200, Equity: 50, Reserves: 950 -> Total Equity: 1000 -> 20.0%
    assert compute_roe(200.0, 50.0, 950.0) == 20.0

def test_6_roe_negative_equity_returns_none():
    # Equity: 50, Reserves: -200 -> Total Equity: -150 -> None
    assert compute_roe(100.0, 50.0, -200.0) is None
    assert compute_roe(100.0, 0.0, 0.0) is None

def test_7_roce_normal_and_financials_sector():
    # Non-financial: EBIT: 350, Capital Employed: 2000 -> 17.5%
    res_normal = compute_roce(300.0, 50.0, 100.0, 900.0, 1000.0, broad_sector="Industrials")
    assert res_normal["roce_pct"] == 17.5
    assert res_normal["is_financial_sector"] is False

    # Financial sector carve-out
    res_fin = compute_roce(300.0, 50.0, 100.0, 900.0, 1000.0, broad_sector="Financials")
    assert res_fin["is_financial_sector"] is True

def test_8_roa_normal_and_zero_assets():
    # Net profit: 120, Total assets: 1200 -> 10.0%
    assert compute_roa(120.0, 1200.0) == 10.0
    assert compute_roa(120.0, 0.0) is None
    assert compute_roa(120.0, -500.0) is None
