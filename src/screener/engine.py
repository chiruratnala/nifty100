"""
Nifty 100 Quantitative Screener Engine
Module: src/screener/engine.py
Description: Dynamic threshold filtering, YAML config parsing, and financial ratio screening.
"""

import os
import yaml
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


def load_screener_config(config_path: str = "config/screener_config.yaml") -> Dict[str, Any]:
    """Loads screener YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_screener_universe(conn: sqlite3.Connection, latest_only: bool = True) -> pd.DataFrame:
    """
    Extracts complete financial ratios joined with company master metadata, 
    sectors, and statement attributes using validated schema columns.
    """
    query = """
    SELECT 
        f.company_id,
        f.year,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.index_weight_pct,
        s.market_cap_category,
        p.sales,
        p.operating_profit,
        p.net_profit,
        f.net_profit_margin_pct,
        f.operating_profit_margin_pct,
        f.return_on_equity_pct,
        f.debt_to_equity,
        f.interest_coverage,
        f.asset_turnover,
        f.free_cash_flow_cr,
        f.capex_cr,
        f.earnings_per_share,
        f.book_value_per_share,
        f.dividend_payout_ratio_pct,
        f.total_debt_cr,
        f.cash_from_operations_cr,
        f.revenue_cagr_5yr,
        f.pat_cagr_5yr,
        f.eps_cagr_5yr,
        f.composite_quality_score,
        -- Valuation proxies derived from fundamentals
        (p.sales * 2.5) AS market_cap,
        CASE WHEN f.earnings_per_share > 0 THEN f.earnings_per_share * 22.0 ELSE 100.0 END AS current_market_price,
        22.0 AS pe_ratio,
        CASE 
            WHEN f.book_value_per_share > 0 THEN (f.earnings_per_share * 22.0) / f.book_value_per_share 
            ELSE 2.5 
        END AS pb_ratio,
        CASE 
            WHEN f.dividend_payout_ratio_pct > 0 THEN (f.dividend_payout_ratio_pct / 100.0 * f.earnings_per_share) / (f.earnings_per_share * 22.0) * 100.0 
            ELSE 1.2 
        END AS dividend_yield_pct
    FROM financial_ratios f
    LEFT JOIN companies c ON f.company_id = c.id
    LEFT JOIN sectors s ON f.company_id = s.company_id
    LEFT JOIN profitandloss p ON f.company_id = p.company_id AND f.year = p.year
    LEFT JOIN balancesheet b ON f.company_id = b.company_id AND f.year = b.year
    ORDER BY f.company_id, f.year ASC;
    """
    df = pd.read_sql_query(query, conn)
    
    if latest_only and not df.empty:
        df = df.sort_values("year").groupby("company_id").last().reset_index()
        
    return df


def apply_filter_criteria(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Applies 15 filterable metrics with bank leverage carve-out and debt-free ICR conversion.
    """
    df_filtered = df.copy()

    # Normalize ICR: Debt Free or None -> np.inf
    if "interest_coverage" in df_filtered.columns:
        df_filtered["icr_numeric"] = pd.to_numeric(df_filtered["interest_coverage"], errors="coerce")
        df_filtered["icr_numeric"] = df_filtered["icr_numeric"].fillna(np.inf)

    for key, threshold in filters.items():
        if threshold is None or pd.isna(threshold):
            continue

        # 1. ROE Min
        if key == "return_on_equity_pct_min":
            df_filtered = df_filtered[df_filtered["return_on_equity_pct"] >= float(threshold)]

        # 2. D/E Max (Automatically skips Financials broad sector)
        elif key == "debt_to_equity_max":
            is_financials = df_filtered["broad_sector"] == "Financials"
            meets_de = df_filtered["debt_to_equity"] <= float(threshold)
            df_filtered = df_filtered[is_financials | meets_de]

        # 3. Free Cash Flow Min
        elif key == "free_cash_flow_cr_min":
            df_filtered = df_filtered[df_filtered["free_cash_flow_cr"] >= float(threshold)]

        # 4. Revenue CAGR 5Y Min
        elif key == "revenue_cagr_5yr_min":
            df_filtered = df_filtered[df_filtered["revenue_cagr_5yr"] >= float(threshold)]

        # 5. PAT CAGR 5Y Min
        elif key == "pat_cagr_5yr_min":
            df_filtered = df_filtered[df_filtered["pat_cagr_5yr"] >= float(threshold)]

        # 6. OPM Min
        elif key == "operating_profit_margin_pct_min":
            df_filtered = df_filtered[df_filtered["operating_profit_margin_pct"] >= float(threshold)]

        # 7. P/E Max
        elif key == "pe_ratio_max":
            df_filtered = df_filtered[(df_filtered["pe_ratio"].notna()) & (df_filtered["pe_ratio"] <= float(threshold))]

        # 8. P/B Max
        elif key == "pb_ratio_max":
            df_filtered = df_filtered[(df_filtered["pb_ratio"].notna()) & (df_filtered["pb_ratio"] <= float(threshold))]

        # 9. Dividend Yield Min
        elif key == "dividend_yield_pct_min":
            df_filtered = df_filtered[(df_filtered["dividend_yield_pct"].notna()) & (df_filtered["dividend_yield_pct"] >= float(threshold))]

        # 10. ICR Min (Debt free companies with np.inf always pass)
        elif key == "interest_coverage_min":
            df_filtered = df_filtered[df_filtered["icr_numeric"] >= float(threshold)]

        # 11. Market Cap Min
        elif key == "market_cap_min":
            df_filtered = df_filtered[df_filtered["market_cap"] >= float(threshold)]

        # 12. Net Profit Min
        elif key == "net_profit_min":
            df_filtered = df_filtered[df_filtered["net_profit"] >= float(threshold)]

        # 13. EPS CAGR 5Y Min
        elif key == "eps_cagr_5yr_min":
            df_filtered = df_filtered[df_filtered["eps_cagr_5yr"] >= float(threshold)]

        # 14. Asset Turnover Min
        elif key == "asset_turnover_min":
            df_filtered = df_filtered[df_filtered["asset_turnover"] >= float(threshold)]

        # 15. Sales Min
        elif key == "sales_min":
            df_filtered = df_filtered[df_filtered["sales"] >= float(threshold)]

        # Payout ratio max (for Dividend Champion)
        elif key == "dividend_payout_ratio_pct_max":
            df_filtered = df_filtered[df_filtered["dividend_payout_ratio_pct"] <= float(threshold)]

    if "icr_numeric" in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=["icr_numeric"])

    return df_filtered.sort_values("composite_quality_score", ascending=False).reset_index(drop=True)
