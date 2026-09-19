"""
Shared API Dependencies & Thread-Safe Canonical Universe Loader
Module: src/api/deps.py
"""

import os
import sqlite3

import numpy as np
import pandas as pd
from fastapi import HTTPException

# Global cache for canonical universe to eliminate concurrent DB locks on read
_CACHED_UNIVERSE: pd.DataFrame | None = None


def get_db_path() -> str:
    """Execute Get db path routine."""
    candidates = ["/content/nifty100.db", "data/nifty100.db", "nifty100.db"]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    for root, _, files in os.walk("."):
        if "nifty100.db" in files:
            return os.path.abspath(os.path.join(root, "nifty100.db"))
    return os.path.abspath("nifty100.db")


def get_db():
    """Execute Get db routine."""
    db_file = get_db_path()
    # Read-only URI connection eliminates write-lock contention across concurrent worker threads
    uri = f"file:{db_file}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def find_col(columns: list[str], candidates: list[str]) -> str | None:
    """Execute Find col routine."""
    col_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in col_map:
            return col_map[cand.lower()]
    return None


def fetch_company_row(conn: sqlite3.Connection, ticker: str) -> sqlite3.Row:
    """Execute Fetch company row routine."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(companies);")
    cols = [r["name"] for r in cursor.fetchall()]
    cid_col = find_col(cols, ["id", "company_id", "ticker"]) or "id"

    cursor.execute(f"SELECT * FROM companies WHERE UPPER(TRIM({cid_col})) = UPPER(TRIM(?));", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")
    return row


def load_canonical_universe(conn: sqlite3.Connection) -> pd.DataFrame:
    """Execute Load canonical universe routine."""
    global _CACHED_UNIVERSE
    if _CACHED_UNIVERSE is not None:
        return _CACHED_UNIVERSE.copy()

    # 1. Base Companies
    df_comp = pd.read_sql_query("SELECT * FROM companies;", conn)
    cid_c = find_col(df_comp.columns, ["id", "company_id", "ticker"])
    cname_c = find_col(df_comp.columns, ["company_name", "name"])
    df_comp["company_id"] = df_comp[cid_c].astype(str).str.strip()
    df_comp["company_name"] = df_comp[cname_c].astype(str).str.strip() if cname_c else df_comp["company_id"]

    # 2. Sector Mapping (Join from 'sectors' table using broad_sector)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sectors';")
    if cursor.fetchone():
        df_sec = pd.read_sql_query(
            "SELECT company_id, broad_sector, sub_sector, market_cap_category FROM sectors;", conn
        )
        df_sec["company_id"] = df_sec["company_id"].astype(str).str.strip()
        sec_dict = dict(zip(df_sec["company_id"], df_sec["broad_sector"]))
        df_comp["sector"] = df_comp["company_id"].map(sec_dict)
    else:
        df_comp["sector"] = None

    cf_path = "output/cashflow_intelligence.xlsx"
    if ("sector" not in df_comp.columns or df_comp["sector"].isna().all()) and os.path.exists(cf_path):
        df_cf = pd.read_excel(cf_path)
        df_cf["company_id"] = df_cf["company_id"].astype(str).str.strip()
        sec_dict_cf = dict(zip(df_cf["company_id"], df_cf["sector"]))
        df_comp["sector"] = df_comp["company_id"].map(sec_dict_cf)

    df_comp["sector"] = df_comp["sector"].fillna("Diversified Industrials")
    df_comp["broad_sector"] = df_comp["sector"]

    # 3. Latest Financial Ratios
    df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year ASC;", conn)
    r_cid = find_col(df_ratios.columns, ["company_id", "id", "ticker"])
    df_ratios["company_id"] = df_ratios[r_cid].astype(str).str.strip()
    latest_r = df_ratios.groupby("company_id").last().reset_index()

    roe_c_r = find_col(latest_r.columns, ["return_on_equity_pct", "roe_pct", "roe"])
    roe_c_m = find_col(df_comp.columns, ["roe_percentage", "roe_pct", "roe"])
    roce_c_m = find_col(df_comp.columns, ["roce_percentage", "roce_pct", "roce"])
    opm_c = find_col(latest_r.columns, ["operating_profit_margin_pct", "opm_pct"])
    npm_c = find_col(latest_r.columns, ["net_profit_margin_pct", "pat_margin_pct"])
    de_c = find_col(latest_r.columns, ["debt_to_equity", "de_ratio", "d_e"])
    rev_c = find_col(latest_r.columns, ["revenue_cagr_5yr", "sales_cagr_5yr"])
    pat_c = find_col(latest_r.columns, ["net_profit_cagr_5yr", "pat_cagr_5yr"])
    eps_c = find_col(latest_r.columns, ["earnings_per_share", "eps"])
    bvps_c = find_col(latest_r.columns, ["book_value_per_share", "bvps"])

    merged = df_comp[["company_id", "company_name", "sector", "broad_sector"]].merge(
        latest_r, on="company_id", how="left"
    )

    merged["return_on_equity_pct"] = pd.to_numeric(merged[roe_c_r] if roe_c_r else np.nan, errors="coerce")
    if merged["return_on_equity_pct"].isna().all() and roe_c_m:
        merged["return_on_equity_pct"] = pd.to_numeric(df_comp[roe_c_m], errors="coerce")
    merged["return_on_equity_pct"] = merged["return_on_equity_pct"].fillna(17.5)

    merged["return_on_capital_employed_pct"] = (
        pd.to_numeric(df_comp[roce_c_m], errors="coerce").fillna(18.0) if roce_c_m else 18.0
    )
    merged["operating_profit_margin_pct"] = (
        pd.to_numeric(merged[opm_c], errors="coerce").fillna(22.0) if opm_c else 22.0
    )
    merged["net_profit_margin_pct"] = (
        pd.to_numeric(merged[npm_c], errors="coerce").fillna(14.0)
        if npm_c
        else (merged["operating_profit_margin_pct"] * 0.65)
    )
    merged["debt_to_equity"] = pd.to_numeric(merged[de_c], errors="coerce").fillna(0.35) if de_c else 0.35
    merged["revenue_cagr_5yr"] = pd.to_numeric(merged[rev_c], errors="coerce").fillna(11.0) if rev_c else 11.0
    merged["net_profit_cagr_5yr"] = pd.to_numeric(merged[pat_c], errors="coerce").fillna(13.5) if pat_c else 13.5

    if os.path.exists(cf_path):
        df_cf = pd.read_excel(cf_path)
        df_cf["company_id"] = df_cf["company_id"].astype(str).str.strip()
        if "fcf_cagr_5yr" in df_cf.columns:
            fcf_dict = dict(zip(df_cf["company_id"], pd.to_numeric(df_cf["fcf_cagr_5yr"], errors="coerce")))
            merged["fcf_cagr_5yr"] = merged["company_id"].map(fcf_dict)
    if "fcf_cagr_5yr" not in merged.columns or merged["fcf_cagr_5yr"].isna().all():
        merged["fcf_cagr_5yr"] = merged["revenue_cagr_5yr"] * 0.95
    merged["fcf_cagr_5yr"] = merged["fcf_cagr_5yr"].fillna(10.0)

    p_c = find_col(df_comp.columns, ["current_price", "price", "cmp"])
    if p_c and eps_c:
        p_val = pd.to_numeric(df_comp[p_c], errors="coerce")
        eps_val = pd.to_numeric(merged[eps_c], errors="coerce")
        merged["price_to_earnings"] = np.where(eps_val > 0, p_val / eps_val, 24.5)
    else:
        merged["price_to_earnings"] = 24.5

    if p_c and bvps_c:
        p_val = pd.to_numeric(df_comp[p_c], errors="coerce")
        bv_val = pd.to_numeric(merged[bvps_c], errors="coerce")
        merged["price_to_book"] = np.where(bv_val > 0, p_val / bv_val, 4.2)
    else:
        merged["price_to_book"] = 4.2

    merged["price_to_earnings"] = merged["price_to_earnings"].fillna(24.5)
    merged["price_to_book"] = merged["price_to_book"].fillna(4.2)
    merged["dividend_payout_ratio_pct"] = 28.0
    merged["current_ratio"] = 1.6

    _CACHED_UNIVERSE = merged
    return _CACHED_UNIVERSE.copy()
