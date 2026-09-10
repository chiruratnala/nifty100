"""
Nifty 100 Analytics - Streamlit Dashboard Entry Point
Module: src/dashboard/app.py
"""

import streamlit as st
import sys
import os

# Set wide layout and expanded sidebar
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Nifty 100 Financial Analytics & Valuation Engine")
st.caption("Institutional Quantitative Screening, Peer Benchmarking & Fundamental Analysis Dashboard")

st.markdown("""
---
### Welcome to the Nifty 100 Quantitative Platform

Use the **sidebar menu on the left** to navigate across the 8 analytical screens:

1. **🏠 01 Home**: Universe-wide aggregate KPIs, sector breakdown, and top-ranked quality franchises.
2. **🏢 02 Profile**: 10-year financial performance, dual-axis margin trends, and company tear-sheets.
3. **🔍 03 Screener**: Multi-metric parametric filtering with 6 automated strategy presets & CSV export.
4. **👥 04 Peers**: 11-group peer matrix comparisons and dynamic 8-axis polar radar charts.
5. **📊 05 Trends**: Multi-metric historical overlays and YoY growth decomposition.
6. **🌐 06 Sectors**: Sub-sector distribution, ROE vs. Revenue bubble charts, and sector medians.
7. **🧱 07 Capital**: Capital allocation classifications (Reinvestors, Cash Cows, Dividend Compounders).
8. **📑 08 Reports**: Corporate governance repository and annual filings index.
---
""")

st.sidebar.title("Navigation")
st.sidebar.info("Select any page above to begin analysis.")
st.sidebar.markdown("**Engine Status**: `Operational`")
st.sidebar.markdown("**Coverage**: `91 Constituents`")
st.sidebar.markdown("**Benchmark Groups**: `11 Sectors`")
