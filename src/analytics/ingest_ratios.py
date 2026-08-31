"""
Nifty 100 Ratio Engine - Database Ingestion Pipeline
Module: src/analytics/ingest_ratios.py
Description: Computes all 14+ financial KPIs across companies and populates 
             the SQLite `financial_ratios` table.
"""

import os
import sqlite3
import logging
import pandas as pd
from typing import List, Tuple

from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_roe,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_asset_turnover,
)
from src.analytics.cagr import compute_cagr
from src.analytics.cashflow_kpis import compute_fcf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_db_connection(preferred_path: str = None) -> sqlite3.Connection:
    possible_paths = [
        preferred_path,
        "data/nifty100.db",
        "nifty100.db",
        "database/nifty100.db",
        "db/nifty100.db"
    ]
    
    valid_paths = [p for p in possible_paths if p and os.path.exists(p)]
    
    # Locate the database file that actually contains the raw tables
    for path in valid_paths:
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profitandloss';")
            if cursor.fetchone():
                return conn
            conn.close()
        except Exception:
            continue
            
    raise FileNotFoundError(
        f"Could not find an active database containing 'profitandloss'. Checked paths: {valid_paths}"
    )


def init_table(conn: sqlite3.Connection):
    """Initializes the financial_ratios table schema."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS financial_ratios;")
    cursor.execute("""
    CREATE TABLE financial_ratios (
        company_id TEXT NOT NULL,
        year TEXT NOT NULL,
        net_profit_margin_pct REAL,
        operating_profit_margin_pct REAL,
        return_on_equity_pct REAL,
        debt_to_equity REAL,
        interest_coverage REAL,
        asset_turnover REAL,
        free_cash_flow_cr REAL,
        capex_cr REAL,
        earnings_per_share REAL,
        book_value_per_share REAL,
        dividend_payout_ratio_pct REAL,
        total_debt_cr REAL,
        cash_from_operations_cr REAL,
        revenue_cagr_5yr REAL,
        pat_cagr_5yr REAL,
        eps_cagr_5yr REAL,
        composite_quality_score REAL,
        PRIMARY KEY (company_id, year)
    );
    """)
    conn.commit()
    logging.info("Initialized financial_ratios table schema.")


def extract_raw_data(conn: sqlite3.Connection) -> pd.DataFrame:
    """Extracts joined historical filings across all companies."""
    query = """
    SELECT 
        p.company_id,
        p.year,
        s.broad_sector,
        p.sales,
        p.operating_profit,
        p.other_income,
        p.interest,
        p.net_profit,
        p.eps,
        p.dividend_payout,
        b.equity_capital,
        b.reserves,
        b.borrowings,
        b.investments,
        b.total_assets,
        c.operating_activity AS cfo,
        c.investing_activity AS cfi,
        c.financing_activity AS cff
    FROM profitandloss p
    JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    LEFT JOIN cashflow c ON p.company_id = c.company_id AND p.year = c.year
    LEFT JOIN sectors s ON p.company_id = s.company_id
    ORDER BY p.company_id, p.year ASC;
    """
    df = pd.read_sql_query(query, conn)
    logging.info(f"Loaded {len(df)} company-year records for ratio generation.")
    return df


def calculate_and_insert_ratios(conn: sqlite3.Connection, df_raw: pd.DataFrame) -> int:
    """Computes all ratios and batch inserts them into financial_ratios table."""
    records_to_insert: List[Tuple] = []

    for company_id, group in df_raw.groupby("company_id"):
        group = group.sort_values("year").reset_index(drop=True)
        num_years = len(group)

        for i in range(num_years):
            row = group.iloc[i]
            yr = row["year"]

            # 1. Profitability Ratios
            npm = compute_net_profit_margin(row["net_profit"], row["sales"])
            opm, _ = compute_operating_profit_margin(row["operating_profit"], row["sales"])
            roe = compute_roe(row["net_profit"], row["equity_capital"], row["reserves"])

            # 2. Leverage & Efficiency Ratios
            de, _ = compute_debt_to_equity(row["borrowings"], row["equity_capital"], row["reserves"], row["broad_sector"])
            icr, _, _ = compute_interest_coverage(row["operating_profit"], row["other_income"], row["interest"])
            asset_to = compute_asset_turnover(row["sales"], row["total_assets"])

            # 3. Cash Flow & CapEx
            fcf = compute_fcf(row["cfo"], row["cfi"])
            capex = abs(float(row["cfi"])) if row["cfi"] is not None and not pd.isna(row["cfi"]) else None

            # 4. Per Share & Debt Metrics
            eps = float(row["eps"]) if row["eps"] is not None and not pd.isna(row["eps"]) else None
            tot_equity = (float(row["equity_capital"]) + float(row["reserves"])) if row["equity_capital"] is not None and row["reserves"] is not None else None
            bvps = None
            if tot_equity is not None and row["equity_capital"] is not None and float(row["equity_capital"]) > 0:
                bvps = round(tot_equity / (float(row["equity_capital"]) / 10.0), 2)

            div_payout = float(row["dividend_payout"]) if row["dividend_payout"] is not None and not pd.isna(row["dividend_payout"]) else None
            total_debt = float(row["borrowings"]) if row["borrowings"] is not None and not pd.isna(row["borrowings"]) else 0.0
            cfo = float(row["cfo"]) if row["cfo"] is not None and not pd.isna(row["cfo"]) else None

            # 5. 5-Year CAGR
            rev_cagr_5, pat_cagr_5, eps_cagr_5 = None, None, None
            if i >= 5:
                start_row = group.iloc[i - 5]
                rev_cagr_5, _ = compute_cagr(start_row["sales"], row["sales"], 5)
                pat_cagr_5, _ = compute_cagr(start_row["net_profit"], row["net_profit"], 5)
                eps_cagr_5, _ = compute_cagr(start_row["eps"], row["eps"], 5)

            # 6. Composite Quality Score
            score_components = []
            if roe is not None:
                score_components.append(min(max(roe / 25.0 * 30.0, 0), 30.0))
            if npm is not None:
                score_components.append(min(max(npm / 20.0 * 20.0, 0), 20.0))
            if rev_cagr_5 is not None:
                score_components.append(min(max(rev_cagr_5 / 15.0 * 25.0, 0), 25.0))
            if de is not None:
                de_score = 25.0 if de <= 0.5 else (15.0 if de <= 1.5 else (5.0 if de <= 3.0 else 0.0))
                score_components.append(de_score)

            comp_quality = round(sum(score_components), 2) if len(score_components) >= 2 else None

            records_to_insert.append((
                company_id, yr, npm, opm, roe, de, icr, asset_to,
                fcf, capex, eps, bvps, div_payout, total_debt, cfo,
                rev_cagr_5, pat_cagr_5, eps_cagr_5, comp_quality
            ))

    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO financial_ratios (
        company_id, year, net_profit_margin_pct, operating_profit_margin_pct,
        return_on_equity_pct, debt_to_equity, interest_coverage, asset_turnover,
        free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share,
        dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr,
        revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr, composite_quality_score
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records_to_insert)
    conn.commit()

    logging.info(f"Successfully inserted {len(records_to_insert)} rows into financial_ratios table.")
    return len(records_to_insert)


def main():
    conn = get_db_connection()
    try:
        init_table(conn)
        df_raw = extract_raw_data(conn)
        count = calculate_and_insert_ratios(conn, df_raw)
        print(f"\n[✓] Ingestion Complete. Total Rows Populated: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
