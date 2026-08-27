"""
Nifty 100 Financial Ratio Engine - Cash Flow KPIs & Capital Allocation Classifier
Module: src/analytics/cashflow.py
"""

import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def compute_fcf(cfo: Optional[float], cfi: Optional[float]) -> Optional[float]:
    """Free Cash Flow = CFO + CFI (negative value allowed)."""
    if cfo is None or pd.isna(cfo):
        return None
    cfi_val = float(cfi) if cfi is not None and not pd.isna(cfi) else 0.0
    return round(float(cfo) + cfi_val, 2)


def compute_capex_intensity(cfi: Optional[float], sales: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
    """
    CapEx Intensity = (abs(CFI) / Sales) * 100
    - < 3%: 'Asset Light'
    - 3-8%: 'Moderate'
    - > 8%: 'Capital Intensive'
    """
    if cfi is None or sales is None or pd.isna(cfi) or pd.isna(sales) or float(sales) <= 0:
        return None, None

    intensity = round((abs(float(cfi)) / float(sales)) * 100, 2)

    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf_conversion(fcf: Optional[float], operating_profit: Optional[float]) -> Optional[float]:
    """
    FCF Conversion Rate = (FCF / Operating Profit) * 100
    Returns None if operating_profit <= 0 or null.
    """
    if fcf is None or operating_profit is None or pd.isna(fcf) or pd.isna(operating_profit):
        return None
    if float(operating_profit) <= 0:
        return None
    return round((float(fcf) / float(operating_profit)) * 100, 2)


def compute_5yr_cfo_quality(company_df: pd.DataFrame) -> Tuple[Optional[float], Optional[str]]:
    """
    CFO Quality Score = 5-year sum(CFO) / 5-year sum(PAT)
    - > 1.0: 'High Quality'
    - 0.5 - 1.0: 'Moderate'
    - < 0.5: 'Accrual Risk'
    """
    clean_df = company_df.dropna(subset=["cfo", "pat"]).sort_values("year")
    if len(clean_df) < 3:
        return None, None

    subset = clean_df if len(clean_df) < 5 else clean_df.iloc[-5:]

    sum_cfo = subset["cfo"].sum()
    sum_pat = subset["pat"].sum()

    if sum_pat <= 0:
        return None, "Accrual Risk"

    quality_score = round(sum_cfo / sum_pat, 2)

    if quality_score > 1.0:
        label = "High Quality"
    elif quality_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return quality_score, label


def classify_capital_allocation_pattern(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_quality: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classifies 8-pattern capital allocation based on signs of (CFO, CFI, CFF).
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    if cfo is None or cfi is None or cff is None or pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return ("?", "?", "?", "Insufficient Data")

    s_cfo = "+" if float(cfo) >= 0 else "-"
    s_cfi = "+" if float(cfi) >= 0 else "-"
    s_cff = "+" if float(cff) >= 0 else "-"

    sign_tuple = (s_cfo, s_cfi, s_cff)

    if sign_tuple == ("+", "-", "-"):
        if cfo_quality is not None and cfo_quality > 1.2:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif sign_tuple == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif sign_tuple == ("-", "+", "+"):
        label = "Distress Signal"
    elif sign_tuple == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif sign_tuple == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif sign_tuple == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif sign_tuple == ("+", "-", "+"):
        label = "Mixed"
    else:  # ("-", "+", "-")
        label = "Distress / Asset Sale"

    return s_cfo, s_cfi, s_cff, label
