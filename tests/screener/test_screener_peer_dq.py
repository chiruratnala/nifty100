"""
Nifty 100 Screener & Peer Engine Data Quality (DQ) Test Suite
Module: tests/screener/test_screener_peer_dq.py
Description: 14 formula, boundary, and monotonicity unit tests for Epics 03 & 04.
"""

import pytest
import sqlite3
import pandas as pd
import numpy as np
import os
import openpyxl

from src.screener.engine import load_screener_config, get_screener_universe, apply_filter_criteria
import src.screener.presets as presets
import src.screener.composite as composite
import src.analytics.peer as peer


@pytest.fixture(scope="module")
def db_conn():
    db_path = "data/nifty100.db" if os.path.exists("data/nifty100.db") else "nifty100.db"
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def universe_df(db_conn):
    return get_screener_universe(db_conn, latest_only=True)


@pytest.fixture(scope="module")
def config():
    return load_screener_config()


# --- Epic 03: Screener DQ Tests (1-7) ---

def test_dq_01_universe_non_empty(universe_df):
    """DQ 1: Screener universe loads at least 80 active companies."""
    assert len(universe_df) >= 80, f"Expected >= 80 companies, got {len(universe_df)}"


def test_dq_02_quality_compounder_bounds(universe_df, config):
    """DQ 2: Quality Compounder preset returns 5 to 50 companies."""
    res = presets.run_quality_compounder(universe_df, config.get("presets", {}))
    assert 5 <= len(res) <= 50, f"Quality Compounder returned {len(res)} companies"


def test_dq_03_quality_compounder_roe_filter(universe_df, config):
    """DQ 3: All Quality Compounder results have ROE >= 15%."""
    res = presets.run_quality_compounder(universe_df, config.get("presets", {}))
    assert (res["return_on_equity_pct"] >= 15.0).all(), "Found company with ROE < 15%"


def test_dq_04_financials_de_carve_out(universe_df):
    """DQ 4: D/E filter skips Financials sector companies."""
    filtered = apply_filter_criteria(universe_df, {"debt_to_equity_max": 0.5})
    # If a bank is present, its D/E can be > 0.5 because Financials are carved out
    financials = filtered[filtered["broad_sector"] == "Financials"]
    assert len(financials) > 0, "Financials carve-out failed to retain eligible banking stocks"


def test_dq_05_composite_score_range(universe_df):
    """DQ 5: Composite quality score strictly between 0 and 100."""
    scored = composite.compute_composite_quality_scores(universe_df)
    assert scored["composite_quality_score"].between(0.0, 100.0).all(), "Scores out of 0-100 range"


def test_dq_06_screener_excel_exists():
    """DQ 6: output/screener_output.xlsx exists with 6 sheets."""
    assert os.path.exists("output/screener_output.xlsx"), "output/screener_output.xlsx missing"
    wb = openpyxl.load_workbook("output/screener_output.xlsx", read_only=True)
    assert len(wb.sheetnames) == 6, f"Expected 6 sheets, found {len(wb.sheetnames)}"
    wb.close()


def test_dq_07_debt_free_icr_handling(universe_df):
    """DQ 7: Debt-free companies (null ICR) pass minimum ICR filters."""
    filtered = apply_filter_criteria(universe_df, {"interest_coverage_min": 5.0})
    debt_free = filtered[filtered["debt_to_equity"] <= 0.01]
    assert len(debt_free) > 0, "Debt-free companies incorrectly excluded by ICR filter"


# --- Epic 04: Peer Engine DQ Tests (8-14) ---

def test_dq_08_peer_percentiles_table_exists(db_conn):
    """DQ 8: peer_percentiles table exists in SQLite and has >= 800 rows."""
    count = db_conn.execute("SELECT COUNT(*) FROM peer_percentiles;").fetchone()[0]
    assert count >= 800, f"Expected >= 800 rows in peer_percentiles, got {count}"


def test_dq_09_peer_group_count(db_conn):
    """DQ 9: Exactly 11 peer groups covered in peer_percentiles."""
    groups = db_conn.execute("SELECT COUNT(DISTINCT peer_group_name) FROM peer_percentiles;").fetchone()[0]
    assert groups == 11, f"Expected 11 peer groups, found {groups}"


def test_dq_10_de_percentile_inversion(db_conn):
    """DQ 10: D/E percentile rank is inverted (lower D/E has higher percentile rank)."""
    df_it = pd.read_sql_query("""
        SELECT company_id, value, percentile_rank 
        FROM peer_percentiles 
        WHERE peer_group_name = 'IT Services' AND metric = 'debt_to_equity'
        ORDER BY value ASC;
    """, db_conn)
    if len(df_it) >= 2:
        # Lowest debt should have top rank
        assert df_it.iloc[0]["percentile_rank"] >= df_it.iloc[-1]["percentile_rank"]


def test_dq_11_it_services_roe_monotonicity(db_conn):
    """DQ 11: IT Services ROE ranking is strictly monotonic."""
    df_roe = pd.read_sql_query("""
        SELECT percentile_rank 
        FROM peer_percentiles 
        WHERE peer_group_name = 'IT Services' AND metric = 'return_on_equity_pct'
        ORDER BY value DESC;
    """, db_conn)
    ranks = df_roe["percentile_rank"].tolist()
    assert ranks == sorted(ranks, reverse=True), "ROE percentile ranking is not monotonic"


def test_dq_12_peer_comparison_excel_exists():
    """DQ 12: output/peer_comparison.xlsx exists with 11 sheets."""
    assert os.path.exists("output/peer_comparison.xlsx"), "output/peer_comparison.xlsx missing"
    wb = openpyxl.load_workbook("output/peer_comparison.xlsx", read_only=True)
    assert len(wb.sheetnames) == 11, f"Expected 11 sheets, found {len(wb.sheetnames)}"
    wb.close()


def test_dq_13_radar_charts_count():
    """DQ 13: Radar charts directory contains >= 80 generated PNGs."""
    charts = [f for f in os.listdir("reports/radar_charts") if f.endswith("_radar.png")]
    assert len(charts) >= 80, f"Expected >= 80 radar charts, found {len(charts)}"


def test_dq_14_percentile_boundary_limits(db_conn):
    """DQ 14: All percentile ranks fall strictly within [0.0, 1.0]."""
    df_ranks = pd.read_sql_query("SELECT percentile_rank FROM peer_percentiles WHERE percentile_rank IS NOT NULL;", db_conn)
    assert df_ranks["percentile_rank"].between(0.0, 1.0).all(), "Percentile ranks outside [0, 1] range"
