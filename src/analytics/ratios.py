"""
Nifty 100 Financial Ratio Engine - Profitability Ratios
Module: src/analytics/ratios.py
"""

import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def compute_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Net Profit Margin = (Net Profit / Sales) * 100
    Returns None if sales <= 0 or if values are null.
    """
    if net_profit is None or sales is None or pd.isna(net_profit) or pd.isna(sales) or sales <= 0:
        return None
    return round((float(net_profit) / float(sales)) * 100, 2)


def compute_operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
    source_opm: Optional[float] = None,
    company_id: Optional[str] = None,
    year: Optional[str] = None
) -> Tuple[Optional[float], Optional[str]]:
    """
    Operating Profit Margin = (Operating Profit / Sales) * 100
    Cross-checks with source_opm; logs a warning if difference > 1.0%.
    """
    if operating_profit is None or sales is None or pd.isna(operating_profit) or pd.isna(sales) or sales <= 0:
        return None, None

    computed_opm = round((float(operating_profit) / float(sales)) * 100, 2)
    warning = None

    if source_opm is not None and not pd.isna(source_opm):
        diff = round(abs(computed_opm - float(source_opm)), 2)
        if diff > 1.0:
            warning = f"OPM Mismatch for {company_id} [{year}]: computed={computed_opm}%, source={source_opm}%, diff={diff}%"
            logging.warning(warning)

    return computed_opm, warning


def compute_roe(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float]
) -> Optional[float]:
    """
    Return on Equity = Net Profit / (Equity Capital + Reserves) * 100
    Returns None if total equity <= 0 or if values are null.
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    if pd.isna(net_profit) or pd.isna(equity_capital) or pd.isna(reserves):
        return None

    total_equity = float(equity_capital) + float(reserves)
    if total_equity <= 0:
        return None

    return round((float(net_profit) / total_equity) * 100, 2)


def compute_roce(
    operating_profit: Optional[float],
    other_income: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    broad_sector: Optional[str] = None
) -> Dict[str, Any]:
    """
    Return on Capital Employed = EBIT / (Equity Capital + Reserves + Borrowings) * 100
    EBIT = operating_profit + (other_income or 0)
    Handles Financials broad_sector carve-out.
    """
    is_financial = (broad_sector == "Financials")

    if operating_profit is None or equity_capital is None or reserves is None:
        return {"roce_pct": None, "is_financial_sector": is_financial}
    if pd.isna(operating_profit) or pd.isna(equity_capital) or pd.isna(reserves):
        return {"roce_pct": None, "is_financial_sector": is_financial}

    ebit = float(operating_profit) + (float(other_income) if other_income is not None and not pd.isna(other_income) else 0.0)
    total_borrowings = float(borrowings) if borrowings is not None and not pd.isna(borrowings) else 0.0
    capital_employed = float(equity_capital) + float(reserves) + total_borrowings

    if capital_employed <= 0:
        return {"roce_pct": None, "is_financial_sector": is_financial}

    roce_val = round((ebit / capital_employed) * 100, 2)
    return {
        "roce_pct": roce_val,
        "is_financial_sector": is_financial
    }


def compute_roa(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Return on Assets = (Net Profit / Total Assets) * 100
    Returns None if total_assets <= 0 or if values are null.
    """
    if net_profit is None or total_assets is None or pd.isna(net_profit) or pd.isna(total_assets):
        return None

    t_assets = float(total_assets)
    if t_assets <= 0:
        return None

    return round((float(net_profit) / t_assets) * 100, 2)
