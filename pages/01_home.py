"""
Nifty 100 Analytics - Home Screen
Module: pages/01_home.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios, get_sectors

st.set_page_config(page_title="Market Overview - Nifty 100", layout="wide")

# Custom Card Styling
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-top: 3px solid #38bdf8;
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.15s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-top: 3px solid #0ea5e9;
    }
    .kpi-title {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #f8fafc;
        font-size: 20px;
        font-weight: 700;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# 1. Sidebar: Year Selector
st.sidebar.header("Universe Filters")
available_years = ["2024", "2023", "2022", "2021", "2020", "2019"]
selected_year = st.sidebar.selectbox("Reporting Year", available_years, index=0)

st.title("🏠 Nifty 100 Market Overview & Universe Summary")
st.caption(f"Aggregated Performance & Sector Landscape for FY {selected_year}")

# 2. Data Retrieval
df_comp = get_companies()
df_ratios = get_ratios(year=selected_year)

if not df_ratios.empty and not df_comp.empty:
    df_merged = pd.merge(df_comp, df_ratios, on="company_id", how="inner")
else:
    df_merged = df_comp.copy()

# Metric calculations
total_companies = len(df_merged)
avg_roe = df_merged["return_on_equity_pct"].mean() if "return_on_equity_pct" in df_merged else 0.0
median_pe = df_merged["price_to_earnings"].median() if "price_to_earnings" in df_merged else 0.0
median_de = df_merged["debt_to_equity"].median() if "debt_to_equity" in df_merged else 0.0
median_rev_cagr = df_merged["revenue_cagr_5yr"].median() if "revenue_cagr_5yr" in df_merged else 0.0
debt_free_count = (df_merged["debt_to_equity"] <= 0.01).sum() if "debt_to_equity" in df_merged else 0

# Helper to render styled card
def render_kpi(col, title, val):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{val}</div>
    </div>
    """, unsafe_allow_html=True)

# 3. 6 Styled Cards
k1, k2, k3, k4, k5, k6 = st.columns(6)
render_kpi(k1, "Total Companies", f"{total_companies}")
render_kpi(k2, "Average ROE", f"{avg_roe:.1f}%")
render_kpi(k3, "Median P/E", f"{median_pe:.1f}x")
render_kpi(k4, "Median D/E", f"{median_de:.2f}")
render_kpi(k5, "5Y Rev CAGR", f"{median_rev_cagr:.1f}%")
render_kpi(k6, "Debt-Free Stocks", f"{debt_free_count}")

st.markdown("<hr style='margin: 20px 0; border-color: #334155;'>", unsafe_allow_html=True)

col_left, col_right = st.columns([5, 5])

# 4. Donut Chart
with col_left:
    st.subheader("🌐 Sector Composition (11 Benchmark Groups)")
    df_sec = get_sectors()
    if not df_sec.empty:
        fig_donut = px.pie(
            df_sec,
            names="broad_sector",
            values="company_count",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        fig_donut.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            height=360,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# 5. Top 5 Table
with col_right:
    st.subheader("⭐ Top 5 Quality Compounders")
    sort_col = "composite_quality_score" if "composite_quality_score" in df_merged.columns else "return_on_equity_pct"
    df_top5 = df_merged.sort_values(sort_col, ascending=False).head(5) if sort_col in df_merged.columns else df_merged.head(5)

    display_cols = [c for c in ["company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity"] if c in df_top5.columns]
    df_display = df_top5[display_cols].rename(columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "broad_sector": "Sector",
        "return_on_equity_pct": "ROE (%)",
        "debt_to_equity": "D/E"
    })
    st.dataframe(df_display, hide_index=True, use_container_width=True)
