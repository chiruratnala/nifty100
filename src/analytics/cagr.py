"""
Nifty 100 Financial Ratio Engine - Compound Annual Growth Rate (CAGR)
Module: src/analytics/cagr.py
"""

import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Allowed CAGR classification flags
FLAG_NORMAL = "NORMAL"
FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


def compute_cagr(start_val: Optional[float], end_val: Optional[float], periods: int) -> Tuple[Optional[float], str]:
    """
    Computes CAGR over `periods` years and classifies all 6 edge-case states:
      1. Normal: start > 0 and end > 0 -> returns (computed_cagr, "NORMAL")
      2. Decline to Loss: start > 0 and end < 0 -> returns (None, "DECLINE_TO_LOSS")
      3. Turnaround: start < 0 and end > 0 -> returns (None, "TURNAROUND")
      4. Both Negative: start < 0 and end < 0 -> returns (None, "BOTH_NEGATIVE")
      5. Zero Base: start == 0 -> returns (None, "ZERO_BASE")
      6. Insufficient/Invalid: periods <= 0 or missing values -> returns (None, "INSUFFICIENT")
    """
    if periods is None or periods <= 0:
        return None, FLAG_INSUFFICIENT

    if start_val is None or end_val is None or pd.isna(start_val) or pd.isna(end_val):
        return None, FLAG_INSUFFICIENT

    start_v = float(start_val)
    end_v = float(end_val)

    # Edge Case: Zero Base
    if start_v == 0.0:
        return None, FLAG_ZERO_BASE

    # Edge Case: Positive to Negative (Decline to Loss)
    if start_v > 0.0 and end_v < 0.0:
        return None, FLAG_DECLINE_TO_LOSS

    # Edge Case: Negative to Positive (Turnaround)
    if start_v < 0.0 and end_v > 0.0:
        return None, FLAG_TURNAROUND

    # Edge Case: Both Negative
    if start_v < 0.0 and end_v < 0.0:
        return None, FLAG_BOTH_NEGATIVE

    # Edge Case: Positive to Zero (100% decline)
    if start_v > 0.0 and end_v == 0.0:
        return -100.0, FLAG_NORMAL

    # Normal Compounding Calculation (Both positive)
    try:
        cagr_val = round(((end_v / start_v) ** (1.0 / periods) - 1.0) * 100.0, 2)
        return cagr_val, FLAG_NORMAL
    except Exception as exc:
        logging.error(f"CAGR calculation exception: {exc}")
        return None, FLAG_INSUFFICIENT


def calculate_series_cagr(
    series_df: pd.DataFrame,
    metric_col: str,
    periods: int,
    year_col: str = "year"
) -> Tuple[Optional[float], str]:
    """
    Computes CAGR for `metric_col` from the latest available year back `periods` years.
    Returns (cagr_val, cagr_flag).
    """
    if series_df is None or series_df.empty or metric_col not in series_df.columns:
        return None, FLAG_INSUFFICIENT

    clean_df = series_df.dropna(subset=[metric_col, year_col]).sort_values(year_col)

    if len(clean_df) < (periods + 1):
        return None, FLAG_INSUFFICIENT

    start_val = clean_df.iloc[-(periods + 1)][metric_col]
    end_val = clean_df.iloc[-1][metric_col]

    return compute_cagr(start_val, end_val, periods)


def compute_company_cagrs(company_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes 3Y, 5Y, and 10Y CAGRs for sales, net_profit, and eps.
    Returns dictionary formatted for financial_ratios table.
    """
    windows = [3, 5, 10]
    metrics = {
        "revenue": "sales",
        "pat": "net_profit",
        "eps": "eps"
    }

    result = {}
    for metric_label, col_name in metrics.items():
        for w in windows:
            cagr_val, flag = calculate_series_cagr(company_df, col_name, w)
            result[f"{metric_label}_cagr_{w}yr"] = cagr_val
            result[f"{metric_label}_cagr_{w}yr_flag"] = flag

    return result
