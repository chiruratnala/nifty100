"""
Unit Tests for Data Quality (DQ) Rules
Module: tests/dq/test_rules.py
"""

import pandas as pd

from src.dq.rules import evaluate_dq_rule


def test_dq001_missing_company_id():
    df = pd.DataFrame([{"company_id": None, "sales": 100}])
    res = evaluate_dq_rule("DQ001", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ001"
    assert res[0]["severity"] == "CRITICAL"


def test_dq002_negative_sales():
    df = pd.DataFrame([{"company_id": "TCS", "sales": -50.0}])
    res = evaluate_dq_rule("DQ002", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ002"
    assert res[0]["severity"] == "CRITICAL"


def test_dq003_balance_sheet_imbalance():
    df = pd.DataFrame([{"company_id": "INFY", "total_assets": 1000.0, "total_liabilities": 800.0}])
    res = evaluate_dq_rule("DQ003", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ003"
    assert res[0]["severity"] == "CRITICAL"


def test_dq004_opm_greater_than_100():
    df = pd.DataFrame([{"company_id": "ITC", "opm_pct": 115.0}])
    res = evaluate_dq_rule("DQ004", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ004"
    assert res[0]["severity"] == "HIGH"


def test_dq005_npm_exceeds_opm():
    df = pd.DataFrame([{"company_id": "HDFCBANK", "opm_pct": 20.0, "npm_pct": 35.0}])
    res = evaluate_dq_rule("DQ005", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ005"
    assert res[0]["severity"] == "HIGH"


def test_dq006_extreme_debt_to_equity():
    df = pd.DataFrame([{"company_id": "ADANIENT", "debt_to_equity": 32.5}])
    res = evaluate_dq_rule("DQ006", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ006"
    assert res[0]["severity"] == "HIGH"


def test_dq007_unnormalized_year():
    df = pd.DataFrame([{"company_id": "WIPRO", "year": "FY_2023_Invalid"}])
    res = evaluate_dq_rule("DQ007", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ007"
    assert res[0]["severity"] == "MEDIUM"


def test_dq008_negative_shareholders_equity():
    df = pd.DataFrame([{"company_id": "SUZLON", "shareholders_equity": -450.0}])
    res = evaluate_dq_rule("DQ008", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ008"
    assert res[0]["severity"] == "HIGH"


def test_dq009_positive_cfo_with_negative_sales():
    df = pd.DataFrame([{"company_id": "ZOMATO", "cfo": 120.0, "sales": -10.0}])
    res = evaluate_dq_rule("DQ009", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ009"
    assert res[0]["severity"] == "HIGH"


def test_dq010_extreme_dividend_payout():
    df = pd.DataFrame([{"company_id": "COALINDIA", "dividend_payout_pct": 180.0}])
    res = evaluate_dq_rule("DQ010", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ010"
    assert res[0]["severity"] == "MEDIUM"


def test_dq011_negative_cash_balance():
    df = pd.DataFrame([{"company_id": "RELIANCE", "cash_balance": -35.0}])
    res = evaluate_dq_rule("DQ011", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ011"
    assert res[0]["severity"] == "CRITICAL"


def test_dq012_unassigned_sector():
    df = pd.DataFrame([{"company_id": "UNKNOWN_CORP", "sector": "Unassigned"}])
    res = evaluate_dq_rule("DQ012", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ012"
    assert res[0]["severity"] == "MEDIUM"


def test_dq013_negative_pe_with_positive_eps():
    df = pd.DataFrame([{"company_id": "TATAMOTORS", "pe_ratio": -15.0, "eps": 22.0}])
    res = evaluate_dq_rule("DQ013", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ013"
    assert res[0]["severity"] == "HIGH"


def test_dq014_duplicate_constituent_period():
    df = pd.DataFrame([{"company_id": "SBIN", "year": "2024"}, {"company_id": "SBIN", "year": "2024"}])
    res = evaluate_dq_rule("DQ014", df)
    assert len(res) == 1
    assert res[0]["rule_id"] == "DQ014"
    assert res[0]["severity"] == "CRITICAL"
