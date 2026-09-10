"""
Nifty 100 Analytics - Annual Reports Repository
Module: pages/08_reports.py
"""

import streamlit as st
import pandas as pd
import requests
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_companies, get_connection

st.set_page_config(page_title="Annual Reports - Nifty 100", layout="wide")

st.title("📑 Annual Report Repository & Document Index")
st.caption("Access audited annual filings, financial statements, and regulatory disclosures.")

df_companies = get_companies()
if df_companies.empty:
    st.error("No companies found in database.")
    st.stop()

# 1. Company Search
company_options = (df_companies["company_id"] + " - " + df_companies["company_name"]).tolist()
selected_comp = st.selectbox("Search Company by Ticker or Name", options=company_options, index=0)
ticker = selected_comp.split(" - ")[0].strip()
comp_name = selected_comp.split(" - ")[1].strip()

st.subheader(f"Available Filings: {comp_name} (`{ticker}`)")

# 2. Query Annual Reports from Database
conn = get_connection()
filings = conn.execute("""
    SELECT year, report_url, is_available 
    FROM annual_reports 
    WHERE company_id = ? 
    ORDER BY year DESC;
""", (ticker,)).fetchall()
conn.close()

# 3. Render Table
if filings:
    for yr, url, is_avail in filings:
        col_yr, col_link, col_badge = st.columns([2, 5, 3])

        with col_yr:
            st.markdown(f"**FY {yr}**")

        with col_link:
            if is_avail:
                st.markdown(f"📄 [{ticker} Annual Report FY {yr} (PDF / Filing Portal)]({url})")
            else:
                st.markdown(f"📄 <span style='color: #64748B;'>{ticker} Annual Report FY {yr} (Archived)</span>", unsafe_allow_html=True)

        with col_badge:
            if is_avail:
                st.markdown(
                    '<span style="background-color: #064E3B; color: #6EE7B7; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">'
                    '✅ Available</span>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<span style="background-color: #7F1D1D; color: #FCA5A5; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">'
                    '❌ Report unavailable</span>',
                    unsafe_allow_html=True
                )

        st.markdown("<hr style='margin: 8px 0; border-color: #334155;'>", unsafe_allow_html=True)
else:
    st.warning("No annual report records indexed for this company.")
