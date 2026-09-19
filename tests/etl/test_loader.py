"""
Unit Tests for Database Loader & Ingestion
Module: tests/etl/test_loader.py
"""

import sqlite3

import pandas as pd
import pytest

from src.api.deps import get_db_path


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(get_db_path())
    yield c
    c.close()


def test_loader_01_companies_rows_and_cols(conn):
    df = pd.read_sql_query("SELECT * FROM companies;", conn)
    assert len(df) == 92, f"Expected 92 companies, got {len(df)}"
    assert any(c in df.columns for c in ["id", "company_id", "ticker"])
    assert any(c in df.columns for c in ["company_name", "name"])


def test_loader_02_profitandloss_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM profitandloss;", conn)
    assert len(df) >= 1000, f"Expected >= 1000 rows in profitandloss, got {len(df)}"
    assert "sales" in [c.lower() for c in df.columns] or "revenue" in [c.lower() for c in df.columns]


def test_loader_03_balancesheet_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM balancesheet;", conn)
    assert len(df) >= 1000, f"Expected >= 1000 rows in balancesheet, got {len(df)}"
    assert any(k in " ".join(df.columns).lower() for k in ["equity", "borrowings", "assets", "liabilities"])


def test_loader_04_cashflow_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM cashflow;", conn)
    assert len(df) >= 1000, f"Expected >= 1000 rows in cashflow, got {len(df)}"
    assert any("cash_from_operating_activity" in c.lower() or "operating" in c.lower() for c in df.columns)


def test_loader_05_sectors_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM sectors;", conn)
    assert len(df) == 92, f"Expected 92 rows in sectors, got {len(df)}"
    assert "broad_sector" in df.columns or "sector" in df.columns


def test_loader_06_market_cap_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM market_cap;", conn)
    assert len(df) >= 500, f"Expected >= 500 rows in market_cap, got {len(df)}"
    cols = [c.lower() for c in df.columns]
    assert "pe_ratio" in cols
    assert "pb_ratio" in cols


def test_loader_07_financial_ratios_count_and_columns(conn):
    df = pd.read_sql_query("SELECT * FROM financial_ratios;", conn)
    assert len(df) >= 1000, f"Expected >= 1000 rows in financial_ratios, got {len(df)}"
    assert "year" in df.columns or "period" in df.columns


def test_loader_08_annual_reports_or_documents(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('documents', 'annual_reports');")
    tables = [r[0] for r in cur.fetchall()]
    assert len(tables) >= 1
    tbl = tables[0]
    df = pd.read_sql_query(f"SELECT * FROM {tbl};", conn)
    assert len(df) >= 500


def test_loader_09_stock_prices_row_count(conn):
    df = pd.read_sql_query("SELECT * FROM stock_prices;", conn)
    assert len(df) >= 5000, f"Expected >= 5000 stock price records, got {len(df)}"


def test_loader_10_unique_constituent_ids(conn):
    df = pd.read_sql_query("SELECT DISTINCT id FROM companies;", conn)
    assert len(df) == 92
