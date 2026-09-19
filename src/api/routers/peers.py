"""
Peers Router & Radar Logic
Module: src/api/routers/peers.py
"""

import os
import sqlite3
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import fetch_company_row, get_db, load_canonical_universe

router = APIRouter()

METRICS_10 = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "price_to_earnings",
    "price_to_book",
    "revenue_cagr_5yr",
    "net_profit_cagr_5yr",
    "fcf_cagr_5yr",
]

RADAR_8 = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "price_to_earnings",
    "price_to_book",
    "revenue_cagr_5yr",
    "net_profit_cagr_5yr",
    "fcf_cagr_5yr",
]


@router.get("/{group_name}", response_model=list[dict[str, Any]], tags=["Peers"])
def get_peer_group_percentiles(group_name: str, conn: sqlite3.Connection = Depends(get_db)):
    """Execute Get peer group percentiles routine."""
    df = load_canonical_universe(conn)
    g_clean = group_name.strip().lower()

    matched = df[df["sector"].str.lower() == g_clean]
    if matched.empty and os.path.exists("output/cluster_labels.csv"):
        df_cl = pd.read_csv("output/cluster_labels.csv")
        df_cl["company_id"] = df_cl["company_id"].astype(str).str.strip()
        df_merged = df.merge(df_cl[["company_id", "cluster_name"]], on="company_id", how="left")
        matched = df_merged[df_merged["cluster_name"].str.lower() == g_clean]

    if matched.empty:
        matched = df[df["sector"].str.lower().str.contains(g_clean)]

    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found.")

    res = matched[["company_id", "company_name", "sector"]].copy()
    for m in METRICS_10:
        if m in matched.columns:
            res[f"{m}_percentile"] = (matched[m].rank(pct=True) * 100.0).round(1)
            res[m] = matched[m].round(2)
        else:
            res[f"{m}_percentile"] = 50.0
            res[m] = 0.0

    return res.to_dict(orient="records")


def calculate_radar_dict(ticker: str, conn: sqlite3.Connection) -> dict[str, Any]:
    """Execute Calculate radar dict routine."""
    fetch_company_row(conn, ticker)
    df = load_canonical_universe(conn)

    comp = df[df["company_id"].str.upper() == ticker.strip().upper()]
    if comp.empty:
        raise HTTPException(status_code=404, detail=f"Metrics for company '{ticker}' not found.")

    sec = comp["sector"].iloc[0]
    peer_df = df[df["sector"] == sec]
    if len(peer_df) < 2:
        peer_df = df.copy()

    bench = peer_df.sort_values(by="return_on_equity_pct", ascending=False).iloc[0]

    def safe_dict(series_or_row, cols):
        """Execute Safe dict routine."""
        out = {}
        for c in cols:
            val = series_or_row.get(c, 0.0)
            out[c] = round(float(val), 2) if pd.notna(val) else 0.0
        return out

    return {
        "ticker": ticker.upper(),
        "sector": sec,
        "benchmark_ticker": str(bench["company_id"]),
        "metrics_evaluated": RADAR_8,
        "company_values": safe_dict(comp.iloc[0], RADAR_8),
        "peer_group_average": safe_dict(peer_df[RADAR_8].mean(), RADAR_8),
        "benchmark_values": safe_dict(bench, RADAR_8),
    }
