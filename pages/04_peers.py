"""
Nifty 100 Analytics - Peer Comparison Screen
Module: pages/04_peers.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Peer Benchmarking - Nifty 100", layout="wide")

st.title("👥 Sector Peer Group Benchmarking & Radar Overlays")
st.caption("Multi-dimensional comparative analysis across 11 benchmark groups.")

df_comp = get_companies()
df_ratios = get_ratios(year="2024")
if df_ratios.empty:
    df_ratios = get_ratios()

if df_comp.empty or df_ratios.empty:
    st.error("Universe or ratio data unavailable.")
    st.stop()

# Get latest year record per stock
df_latest_ratios = df_ratios.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
df_merged = pd.merge(df_comp, df_latest_ratios, on="company_id", how="inner")

# 1. Peer Group Dropdown with 11 Broad Groups
peer_groups = sorted(df_merged["broad_sector"].dropna().unique().tolist())
if not peer_groups:
    peer_groups = ["Financials", "Information Technology", "Energy", "Consumer Discretionary", "Materials"]

col_sel1, col_sel2 = st.columns([1, 1])
with col_sel1:
    selected_group = st.selectbox("Select Peer Group (11 Sectors)", options=peer_groups, index=0)

df_group = df_merged[df_merged["broad_sector"] == selected_group].copy()

with col_sel2:
    company_options = (df_group["company_id"] + " - " + df_group["company_name"]).tolist()
    if company_options:
        selected_comp_str = st.selectbox("Select Benchmark Company", options=company_options, index=0)
        benchmark_ticker = selected_comp_str.split(" - ")[0].strip()
    else:
        benchmark_ticker = ""

if not benchmark_ticker:
    st.warning("No companies found in this peer group.")
    st.stop()

benchmark_row = df_group[df_group["company_id"] == benchmark_ticker].iloc[0]

# 8 Metrics for Radar Chart matching schema
metric_defs = [
    ("ROE (%)", "return_on_equity_pct"),
    ("NPM (%)", "net_profit_margin_pct"),
    ("OPM (%)", "operating_profit_margin_pct"),
    ("5Y Rev CAGR", "revenue_cagr_5yr"),
    ("5Y PAT CAGR", "pat_cagr_5yr"),
    ("Leverage Score", "debt_to_equity"),
    ("ICR (Coverage)", "interest_coverage"),
    ("Asset Turnover", "asset_turnover")
]

radar_axes = []
comp_vals = []
peer_avg_vals = []

for label, col in metric_defs:
    radar_axes.append(label)
    val = benchmark_row.get(col, 0)
    val = float(val) if pd.notna(val) else 0.0

    avg = df_group[col].mean() if col in df_group.columns else 0.0
    avg = float(avg) if pd.notna(avg) else 0.0

    if col == "debt_to_equity":
        val_norm = max(0.0, 100.0 - (val * 40.0))
        avg_norm = max(0.0, 100.0 - (avg * 40.0))
    elif col == "asset_turnover":
        val_norm = np.clip(val * 50.0, 10.0, 100.0)
        avg_norm = np.clip(avg * 50.0, 10.0, 100.0)
    elif col == "interest_coverage":
        val_norm = np.clip(val * 5.0, 10.0, 100.0)
        avg_norm = np.clip(avg * 5.0, 10.0, 100.0)
    else:
        val_norm = np.clip(val * 2.5, 5.0, 100.0)
        avg_norm = np.clip(avg * 2.5, 5.0, 100.0)

    comp_vals.append(round(val_norm, 1))
    peer_avg_vals.append(round(avg_norm, 1))

radar_axes.append(radar_axes[0])
comp_vals.append(comp_vals[0])
peer_avg_vals.append(peer_avg_vals[0])

# 2. Polar Radar Chart
st.subheader(f"🕸️ 8-Axis Polar Radar: {benchmark_row['company_name']} vs. {selected_group} Average")

fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=comp_vals,
    theta=radar_axes,
    fill='toself',
    name=f"{benchmark_ticker} (Selected)",
    line=dict(color='#38BDF8', width=3),
    fillcolor='rgba(56, 189, 248, 0.35)'
))

fig_radar.add_trace(go.Scatterpolar(
    r=peer_avg_vals,
    theta=radar_axes,
    fill='toself',
    name=f"{selected_group} Sector Avg",
    line=dict(color='#F59E0B', width=2, dash='dash'),
    fillcolor='rgba(245, 158, 11, 0.15)'
))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 105], showticklabels=False, linecolor="#CBD5E1", gridcolor="#E2E8F0"),
        angularaxis=dict(linecolor="#CBD5E1", gridcolor="#E2E8F0")
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#0F172A", size=11, family="sans-serif"),
    height=420,
    margin=dict(t=30, b=30, l=40, r=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
)

st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# 3. Side-by-Side KPI Matrix Table
st.subheader(f"📊 Peer Group Fundamental Matrix ({len(df_group)} Constituents)")
st.caption(f"Benchmark stock **{benchmark_ticker}** is highlighted in emerald green.")

cols_to_show = [
    "company_id", "company_name", "sub_sector", "return_on_equity_pct",
    "operating_profit_margin_pct", "net_profit_margin_pct", "debt_to_equity",
    "interest_coverage", "revenue_cagr_5yr", "pat_cagr_5yr", "free_cash_flow_cr"
]
df_matrix = df_group[[c for c in cols_to_show if c in df_group.columns]].copy()

df_matrix_display = df_matrix.rename(columns={
    "company_id": "Ticker",
    "company_name": "Company",
    "sub_sector": "Sub-Sector",
    "return_on_equity_pct": "ROE (%)",
    "operating_profit_margin_pct": "OPM (%)",
    "net_profit_margin_pct": "NPM (%)",
    "debt_to_equity": "D/E",
    "interest_coverage": "ICR",
    "revenue_cagr_5yr": "5Y Rev CAGR (%)",
    "pat_cagr_5yr": "5Y PAT CAGR (%)",
    "free_cash_flow_cr": "FCF (Cr)"
})

def highlight_benchmark(row):
    is_benchmark = row["Ticker"] == benchmark_ticker
    bg_color = "background-color: #064E3B; font-weight: bold; color: #6EE7B7;" if is_benchmark else ""
    return [bg_color] * len(row)

styled_matrix = df_matrix_display.style.apply(highlight_benchmark, axis=1).format({
    "ROE (%)": "{:.1f}%",
    "OPM (%)": "{:.1f}%",
    "NPM (%)": "{:.1f}%",
    "D/E": "{:.2f}",
    "ICR": "{:.1f}x",
    "5Y Rev CAGR (%)": "{:.1f}%",
    "5Y PAT CAGR (%)": "{:.1f}%",
    "FCF (Cr)": "₹{:,.0f}"
}, na_rep="-")

st.dataframe(styled_matrix, hide_index=True, use_container_width=True, height=380)
