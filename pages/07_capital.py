"""
Nifty 100 Analytics - Capital Allocation Map
Module: pages/07_capital.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Capital Allocation - Nifty 100", layout="wide")

st.title("🗺️ Capital Allocation Patterns & Corporate Strategy Map")
st.caption("Categorization of all 92 constituents into 8 classic corporate reinvestment archetypes.")

df_comp = get_companies()
df_ratios = get_ratios(year="2024")
if df_ratios.empty:
    df_ratios = get_ratios()

if df_comp.empty or df_ratios.empty:
    st.error("Universe or ratio data unavailable.")
    st.stop()

# Latest ratio snapshot
df_latest = df_ratios.sort_values("year", ascending=False).groupby("company_id").first().reset_index()
df_full = pd.merge(df_comp, df_latest, on="company_id", how="inner")

# Categorize companies into 8 Capital Allocation Patterns
def assign_pattern(row):
    roe = row.get("return_on_equity_pct", 0) or 0
    de = row.get("debt_to_equity", 0) or 0
    fcf = row.get("free_cash_flow_cr", 0) or 0
    capex = row.get("capex_cr", 0) or 0

    if roe >= 20 and fcf > 0 and de <= 0.3:
        return "1. Compounders (High ROE, Debt-Free FCF)"
    elif roe >= 15 and capex > 2000 and de <= 0.8:
        return "2. Aggressive Reinvestors (High Growth Capex)"
    elif de > 1.2 and row.get("broad_sector") != "Financials":
        return "3. Leveraged Expanders (Debt-Financed)"
    elif fcf > 2000 and roe < 15:
        return "4. Cash Cows (Moderate ROE, High FCF)"
    elif roe >= 15 and de > 0.5:
        return "5. Efficient Levered Returners"
    elif fcf <= 0 and capex > 1000:
        return "6. Heavy Incubators (Negative FCF / Heavy Capex)"
    elif roe < 10 and de <= 0.5:
        return "7. Conservative Consolidators (Low Debt, Low ROE)"
    else:
        return "8. Value Cyclicals / Turnarounds"

df_full["allocation_pattern"] = df_full.apply(assign_pattern, axis=1)

# 1. Plotly Treemap
fig_tree = px.treemap(
    df_full,
    path=["allocation_pattern", "broad_sector", "company_id"],
    color="return_on_equity_pct",
    color_continuous_scale="Blues",
    hover_data=["company_name", "return_on_equity_pct", "debt_to_equity"],
    height=540
)
fig_tree.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#FFFFFF")
)
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# 2. Interactive Pattern Selector & Constituent Table
st.subheader("📋 Drill-down by Capital Allocation Pattern")
pattern_list = sorted(df_full["allocation_pattern"].unique().tolist())
selected_pat = st.selectbox("Choose Pattern", options=pattern_list, index=0)

df_pat = df_full[df_full["allocation_pattern"] == selected_pat].copy()
st.info(f"**{len(df_pat)} constituents** classified under `{selected_pat}`")

display_cols = ["company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"]
df_pat_show = df_pat[display_cols].rename(columns={
    "company_id": "Ticker",
    "company_name": "Company Name",
    "broad_sector": "Sector",
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)"
})

st.dataframe(df_pat_show, hide_index=True, use_container_width=True)
