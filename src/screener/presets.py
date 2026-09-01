"""
Nifty 100 Preset Investment Screeners
Module: src/screener/presets.py
Description: Encapsulates the 6 standard screener presets with dynamic edge-case handling.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.screener.engine import apply_filter_criteria, load_screener_config


def get_preset_definitions(config_path: str = "config/screener_config.yaml") -> Dict[str, Any]:
    """Retrieves preset filter specifications from YAML config."""
    config = load_screener_config(config_path)
    return config.get("presets", {})


def run_quality_compounder(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 1: Quality Compounder
    Criteria: ROE > 15%, D/E < 1.0 (ex-Financials), FCF > 0, Revenue CAGR 5Y > 10%
    """
    filters = config.get("quality_compounder", {}).get("filters", {
        "return_on_equity_pct_min": 15.0,
        "debt_to_equity_max": 1.0,
        "free_cash_flow_cr_min": 0.0,
        "revenue_cagr_5yr_min": 10.0
    })
    return apply_filter_criteria(df, filters)


def run_value_pick(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 2: Value Pick
    Criteria: P/E < 20, P/B < 3.0, D/E < 2.0 (ex-Financials), Dividend Yield > 1%
    """
    filters = config.get("value_pick", {}).get("filters", {
        "pe_ratio_max": 20.0,
        "pb_ratio_max": 3.0,
        "debt_to_equity_max": 2.0,
        "dividend_yield_pct_min": 1.0
    })
    return apply_filter_criteria(df, filters)


def run_growth_accelerator(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 3: Growth Accelerator
    Criteria: PAT CAGR 5Y > 20%, Revenue CAGR 5Y > 15%, D/E < 2.0 (ex-Financials)
    """
    filters = config.get("growth_accelerator", {}).get("filters", {
        "pat_cagr_5yr_min": 20.0,
        "revenue_cagr_5yr_min": 15.0,
        "debt_to_equity_max": 2.0
    })
    return apply_filter_criteria(df, filters)


def run_dividend_champion(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 4: Dividend Champion
    Criteria: Dividend Yield > 2%, Dividend Payout < 80%, FCF > 0
    """
    filters = config.get("dividend_champion", {}).get("filters", {
        "dividend_yield_pct_min": 2.0,
        "dividend_payout_ratio_pct_max": 80.0,
        "free_cash_flow_cr_min": 0.0
    })
    return apply_filter_criteria(df, filters)


def run_debt_free_blue_chip(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 5: Debt-Free Blue Chip
    Criteria: D/E <= 0.05, ROE > 12%, Sales > 5,000 Cr
    """
    filters = config.get("debt_free_blue_chip", {}).get("filters", {
        "debt_to_equity_max": 0.05,
        "return_on_equity_pct_min": 12.0,
        "sales_min": 5000.0
    })
    return apply_filter_criteria(df, filters)


def run_turnaround_watch(df_all_years: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preset 6: Turnaround Watch
    Criteria: FCF positive in latest year, D/E declining YoY, Revenue CAGR >= 10% (or positive growth)
    """
    # Group by company to compute YoY D/E change
    df_sorted = df_all_years.sort_values(["company_id", "year"]).reset_index(drop=True)
    df_sorted["de_prev"] = df_sorted.groupby("company_id")["debt_to_equity"].shift(1)
    df_sorted["de_declining"] = df_sorted["debt_to_equity"] < df_sorted["de_prev"]
    
    # Extract latest year per company
    df_latest = df_sorted.groupby("company_id").last().reset_index()
    
    # Filter conditions: FCF > 0, declining D/E (or debt free), positive revenue compounding
    mask = (
        (df_latest["free_cash_flow_cr"] > 0) &
        ((df_latest["de_declining"] == True) | (df_latest["debt_to_equity"] <= 0.05)) &
        (df_latest["revenue_cagr_5yr"].fillna(10.0) >= 8.0)
    )
    
    df_turnaround = df_latest[mask].sort_values("composite_quality_score", ascending=False).reset_index(drop=True)
    return df_turnaround
