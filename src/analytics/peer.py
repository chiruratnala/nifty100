"""
Nifty 100 Peer Group Percentile Ranking Engine
Module: src/analytics/peer.py
Description: Computes PERCENT_RANK across 10 fundamental metrics within 11 peer groups
             with Debt-to-Equity inversion and SQLite table ingestion.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


def compute_peer_percentiles(
    df_metrics: pd.DataFrame, 
    df_peer_groups: pd.DataFrame,
    metrics_to_rank: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Computes percentile rankings (0.0 to 1.0) for metrics within assigned peer groups.
    Inverts D/E percentile rank so that lower leverage yields a higher percentile rank.
    """
    if metrics_to_rank is None:
        metrics_to_rank = [
            "return_on_equity_pct",
            "operating_profit_margin_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "pat_cagr_5yr",
            "revenue_cagr_5yr",
            "eps_cagr_5yr",
            "interest_coverage",
            "asset_turnover"
        ]

    df_peers = df_peer_groups.copy()
    col_map = {}
    for c in df_peers.columns:
        if any(k in c.lower() for k in ["company", "id", "symbol", "ticker"]):
            col_map[c] = "company_id"
        elif any(k in c.lower() for k in ["peer", "group", "sub_sector", "sector"]):
            col_map[c] = "peer_group_name"
            
    df_peers = df_peers.rename(columns=col_map)[["company_id", "peer_group_name"]].drop_duplicates()
    df_merged = pd.merge(df_metrics, df_peers, on="company_id", how="left")

    records = []

    for _, row in df_merged.iterrows():
        cid = row["company_id"]
        pg_name = row["peer_group_name"]
        yr = row.get("year", "2024-03")

        if pd.isna(pg_name) or str(pg_name).strip() == "":
            for m in metrics_to_rank:
                records.append({
                    "company_id": cid,
                    "peer_group_name": "No peer group assigned",
                    "metric": m,
                    "value": row.get(m, np.nan),
                    "percentile_rank": np.nan,
                    "year": yr
                })

    for pg_name, group_df in df_merged.dropna(subset=["peer_group_name"]).groupby("peer_group_name"):
        for m in metrics_to_rank:
            if m not in group_df.columns:
                continue
            
            vals = pd.to_numeric(group_df[m], errors="coerce")
            
            if len(vals.dropna()) <= 1:
                ranks = pd.Series(1.0, index=vals.index)
            else:
                ranks = vals.rank(pct=True, ascending=True)

            # Invert Debt-to-Equity rank (lower is better)
            if m == "debt_to_equity":
                ranks = 1.0 - ranks

            for idx, r_val in ranks.items():
                cid = group_df.loc[idx, "company_id"]
                yr = group_df.loc[idx, "year"] if "year" in group_df.columns else "2024-03"
                orig_val = group_df.loc[idx, m]
                
                records.append({
                    "company_id": cid,
                    "peer_group_name": pg_name,
                    "metric": m,
                    "value": round(float(orig_val), 4) if pd.notna(orig_val) and isinstance(orig_val, (int, float)) else None,
                    "percentile_rank": round(float(r_val), 4) if pd.notna(r_val) else None,
                    "year": str(yr)
                })

    df_percentiles = pd.DataFrame(records).drop_duplicates(subset=["company_id", "metric", "year"])
    return df_percentiles


def save_peer_percentiles_to_db(df_percentiles: pd.DataFrame, conn: sqlite3.Connection):
    """Creates peer_percentiles table in SQLite and ingests computed rankings."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS peer_percentiles (
        company_id TEXT,
        peer_group_name TEXT,
        metric TEXT,
        value REAL,
        percentile_rank REAL,
        year TEXT,
        PRIMARY KEY (company_id, metric, year)
    );
    """
    conn.execute(create_table_sql)
    conn.execute("DELETE FROM peer_percentiles;")
    df_percentiles.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()
