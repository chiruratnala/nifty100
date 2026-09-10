"""
Nifty 100 Analytics - Data Loader Layer
Module: src/dashboard/utils/db.py
Description: Cached SQLite data loaders configured for explicit schema column keys.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from typing import Optional

DB_PATH = "/content/data/nifty100.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Returns company universe metadata joining sectors and companies."""
    conn = get_connection()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    
    if "sectors" not in tables:
        conn.close()
        return pd.DataFrame()

    has_peer = "peer_percentiles" in tables

    if has_peer:
        query = """
        SELECT 
            s.company_id,
            COALESCE(c.company_name, s.company_id) AS company_name,
            s.broad_sector,
            s.sub_sector,
            COALESCE(p.peer_group_name, s.sub_sector) AS peer_group_name
        FROM sectors s
        LEFT JOIN companies c ON s.company_id = c.id
        LEFT JOIN (
            SELECT DISTINCT company_id, peer_group_name 
            FROM peer_percentiles
        ) p ON s.company_id = p.company_id
        ORDER BY s.company_id ASC;
        """
    else:
        query = """
        SELECT 
            s.company_id,
            COALESCE(c.company_name, s.company_id) AS company_name,
            s.broad_sector,
            s.sub_sector,
            s.sub_sector AS peer_group_name
        FROM sectors s
        LEFT JOIN companies c ON s.company_id = c.id
        ORDER BY s.company_id ASC;
        """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: Optional[str] = None, year: Optional[str] = None) -> pd.DataFrame:
    """Retrieves financial ratios."""
    conn = get_connection()
    conditions = []
    params = []

    if ticker:
        conditions.append("company_id = ?")
        params.append(ticker)
    if year:
        conditions.append("year LIKE ?")
        params.append(f"{year}%")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
    SELECT *
    FROM financial_ratios
    {where_clause}
    ORDER BY company_id ASC, year DESC;
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Retrieves historical Profit & Loss using table 'profitandloss'."""
    conn = get_connection()
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC;"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Retrieves historical Balance Sheet using table 'balancesheet'."""
    conn = get_connection()
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC;"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Retrieves historical Cash Flow using table 'cashflow'."""
    conn = get_connection()
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC;"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Retrieves broad sector breakdown."""
    conn = get_connection()
    query = """
    SELECT broad_sector, COUNT(*) as company_count
    FROM sectors
    GROUP BY broad_sector
    ORDER BY company_count DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: Optional[str] = None) -> pd.DataFrame:
    """Retrieves percentile ranking rows."""
    conn = get_connection()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    if "peer_percentiles" not in tables:
        conn.close()
        return pd.DataFrame()

    if group_name:
        query = """
        SELECT company_id, peer_group_name, metric, value, percentile_rank, year
        FROM peer_percentiles
        WHERE peer_group_name = ?
        ORDER BY company_id ASC;
        """
        df = pd.read_sql_query(query, conn, params=[group_name])
    else:
        query = "SELECT * FROM peer_percentiles ORDER BY peer_group_name ASC;"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker: Optional[str] = None) -> pd.DataFrame:
    """Retrieves valuation multiples."""
    conn = get_connection()
    if ticker:
        query = """
        SELECT company_id, year, price_to_earnings, price_to_book, dividend_yield_pct
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC;
        """
        df = pd.read_sql_query(query, conn, params=[ticker])
    else:
        query = """
        SELECT company_id, year, price_to_earnings, price_to_book, dividend_yield_pct
        FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
        ORDER BY company_id ASC;
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df
