"""
Nifty 100 Fundamental Analytics - NLP Analysis Text Parser
Module: src/nlp/parser.py
Day 29 Milestone
"""

import os
import re
import sqlite3
import pandas as pd
import numpy as np

# File paths
ANALYSIS_EXCEL = "data/analysis.xlsx"
DB_PATH = "data/nifty100.db"
PARSED_CSV = "output/analysis_parsed.csv"
FAILURES_CSV = "output/parse_failures.csv"
DIVERGENCE_CSV = "output/cagr_divergence_flags.csv"

# Target fields to parse
TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]

# Required regex: extracts period (e.g. 10) and value (e.g. 21.0)
# Handles variations like "10 Years: 21%", "5 Year: 14.5%", "3 Years: -2%"
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([+-]?\d+(?:\.\d+)?)%", re.IGNORECASE)


def load_analysis_data():
    """Load raw analysis.xlsx with fallback detection."""
    if not os.path.exists(ANALYSIS_EXCEL):
        # Fallback to current directory or input variations if path differs
        candidates = ["analysis.xlsx", "/content/data/analysis.xlsx", "/content/analysis.xlsx"]
        for cand in candidates:
            if os.path.exists(cand):
                return pd.read_excel(cand)
        raise FileNotFoundError(f"Cannot find analysis file at {ANALYSIS_EXCEL}")
    return pd.read_excel(ANALYSIS_EXCEL)


def parse_text_fields(df_raw):
    """Parse target text columns into structured records and log unparseable entries."""
    parsed_records = []
    failure_records = []

    # Detect company identifier column
    id_col = next((c for c in ["company_id", "ticker", "id", "symbol", "company_name"] if c in df_raw.columns), None)
    if not id_col:
        id_col = df_raw.columns[0]

    for idx, row in df_raw.iterrows():
        comp_id = str(row[id_col]).strip()

        for field in TARGET_FIELDS:
            if field not in df_raw.columns:
                continue

            raw_val = row[field]
            if pd.isna(raw_val) or not str(raw_val).strip():
                continue

            raw_text = str(raw_val).strip()

            # Find all matches within the text cell
            matches = PATTERN.findall(raw_text)

            if matches:
                for period_str, val_str in matches:
                    try:
                        period_years = int(period_str)
                        value_pct = float(val_str)
                        parsed_records.append({
                            "company_id": comp_id,
                            "metric_type": field,
                            "period_years": period_years,
                            "value_pct": value_pct
                        })
                    except ValueError:
                        failure_records.append({
                            "company_id": comp_id,
                            "metric_type": field,
                            "raw_text": raw_text,
                            "reason": f"Conversion error for match ({period_str}, {val_str})"
                        })
            else:
                # Text present but regex pattern failed to find matches
                failure_records.append({
                    "company_id": comp_id,
                    "metric_type": field,
                    "raw_text": raw_text,
                    "reason": "Pattern mismatch / non-conforming format"
                })

    df_parsed = pd.DataFrame(parsed_records)
    df_failures = pd.DataFrame(failure_records)

    return df_parsed, df_failures


def cross_validate_cagr(df_parsed):
    """
    Cross-validate parsed 5-year CAGR values against database ratios.
    Flags divergence > 5% for manual review.
    """
    if not os.path.exists(DB_PATH):
        print(f"[!] Database {DB_PATH} not found. Skipping cross-validation.")
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        df_ratios = pd.read_sql_query(
            "SELECT company_id, year, revenue_cagr_5yr, net_profit_cagr_5yr FROM financial_ratios;",
            conn
        )
    except Exception:
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df_ratios.empty:
        return pd.DataFrame()

    # Get latest computed CAGR per company
    latest_ratios = df_ratios.sort_values(["company_id", "year"]).groupby("company_id").last().reset_index()

    divergence_records = []

    # Map target metrics to DB ratio fields
    field_db_map = {
        "compounded_sales_growth": "revenue_cagr_5yr",
        "compounded_profit_growth": "net_profit_cagr_5yr"
    }

    for _, row in df_parsed[df_parsed["period_years"] == 5].iterrows():
        cid = row["company_id"]
        metric = row["metric_type"]
        parsed_val = row["value_pct"]

        db_col = field_db_map.get(metric)
        if not db_col:
            continue

        comp_ratio = latest_ratios[latest_ratios["company_id"] == cid]
        if not comp_ratio.empty and pd.notna(comp_ratio[db_col].values[0]):
            computed_val = float(comp_ratio[db_col].values[0])
            diff_abs = abs(parsed_val - computed_val)

            # Divergence > 5% flag
            if diff_abs > 5.0:
                divergence_records.append({
                    "company_id": cid,
                    "metric_type": metric,
                    "period_years": 5,
                    "parsed_cagr_pct": parsed_val,
                    "computed_cagr_pct": computed_val,
                    "absolute_diff_pct": round(diff_abs, 2),
                    "review_status": "FLAGGED_FOR_REVIEW"
                })

    return pd.DataFrame(divergence_records)


def run_pipeline():
    """Execute text parser and cross-validation pipeline."""
    print("[1/4] Loading analysis raw file...")
    df_raw = load_analysis_data()
    print(f"      Loaded {len(df_raw)} rows from analysis source.")

    print("[2/4] Parsing text fields with regex...")
    df_parsed, df_failures = parse_text_fields(df_raw)

    os.makedirs("output", exist_ok=True)

    # Save parsed records
    df_parsed.to_csv(PARSED_CSV, index=False)
    print(f"      [✓] Saved parsed records: {PARSED_CSV} ({len(df_parsed)} entries)")

    # Save failure records
    df_failures.to_csv(FAILURES_CSV, index=False)
    print(f"      [✓] Saved parsing failures: {FAILURES_CSV} ({len(df_failures)} entries)")

    print("[3/4] Cross-validating against Ratio Engine calculations...")
    df_divergence = cross_validate_cagr(df_parsed)

    if not df_divergence.empty:
        df_divergence.to_csv(DIVERGENCE_CSV, index=False)
        print(f"      [!] Found {len(df_divergence)} CAGR divergences > 5%. Saved to: {DIVERGENCE_CSV}")
    else:
        print("      [✓] Zero material divergences (> 5%) detected between parsed and computed values.")

    print("[4/4] Pipeline completed.")
    return df_parsed, df_failures, df_divergence


if __name__ == "__main__":
    run_pipeline()
