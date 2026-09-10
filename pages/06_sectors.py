"""
Nifty 100 Analytics - Sector Analysis Screen
Module: pages/06_sectors.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios, get_sectors, get_connection

st.set_page_config(page_title="Sector Analysis - Nifty 100", layout="wide")

st.title("🌐 Multi-Sector Landscape & Median Benchmarks")

df_comp = get_companies()
df_ratios = get_ratios(year="2024")
if df_ratios.empty:
    df_ratios = get_ratios()

if df_comp.empty or df_ratios.empty:
    st.error("Universe or ratio data unavailable.")
    st.stop()

# Join latest data
df_latest = df_ratios.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
df_merged = pd.merge(df_comp, df_latest, on="company_id", how="inner")

# Approximate Sales/Revenue size proxy for X-axis & Bubble Size
try:
    conn = get_connection()
    df_pl = pd.read_sql_query("SELECT company_id, sales_revenue FROM pl_statements GROUP BY company_id;", conn)
    df_merged = pd.merge(df_merged, df_pl, on="company_id", how="left")
    conn.close()
except Exception:
    df_merged["sales_revenue"] = df_merged.get("free_cash_flow_cr", 500).abs() * 5.0

df_merged["sales_revenue"] = df_merged["sales_revenue"].fillna(5000.0).clip(lower=500.0)
df_merged["bubble_size"] = df_merged["free_cash_flow_cr"].fillna(500).abs().clip(lower=100.0, upper=30000.0)

# 1. Sector Dropdown
sectors = sorted(df_merged["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", options=["All Sectors"] + sectors, index=0)

df_view = df_merged if selected_sector == "All Sectors" else df_merged[df_merged["broad_sector"] == selected_sector]

# 2. Bubble Chart: X = Revenue, Y = ROE, Size = Market Cap / Cash proxy, Color = Sub-Sector
st.subheader("🎯 Revenue vs. Return on Equity (Bubble Sized by Cash Generation)")
fig_bubble = px.scatter(
    df_view,
    x="sales_revenue",
    y="return_on_equity_pct",
    size="bubble_size",
    color="sub_sector",
    hover_name="company_name",
    hover_data=["company_id", "operating_profit_margin_pct", "debt_to_equity"],
    labels={
        "sales_revenue": "Sales Revenue (₹ Cr)",
        "return_on_equity_pct": "Return on Equity (%)",
        "sub_sector": "Sub-Sector"
    },
    log_x=True,
    height=450
)
fig_bubble.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#FFFFFF"),
    xaxis=dict(gridcolor="#334155"),
    yaxis=dict(gridcolor="#334155")
)
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# 3. Sector Median KPI Bar Chart
st.subheader("📊 Sector Median Fundamentals Comparison")
df_grouped = df_merged.groupby("broad_sector").agg({
    "return_on_equity_pct": "median",
    "operating_profit_margin_pct": "median",
    "debt_to_equity": "median",
    "revenue_cagr_5yr": "median"
}).reset_index()

kpi_choice = st.radio(
    "Select Median Metric",
    options=["return_on_equity_pct", "operating_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr"],
    format_func=lambda x: {
        "return_on_equity_pct": "Median ROE (%)",
        "operating_profit_margin_pct": "Median Operating Margin (%)",
        "debt_to_equity": "Median Debt to Equity",
        "revenue_cagr_5yr": "Median 5Y Revenue CAGR (%)"
    }[x],
    horizontal=True
)

fig_bar = px.bar(
    df_grouped.sort_values(kpi_choice, ascending=True),
    x=kpi_choice,
    y="broad_sector",
    orientation='h',
    color=kpi_choice,
    color_continuous_scale="Viridis",
    height=360
)
fig_bar.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#FFFFFF"),
    yaxis=dict(title="", gridcolor="#334155"),
    xaxis=dict(gridcolor="#334155"),
    coloraxis_showscale=False
)
st.plotly_chart(fig_bar, use_container_width=True)
