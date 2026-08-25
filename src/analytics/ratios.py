"""
Nifty 100 Financial Ratio Engine
Module: src/analytics/ratios.py
Includes: Profitability, Leverage, and Efficiency Ratios
"""

import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# --- Day 08: Profitability Ratios ---

def compute_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """Net Profit Margin = (Net Profit / Sales) * 100. Returns None if sales <= 0."""
    if net_profit is None or sales is None or pd.isna(net_profit) or pd.isna(sales) or float(sales) <= 0:
        return None
    return round((float(net_profit) / float(sales)) * 100, 2)


def compute_operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
    source_opm: Optional[float] = None,
    company_id: Optional[str] = None,
    year: Optional[str] = None
) -> Tuple[Optional[float], Optional[str]]:
    """Operating Profit Margin = (Operating Profit / Sales) * 100 with variance cross-check."""
    if operating_profit is None or sales is None or pd.isna(operating_profit) or pd.isna(sales) or float(sales) <= 0:
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
    """Return on Equity = Net Profit / (Equity Capital + Reserves) * 100."""
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
    """Return on Capital Employed with Financials sector carve-out."""
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
    """Return on Assets = (Net Profit / Total Assets) * 100."""
    if net_profit is None or total_assets is None or pd.isna(net_profit) or pd.isna(total_assets):
        return None

    t_assets = float(total_assets)
    if t_assets <= 0:
        return None

    return round((float(net_profit) / t_assets) * 100, 2)


# --- Day 09: Leverage & Efficiency Ratios ---

def compute_debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    broad_sector: Optional[str] = None
) -> Tuple[Optional[float], bool]:
    """
    Debt-to-Equity = Borrowings / (Equity Capital + Reserves)
    - Returns 0.0 if borrowings == 0 (not None).
    - Returns (None, False) if total equity <= 0.
    - Sets high_leverage_flag = True if D/E > 5.0 and broad_sector != 'Financials'.
    """
    if equity_capital is None or reserves is None or pd.isna(equity_capital) or pd.isna(reserves):
        return None, False

    total_equity = float(equity_capital) + float(reserves)
    if total_equity <= 0:
        return None, False

    b = float(borrowings) if borrowings is not None and not pd.isna(borrowings) else 0.0
    if b == 0:
        return 0.0, False

    de_ratio = round(b / total_equity, 2)
    high_leverage = (de_ratio > 5.0) and (broad_sector != "Financials")

    return de_ratio, high_leverage


def compute_interest_coverage(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Interest Coverage Ratio = (Operating Profit + Other Income) / Interest
    - If interest == 0 or null: returns (None, "Debt Free", False).
    - If ICR < 1.5: sets icr_warning_flag = True (solvency risk).
    """
    if operating_profit is None or pd.isna(operating_profit):
        return None, None, False

    ebit = float(operating_profit) + (float(other_income) if other_income is not None and not pd.isna(other_income) else 0.0)

    if interest is None or pd.isna(interest) or float(interest) <= 0:
        return None, "Debt Free", False

    interest_val = float(interest)
    icr = round(ebit / interest_val, 2)
    warning_flag = icr < 1.5
    label = "Normal" if icr >= 1.5 else "Solvency Risk"

    return icr, label, warning_flag


def compute_net_debt(borrowings: Optional[float], investments: Optional[float]) -> float:
    """Net Debt = Borrowings - Investments (Proxy for cash/liquid investments)."""
    b = float(borrowings) if borrowings is not None and not pd.isna(borrowings) else 0.0
    inv = float(investments) if investments is not None and not pd.isna(investments) else 0.0
    return round(b - inv, 2)


def compute_asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Asset Turnover = Sales / Total Assets. Returns None if total_assets <= 0."""
    if sales is None or total_assets is None or pd.isna(sales) or pd.isna(total_assets):
        return None

    t_assets = float(total_assets)
    if t_assets <= 0:
        return None

    return round(float(sales) / t_assets, 2)
