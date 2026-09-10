# 📋 Sprint 4 Retrospective: UI/UX, Valuation & Integration QA

**Sprint Period:** Days 23 – 28  
**Scope:** Complete implementation of all 8 Streamlit screens, SQLite backend integrations, Valuation Engine, Edge-Case Hardening, and Integration QA.

---

### 1. Key UX Decisions
* **Card Scaffolding Over Text**: Replaced flat markdown metrics with card containers styled using CSS linear gradients, soft box shadows, and distinct accent borders for immediate scannability.
* **Session State Preset Buttons**: Linked preset buttons (*Quality, Value, Growth, Dividend, Debt-Free, Turnaround*) directly to Streamlit session-state keys to update all 10 sidebar sliders dynamically.
* **Dynamic Visual Flags**: Built an automated health checklist on the Company Profile screen that uses condition checks on leverage and cash generation to output green checks and red flags.
* **Zero-Overflow Layouts**: Restricted Plotly charts to responsive container widths with tight margins (`margin=dict(t=20, b=20, l=20, r=20)`), preventing horizontal scrolling across viewports.

---

### 2. Data Edge Cases Discovered & Resolved
* **Valuation Multi-Year Fan-out**: The initial valuation query merged multi-year historical ratios without filtering, resulting in 552 records. Resolved by grouping and taking `.last()` per company, isolating the exact 92 Nifty 100 universe constituents.
* **Anti-Scraping 403 Forbidden Errors**: External exchanges (BSE/NSE) blocked automated HTTP HEAD calls with 403 status codes. Created a dedicated `annual_reports` table inside `nifty100.db` to serve validated filing portals and display green/red availability badges reliably.
* **Partial Historical Records**: Identified that 5 recent IPO listings (`ADANIGREEN`, `ATGL`, `HAL`, `JIOFIN`, `LICI`) had fewer than 10 years of data. Handled this safely by displaying an informational banner (`Data available for X years only`) rather than crashing when plotting historical charts.
* **Missing Multiples in SQLite**: Discovered that `price_to_earnings` and `price_to_book` were not present in `financial_ratios`. Derived both metrics dynamically using share prices, EPS, and Book Value, with fallbacks to 5-year historical medians.

---

### 3. Performance & QA Benchmarks
* **Company Profile Assembly Speed**: Measured data retrieval time across 5 core companies:
  * `TCS`: 0.0031s
  * `INFY`: 0.0013s
  * `HDFCBANK`: 0.0018s
  * `ICICIBANK`: 0.0013s
  * `ITC`: 0.0012s
  * **Mean Query Latency**: **~0.0017 seconds**, easily beating the < 3.0s specification.
* **Screener Boundary Resilience**: Tested extreme slider parameters (all minimums vs. all maximums). Both scenarios completed cleanly with zero unhandled exceptions.

---

### 4. Sprint 4 Task Board Completion
- [x] **Day 23**: Home Screen (`01_home.py`) & Company Profile Screen (`02_profile.py`) [COMPLETED]
- [x] **Day 24**: Parametric Screener (`03_screener.py`) & Peer Benchmarking (`04_peers.py`) [COMPLETED]
- [x] **Day 25**: Trend Analysis (`05_trends.py`), Sector Landscape (`06_sectors.py`), Capital Allocation (`07_capital.py`), & Annual Reports (`08_reports.py`) [COMPLETED]
- [x] **Day 26**: Valuation Analytics Module (`src/analytics/valuation.py`), Excel & CSV Exports [COMPLETED]
- [x] **Day 27**: Integration QA, Multi-Sector Stress Testing & Latency Benchmarks [COMPLETED]
- [x] **Day 28**: Production Documentation (`README.md`), Retrospective Sign-Off & Demo Walkthrough [COMPLETED]
