"""
Nifty 100 Analytics - Trend Analysis Screen
Module: pages/05_trends.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.set_page_config(page_title="Trend Analysis - Nifty 100", layout="wide")

st.title("📈 10-Year Multi-Metric Trend Analysis")
st.caption("Overlay historical fundamental indicators with automated Year-over-Year (YoY) growth annotations.")

df_companies = get_companies()
if df_companies.empty:
    st.error("No companies found in database.")
    st.stop()

# 1. Company Search Box
company_options = (df_companies["company_id"] + " - " + df_companies["company_name"]).tolist()
selected_comp = st.selectbox("Search Company by Ticker or Name", options=company_options, index=0)
ticker = selected_comp.split(" - ")[0].strip()

# 2. Metric Options
METRIC_MAP = {
    "Return on Equity (%)": "return_on_equity_pct",
    "Operating Profit Margin (%)": "operating_profit_margin_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Debt to Equity": "debt_to_equity",
    "Free Cash Flow (Cr)": "free_cash_flow_cr",
    "Interest Coverage (x)": "interest_coverage",
    "Asset Turnover": "asset_turnover",
    "Cash from Operations (Cr)": "cash_from_operations_cr"
}

selected_metrics = st.multiselect(
    "Select up to 3 metrics to overlay",
    options=list(METRIC_MAP.keys()),
    default=["Return on Equity (%)", "Operating Profit Margin (%)"],
    max_selections=3
)

if not selected_metrics:
    st.info("Please select at least 1 metric to visualize trends.")
    st.stop()

# 3. Retrieve Historical Data
df_ratios = get_ratios(ticker=ticker)
if df_ratios.empty:
    st.warning("No historical ratio records found for this ticker.")
    st.stop()

df_sorted = df_ratios.sort_values("year", ascending=True).copy()

# 4. Plotly 10-Year Line Chart with YoY Annotations
fig = go.Figure()
palette = ["#38BDF8", "#F59E0B", "#10B981"]

for idx, m_label in enumerate(selected_metrics):
    col = METRIC_MAP[m_label]
    if col not in df_sorted.columns:
        continue

    series = df_sorted[col].astype(float)
    yoy_pct = series.pct_change() * 100

    text_labels = []
    for i, (val, pct) in enumerate(zip(series, yoy_pct)):
        if i == 0 or pd.isna(pct) or np.isinf(pct):
            text_labels.append(f"{val:.1f}")
        else:
            arrow = "+" if pct >= 0 else ""
            text_labels.append(f"{val:.1f}<br>({arrow}{pct:.0f}%)")

    fig.add_trace(go.Scatter(
        x=df_sorted["year"],
        y=series,
        name=m_label,
        mode="lines+markers+text",
        text=text_labels,
        textposition="top center",
        line=dict(color=palette[idx % len(palette)], width=3),
        marker=dict(size=7)
    ))

fig.update_layout(
    height=480,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#FFFFFF"),
    margin=dict(t=40, b=40, l=40, r=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
    xaxis=dict(title="Fiscal Year", gridcolor="#334155"),
    yaxis=dict(gridcolor="#334155")
)

st.plotly_chart(fig, use_container_width=True)
