"""
Nifty 100 Analytics - Screener Screen
Module: pages/03_screener.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios, get_connection

st.set_page_config(page_title="Parametric Screener - Nifty 100", layout="wide")

st.title("🔍 Parametric Screener & Strategy Engine")
st.caption("Filter the Nifty 100 universe by fundamentals, capital structure, and valuation multiples.")

PRESETS = {
    "Quality": {
        "roe_min": 18.0, "de_max": 0.5, "fcf_min": 100.0, "rev_cagr_min": 10.0,
        "pat_cagr_min": 10.0, "opm_min": 15.0, "pe_max": 65.0, "pb_max": 15.0,
        "div_min": 0.5, "icr_min": 5.0
    },
    "Value": {
        "roe_min": 10.0, "de_max": 1.0, "fcf_min": 0.0, "rev_cagr_min": 5.0,
        "pat_cagr_min": 5.0, "opm_min": 8.0, "pe_max": 25.0, "pb_max": 3.0,
        "div_min": 1.5, "icr_min": 3.0
    },
    "Growth": {
        "roe_min": 15.0, "de_max": 1.0, "fcf_min": 0.0, "rev_cagr_min": 15.0,
        "pat_cagr_min": 15.0, "opm_min": 12.0, "pe_max": 80.0, "pb_max": 20.0,
        "div_min": 0.0, "icr_min": 3.0
    },
    "Dividend": {
        "roe_min": 12.0, "de_max": 0.8, "fcf_min": 100.0, "rev_cagr_min": 0.0,
        "pat_cagr_min": 0.0, "opm_min": 10.0, "pe_max": 40.0, "pb_max": 6.0,
        "div_min": 2.0, "icr_min": 4.0
    },
    "Debt-Free": {
        "roe_min": 12.0, "de_max": 0.05, "fcf_min": 0.0, "rev_cagr_min": 5.0,
        "pat_cagr_min": 5.0, "opm_min": 10.0, "pe_max": 60.0, "pb_max": 15.0,
        "div_min": 0.0, "icr_min": 10.0
    },
    "Turnaround": {
        "roe_min": 8.0, "de_max": 1.5, "fcf_min": -500.0, "rev_cagr_min": 0.0,
        "pat_cagr_min": 12.0, "opm_min": 5.0, "pe_max": 35.0, "pb_max": 4.0,
        "div_min": 0.0, "icr_min": 2.0
    }
}

default_preset = PRESETS["Quality"]
for k, v in default_preset.items():
    if k not in st.session_state:
        st.session_state[k] = v

def apply_preset(preset_name):
    chosen = PRESETS[preset_name]
    for key, val in chosen.items():
        st.session_state[key] = val

st.markdown("##### ⚡ Quick Strategy Presets")
c_p1, c_p2, c_p3, c_p4, c_p5, c_p6, c_reset = st.columns([1, 1, 1, 1, 1, 1, 1])
if c_p1.button("🏆 Quality", use_container_width=True): apply_preset("Quality")
if c_p2.button("💎 Value", use_container_width=True): apply_preset("Value")
if c_p3.button("🚀 Growth", use_container_width=True): apply_preset("Growth")
if c_p4.button("💰 Dividend", use_container_width=True): apply_preset("Dividend")
if c_p5.button("🛡️ Debt-Free", use_container_width=True): apply_preset("Debt-Free")
if c_p6.button("🔄 Turnaround", use_container_width=True): apply_preset("Turnaround")
if c_reset.button("🔄 Reset All", use_container_width=True): apply_preset("Quality")

st.markdown("---")

st.sidebar.header("Filter Criteria")
roe_min = st.sidebar.slider("ROE Min (%)", min_value=0.0, max_value=50.0, step=1.0, key="roe_min")
de_max = st.sidebar.slider("Debt-to-Equity Max", min_value=0.0, max_value=4.0, step=0.05, key="de_max")
fcf_min = st.sidebar.slider("FCF Min (₹ Cr)", min_value=-2000.0, max_value=10000.0, step=250.0, key="fcf_min")
rev_cagr_min = st.sidebar.slider("5Y Revenue CAGR Min (%)", min_value=-5.0, max_value=40.0, step=1.0, key="rev_cagr_min")
pat_cagr_min = st.sidebar.slider("5Y PAT CAGR Min (%)", min_value=-5.0, max_value=40.0, step=1.0, key="pat_cagr_min")
opm_min = st.sidebar.slider("Operating Margin (OPM) Min (%)", min_value=0.0, max_value=50.0, step=1.0, key="opm_min")
pe_max = st.sidebar.slider("P/E Ratio Max", min_value=5.0, max_value=120.0, step=2.5, key="pe_max")
pb_max = st.sidebar.slider("P/B Ratio Max", min_value=0.5, max_value=30.0, step=0.5, key="pb_max")
div_min = st.sidebar.slider("Dividend Yield Min (%)", min_value=0.0, max_value=8.0, step=0.25, key="div_min")
icr_min = st.sidebar.slider("Interest Coverage Ratio Min (ICR)", min_value=0.0, max_value=25.0, step=1.0, key="icr_min")

# Fetch Core Data
df_comp = get_companies()
df_ratios = get_ratios(year="2024")
if df_ratios.empty:
    df_ratios = get_ratios()

if df_comp.empty or df_ratios.empty:
    st.error("No screening data available.")
    st.stop()

# Join latest ratios per company
df_latest = df_ratios.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
df_full = pd.merge(df_comp, df_latest, on="company_id", how="inner")

# Load valuation data from stock_prices or market_cap if available
try:
    conn = get_connection()
    df_prices = pd.read_sql_query("SELECT company_id, current_price FROM stock_prices GROUP BY company_id;", conn)
    df_full = pd.merge(df_full, df_prices, on="company_id", how="left")
    conn.close()
except Exception:
    pass

# Ensure standard column mapping matching database schema
df_full["std_roe"] = df_full["return_on_equity_pct"].fillna(0.0)
df_full["std_de"] = df_full["debt_to_equity"].fillna(0.0)
df_full["std_fcf"] = df_full["free_cash_flow_cr"].fillna(0.0)
df_full["std_rev_cagr"] = df_full["revenue_cagr_5yr"].fillna(0.0)
df_full["std_pat_cagr"] = df_full["pat_cagr_5yr"].fillna(df_full["std_rev_cagr"])
df_full["std_opm"] = df_full["operating_profit_margin_pct"].fillna(0.0)
df_full["std_icr"] = df_full["interest_coverage"].fillna(15.0)
df_full["std_score"] = df_full["composite_quality_score"].fillna(
    (df_full["std_roe"] * 0.4 + (1.0 / (df_full["std_de"] + 0.1)) * 10.0 + df_full["std_opm"] * 0.3).round(1)
)

# Valuation Calculations (P/E, P/B, Dividend Yield)
if "current_price" in df_full.columns and "earnings_per_share" in df_full.columns:
    eps = df_full["earnings_per_share"].replace(0, np.nan)
    df_full["std_pe"] = (df_full["current_price"] / eps).clip(lower=1.0, upper=150.0).fillna(25.0)
else:
    df_full["std_pe"] = pd.Series(25.0, index=df_full.index)

if "current_price" in df_full.columns and "book_value_per_share" in df_full.columns:
    bv = df_full["book_value_per_share"].replace(0, np.nan)
    df_full["std_pb"] = (df_full["current_price"] / bv).clip(lower=0.5, upper=40.0).fillna(3.5)
else:
    df_full["std_pb"] = pd.Series(3.5, index=df_full.index)

df_full["std_div"] = (df_full.get("dividend_payout_ratio_pct", pd.Series(15.0, index=df_full.index)).fillna(15.0) * 0.08).clip(0.0, 8.0)

# Filter criteria
cond = (
    (df_full["std_roe"] >= roe_min) &
    (df_full["std_de"] <= de_max) &
    (df_full["std_fcf"] >= fcf_min) &
    (df_full["std_rev_cagr"] >= rev_cagr_min) &
    (df_full["std_pat_cagr"] >= pat_cagr_min) &
    (df_full["std_opm"] >= opm_min) &
    (df_full["std_pe"] <= pe_max) &
    (df_full["std_pb"] <= pb_max) &
    (df_full["std_div"] >= div_min) &
    (df_full["std_icr"] >= icr_min)
)

df_screened = df_full[cond].copy()
count = len(df_screened)

col_count, col_dl = st.columns([7, 3])
with col_count:
    st.markdown(f"### 🎯 **{count} companies match your filters** (Universe: {len(df_full)})")

export_df = pd.DataFrame({
    "Ticker": df_screened["company_id"],
    "Company Name": df_screened["company_name"],
    "Sector": df_screened["broad_sector"],
    "Score": df_screened["std_score"],
    "ROE (%)": df_screened["std_roe"].round(2),
    "D/E": df_screened["std_de"].round(2),
    "FCF (Cr)": df_screened["std_fcf"].round(0),
    "Rev CAGR (%)": df_screened["std_rev_cagr"].round(2),
    "PAT CAGR (%)": df_screened["std_pat_cagr"].round(2),
    "OPM (%)": df_screened["std_opm"].round(2),
    "P/E": df_screened["std_pe"].round(1),
    "P/B": df_screened["std_pb"].round(1),
    "Div Yield (%)": df_screened["std_div"].round(2)
}).sort_values("Score", ascending=False)

with col_dl:
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Results (CSV)",
        data=csv_bytes,
        file_name="nifty100_screened_stocks.csv",
        mime="text/csv",
        use_container_width=True
    )

st.dataframe(export_df, hide_index=True, use_container_width=True, height=420)
