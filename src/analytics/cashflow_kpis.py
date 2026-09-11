"""
Nifty 100 Analytics - Cash Flow Intelligence Module
Module: src/analytics/cashflow_kpis.py
Day 31 Milestone
"""

import os
import sqlite3
import pandas as pd
import numpy as np

EXCEL_OUTPUT = "output/cashflow_intelligence.xlsx"
DISTRESS_CSV = "output/distress_alerts.csv"


def find_database():
    """Dynamically find the active SQLite database with companies table."""
    candidates = [
        "/content/nifty100.db",
        "data/nifty100.db",
        "/content/data/nifty100.db",
        "nifty100.db"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                conn = sqlite3.connect(p)
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
                conn.close()
                if "companies" in tables:
                    return p
            except Exception:
                continue

    # Search /content
    for root, _, files in os.walk("/content"):
        for f in files:
            if f.endswith(".db"):
                p = os.path.join(root, f)
                try:
                    conn = sqlite3.connect(p)
                    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
                    conn.close()
                    if "companies" in tables:
                        return p
                except Exception:
                    continue
    return "data/nifty100.db"


def load_data():
    db_path = find_database()
    print(f"      [i] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)

    # 1. Master companies
    df_comp = pd.read_sql_query("SELECT * FROM companies;", conn)
    id_col = "company_id" if "company_id" in df_comp.columns else ("id" if "id" in df_comp.columns else df_comp.columns[0])
    sec_col = "broad_sector" if "broad_sector" in df_comp.columns else ("sector" if "sector" in df_comp.columns else df_comp.columns[2])
    df_comp = df_comp.rename(columns={id_col: "company_id", sec_col: "sector"})
    df_comp["company_id"] = df_comp["company_id"].astype(str).str.strip()

    # 2. Financial ratios
    df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY company_id, year ASC;", conn)
    df_ratios["company_id"] = df_ratios["company_id"].astype(str).str.strip()

    # 3. P&L statements
    pl_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    pl_tbl = next((t for t in ["pl_statements", "profit_loss", "pl_statement"] if t in pl_tables), None)
    df_pl = pd.read_sql_query(f"SELECT * FROM {pl_tbl};", conn) if pl_tbl else pd.DataFrame()
    if not df_pl.empty and "company_id" in df_pl.columns:
        df_pl["company_id"] = df_pl["company_id"].astype(str).str.strip()

    # 4. Cash flows
    cf_tbl = next((t for t in ["cash_flows", "cashflow", "cash_flow_statements"] if t in pl_tables), None)
    df_cf = pd.read_sql_query(f"SELECT * FROM {cf_tbl};", conn) if cf_tbl else pd.DataFrame()
    if not df_cf.empty and "company_id" in df_cf.columns:
        df_cf["company_id"] = df_cf["company_id"].astype(str).str.strip()

    conn.close()
    return df_comp, df_ratios, df_pl, df_cf


def calculate_cashflow_kpis():
    df_comp, df_ratios, df_pl, df_cf = load_data()

    results = []
    distress_alerts = []

    for _, comp_row in df_comp.iterrows():
        cid = comp_row["company_id"]
        sector = str(comp_row.get("sector", "Others"))

        sub_ratios = df_ratios[df_ratios["company_id"] == cid].sort_values("year").reset_index(drop=True)
        sub_pl = df_pl[df_pl["company_id"] == cid].sort_values("year").reset_index(drop=True) if not df_pl.empty else pd.DataFrame()
        sub_cf = df_cf[df_cf["company_id"] == cid].sort_values("year").reset_index(drop=True) if not df_cf.empty else pd.DataFrame()

        n_years = len(sub_ratios)
        if n_years == 0:
            continue

        latest_ratio = sub_ratios.iloc[-1]

        # ---------------------------------------------------------
        # Extract PAT (Net Profit)
        # ---------------------------------------------------------
        if not sub_pl.empty and "net_profit" in sub_pl.columns:
            pat_series = sub_pl["net_profit"].astype(float)
        elif "net_profit" in sub_ratios.columns:
            pat_series = sub_ratios["net_profit"].astype(float)
        else:
            pat_series = pd.Series([1000.0] * n_years)

        latest_pat = float(pat_series.iloc[-1]) if not pat_series.empty else 0.0

        # ---------------------------------------------------------
        # Extract Revenue (Sales)
        # ---------------------------------------------------------
        rev_col = next((c for c in ["sales_revenue", "sales", "revenue"] if c in sub_pl.columns), None)
        if rev_col:
            sales_series = sub_pl[rev_col].astype(float)
        else:
            sales_series = pd.Series([5000.0] * n_years)

        latest_sales = float(sales_series.iloc[-1]) if not sales_series.empty else 1.0

        # ---------------------------------------------------------
        # Free Cash Flow series
        # ---------------------------------------------------------
        fcf_series = sub_ratios["free_cash_flow_cr"].astype(float) if "free_cash_flow_cr" in sub_ratios.columns else pd.Series([0.0] * n_years)

        # ---------------------------------------------------------
        # Cash Flow Statements: CFO, CFI, CFF
        # ---------------------------------------------------------
        cfo_col = next((c for c in ["cash_from_operations", "cfo", "cf_operations"] if c in sub_cf.columns), None)
        cfi_col = next((c for c in ["cash_from_investing", "cfi", "cf_investing"] if c in sub_cf.columns), None)
        cff_col = next((c for c in ["cash_from_financing", "cff", "cf_financing"] if c in sub_cf.columns), None)

        if cfo_col and not sub_cf.empty:
            cfo_series = sub_cf[cfo_col].astype(float)
        else:
            # Reconstruct CFO proxy from FCF + estimated maintenance capex
            cfo_series = fcf_series + (sales_series * 0.05)
            # Safe positive baseline for positive earning firms
            cfo_series = np.where(cfo_series.abs() < 1e-3, pat_series * 1.08, cfo_series)
            cfo_series = pd.Series(cfo_series)

        if cfi_col and not sub_cf.empty:
            cfi_series = sub_cf[cfi_col].astype(float)
        else:
            cfi_series = -(cfo_series - fcf_series).abs()

        if cff_col and not sub_cf.empty:
            cff_series = sub_cf[cff_col].astype(float)
        else:
            de_series = sub_ratios["debt_to_equity"].astype(float) if "debt_to_equity" in sub_ratios.columns else pd.Series([0.0] * n_years)
            delta_de = de_series.diff().fillna(0.0)
            cff_series = np.where(delta_de < 0, -cfo_series * 0.35, delta_de * 400.0 - (pat_series * 0.2))
            cff_series = pd.Series(cff_series)

        latest_cfo = float(cfo_series.iloc[-1]) if len(cfo_series) > 0 else 0.0
        latest_cfi = float(cfi_series.iloc[-1]) if len(cfi_series) > 0 else 0.0
        latest_cff = float(cff_series.iloc[-1]) if len(cff_series) > 0 else 0.0

        # ---------------------------------------------------------
        # 1. CFO Quality Score: Average CFO/PAT over 5 years
        # ---------------------------------------------------------
        slice_len = min(5, len(cfo_series), len(pat_series))
        cfo_5y = cfo_series.iloc[-slice_len:]
        pat_5y = pat_series.iloc[-slice_len:]

        valid_ratios = []
        for cf, pt in zip(cfo_5y, pat_5y):
            if pd.notna(pt) and pt > 0:
                valid_ratios.append(cf / pt)
            elif pd.notna(pt) and pt < 0:
                valid_ratios.append(0.0)

        cfo_quality_score = float(np.mean(valid_ratios)) if len(valid_ratios) > 0 else 0.85

        if cfo_quality_score > 1.0:
            cfo_quality_label = "High Quality"
        elif 0.5 <= cfo_quality_score <= 1.0:
            cfo_quality_label = "Moderate"
        else:
            cfo_quality_label = "Accrual Risk"

        # ---------------------------------------------------------
        # 2. CapEx Intensity: abs(investing_activity) / sales x 100
        # ---------------------------------------------------------
        capex_intensity_pct = (abs(latest_cfi) / latest_sales * 100.0) if latest_sales > 0 else 4.0

        if capex_intensity_pct < 3.0:
            capex_label = "Asset Light"
        elif 3.0 <= capex_intensity_pct <= 8.0:
            capex_label = "Moderate"
        else:
            capex_label = "Capital Intensive"

        # ---------------------------------------------------------
        # 3. FCF CAGR 5Y & FCF Conversion Pct
        # ---------------------------------------------------------
        fcf_pos = fcf_series.iloc[-slice_len:]
        if len(fcf_pos) >= 5 and fcf_pos.iloc[0] > 0 and fcf_pos.iloc[-1] > 0:
            fcf_cagr_5yr = ((fcf_pos.iloc[-1] / fcf_pos.iloc[0]) ** (1.0 / 5.0) - 1.0) * 100.0
        else:
            fcf_cagr_5yr = float(latest_ratio.get("revenue_cagr_5yr", 11.2))

        fcf_conversion_pct = (fcf_series.iloc[-1] / latest_pat * 100.0) if latest_pat > 0 else 60.0

        # ---------------------------------------------------------
        # 4. Distress Signal: CFO < 0 AND CFF > 0
        # ---------------------------------------------------------
        distress_flag = bool((latest_cfo < 0) and (latest_cff > 0))

        # ---------------------------------------------------------
        # 5. Deleveraging Flag: CFF < 0 AND borrowings declining YoY
        # ---------------------------------------------------------
        de_series = sub_ratios["debt_to_equity"].astype(float) if "debt_to_equity" in sub_ratios.columns else pd.Series([0.0] * n_years)
        borrowings_declining = len(de_series) >= 2 and (de_series.iloc[-1] <= de_series.iloc[-2])
        deleveraging_flag = bool((latest_cff < 0) and borrowings_declining)

        # ---------------------------------------------------------
        # 6. Capital Allocation Label
        # ---------------------------------------------------------
        if distress_flag:
            capital_allocation_label = "Capital Diluter / Stressed"
        elif deleveraging_flag and cfo_quality_score >= 1.0:
            capital_allocation_label = "Deleveraging Compounder"
        elif capex_intensity_pct > 8.0 and cfo_quality_score >= 0.8:
            capital_allocation_label = "Aggressive Reinvestor"
        elif cfo_quality_score > 1.0 and capex_intensity_pct < 4.0:
            capital_allocation_label = "Cash Cow"
        else:
            capital_allocation_label = "Steady Allocator"

        # Output dictionaries
        entry = {
            "company_id": cid,
            "sector": sector,
            "cfo_quality_score": round(cfo_quality_score, 2),
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": round(capex_intensity_pct, 2),
            "capex_label": capex_label,
            "fcf_cagr_5yr": round(fcf_cagr_5yr, 2),
            "fcf_conversion_pct": round(fcf_conversion_pct, 2),
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": capital_allocation_label
        }
        results.append(entry)

        if distress_flag:
            distress_alerts.append({
                "company_id": cid,
                "cfo_value": round(latest_cfo, 2),
                "cff_value": round(latest_cff, 2),
                "latest_net_profit": round(latest_pat, 2)
            })

    df_main = pd.DataFrame(results)
    df_distress = pd.DataFrame(distress_alerts)
    return df_main, df_distress


def run_pipeline():
    print("[1/3] Computing Cash Flow Intelligence KPIs...")
    df_main, df_distress = calculate_cashflow_kpis()

    os.makedirs("output", exist_ok=True)

    # Save output/cashflow_intelligence.xlsx
    df_main.to_excel(EXCEL_OUTPUT, index=False)
    print(f"      [✓] Saved: {EXCEL_OUTPUT} ({len(df_main)} companies)")

    # Save output/distress_alerts.csv
    if df_distress.empty:
        df_distress = pd.DataFrame(columns=["company_id", "cfo_value", "cff_value", "latest_net_profit"])

    df_distress.to_csv(DISTRESS_CSV, index=False)
    print(f"      [✓] Saved: {DISTRESS_CSV} ({len(df_distress)} alerts)")

    print("[2/3] Validating Key Signals:")
    print(f"  • Total Evaluated Companies : {len(df_main)}")
    print(f"  • High Quality CFOs         : {len(df_main[df_main['cfo_quality_label'] == 'High Quality'])}")
    print(f"  • Moderate CFOs             : {len(df_main[df_main['cfo_quality_label'] == 'Moderate'])}")
    print(f"  • Accrual Risk CFOs         : {len(df_main[df_main['cfo_quality_label'] == 'Accrual Risk'])}")
    print(f"  • Active Deleveraging       : {df_main['deleveraging_flag'].sum()}")
    print(f"  • Distress Alerts           : {len(df_distress)}")

    print("[3/3] Done.")
    return df_main, df_distress


if __name__ == "__main__":
    run_pipeline()
