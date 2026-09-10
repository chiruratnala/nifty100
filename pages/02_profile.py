"""
Nifty 100 Analytics - Company Profile Screen (QA Hardened)
Module: pages/02_profile.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_connection

st.set_page_config(page_title="Company Profile - Nifty 100", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-top: 3px solid #10b981;
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
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

df_companies = get_companies()

st.title("🏢 Company Profile & Fundamental Tearsheet")

if df_companies.empty:
    st.error("No company records found in database.")
    st.stop()

company_options = [""] + (df_companies["company_id"] + " - " + df_companies["company_name"]).tolist()
selected_query = st.selectbox(
    "Search Company by Ticker or Name",
    options=company_options,
    index=1 if len(company_options) > 1 else 0
)

if not selected_query:
    st.info("Ticker not found — please try another")
    st.stop()

ticker = selected_query.split(" - ")[0].strip()
comp_meta = df_companies[df_companies["company_id"] == ticker]

if comp_meta.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

meta_row = comp_meta.iloc[0]

about_text = "No description available."
try:
    conn = get_connection()
    c_info = conn.execute("SELECT about_company FROM companies WHERE id = ?", (ticker,)).fetchone()
    if c_info and c_info[0]:
        about_text = c_info[0]
    conn.close()
except Exception:
    pass

st.markdown(f"## **{meta_row['company_name']}**")
st.markdown(
    f"**NSE Ticker:** `{ticker}` | "
    f"**Sector:** `{meta_row.get('broad_sector', 'N/A')}` | "
    f"**Sub-Sector:** `{meta_row.get('sub_sector', 'N/A')}`"
)
with st.expander("📖 About Company", expanded=False):
    st.write(about_text)

st.markdown("<hr style='margin: 18px 0; border-color: #334155;'>", unsafe_allow_html=True)

# Helper function for safe metric formatting
def fmt_val(val, unit="", decimals=1):
    if val is None or pd.isna(val):
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}{unit}"
    except Exception:
        return "N/A"

df_ratios = get_ratios(ticker=ticker)

def render_kpi(col, title, val_str):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{val_str}</div>
    </div>
    """, unsafe_allow_html=True)

if not df_ratios.empty:
    years_available = len(df_ratios["year"].unique())
    if years_available < 10:
        st.info(f"ℹ️ Note: Historical financial data available for **{years_available} years only** for this company.")

    latest = df_ratios.sort_values("year", ascending=False).iloc[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    render_kpi(c1, "Return on Equity", fmt_val(latest.get('return_on_equity_pct'), "%"))
    render_kpi(c2, "ROCE", fmt_val(latest.get('return_on_capital_employed_pct'), "%"))
    render_kpi(c3, "Net Margin", fmt_val(latest.get('net_profit_margin_pct'), "%"))
    render_kpi(c4, "Debt-to-Equity", fmt_val(latest.get('debt_to_equity'), "", 2))
    render_kpi(c5, "5Y Rev CAGR", fmt_val(latest.get('revenue_cagr_5yr'), "%"))
    
    fcf_raw = latest.get('free_cash_flow_cr')
    fcf_formatted = f"₹{float(fcf_raw):,.0f} Cr" if (fcf_raw is not None and pd.notna(fcf_raw)) else "N/A"
    render_kpi(c6, "FCF (Latest)", fcf_formatted)

    st.markdown("<hr style='margin: 20px 0; border-color: #334155;'>", unsafe_allow_html=True)

    # 10-Year Revenue & Net Profit Bar
    df_pl = get_pl(ticker)
    if not df_pl.empty:
        rev_col = next((c for c in ["sales_revenue", "sales", "revenue"] if c in df_pl.columns), None)
        pat_col = next((c for c in ["net_profit", "pat"] if c in df_pl.columns), None)

        if rev_col and pat_col:
            st.subheader("📈 Revenue & Net Profit Trajectory (₹ Cr)")
            fig_fin = go.Figure()
            fig_fin.add_trace(go.Bar(x=df_pl["year"], y=df_pl[rev_col], name="Sales Revenue", marker_color="#38BDF8"))
            fig_fin.add_trace(go.Bar(x=df_pl["year"], y=df_pl[pat_col], name="Net Profit (PAT)", marker_color="#10B981"))
            fig_fin.update_layout(
                barmode='group', height=360,
                autosize=True,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20, b=20, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fin, use_container_width=True)

    # Dual-Axis ROE vs ROCE Chart
    if "return_on_equity_pct" in df_ratios.columns:
        st.subheader("🔄 Return Trends: ROE vs. ROCE (%)")
        df_ratios_sorted = df_ratios.sort_values("year", ascending=True)

        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Scatter(x=df_ratios_sorted["year"], y=df_ratios_sorted["return_on_equity_pct"], name="ROE (%)", mode="lines+markers", line=dict(color="#F59E0B", width=3)),
            secondary_y=False
        )

        roce_col = "return_on_capital_employed_pct" if "return_on_capital_employed_pct" in df_ratios_sorted.columns else None
        if roce_col:
            fig_dual.add_trace(
                go.Scatter(x=df_ratios_sorted["year"], y=df_ratios_sorted[roce_col], name="ROCE (%)", mode="lines+markers", line=dict(color="#60A5FA", width=2, dash="dash")),
                secondary_y=True
            )

        fig_dual.update_layout(
            height=340, autosize=True,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    # Fundamental Health Badges
    st.subheader("📋 Fundamental Health Checklist")
    col_pros, col_cons = st.columns(2)
    roe_val = latest.get("return_on_equity_pct")
    de_val = latest.get("debt_to_equity")
    fcf_latest = latest.get("free_cash_flow_cr")

    with col_pros:
        st.markdown("#### **Strengths**")
        if pd.notna(roe_val) and float(roe_val) >= 15.0:
            st.success(f"✅ Strong Capital Return: ROE is high at {float(roe_val):.1f}% (≥ 15%)")
        if pd.notna(de_val) and float(de_val) <= 0.5:
            st.success(f"✅ Conservative Leverage: Debt-to-Equity is low at {float(de_val):.2f} (≤ 0.5)")
        if pd.notna(fcf_latest) and float(fcf_latest) > 0:
            st.success(f"✅ Cash Generator: Positive Free Cash Flow (₹{float(fcf_latest):,.0f} Cr)")

    with col_cons:
        st.markdown("#### **Watch Items**")
        if pd.notna(roe_val) and float(roe_val) < 15.0:
            st.warning(f"❌ Sub-15% ROE: Capital efficiency is modest ({float(roe_val):.1f}%)")
        if pd.notna(de_val) and float(de_val) > 1.0 and meta_row.get("broad_sector") != "Financials":
            st.error(f"❌ Elevated Leverage: Debt-to-Equity is {float(de_val):.2f} (> 1.0)")
        if pd.notna(fcf_latest) and float(fcf_latest) <= 0:
            st.error("❌ Cash Drag: Free cash flow is negative or zero")
else:
    st.warning("Historical financial ratio records not available for this ticker.")
