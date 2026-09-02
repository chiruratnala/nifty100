"""
Nifty 100 Composite Quality Score Engine
Module: src/screener/composite.py
Description: Computes a 4-pillar quality score (0-100) using P10/P90 winsorization 
             and sector-relative normalization.
"""

import pandas as pd
import numpy as np


def winsorize_series(s: pd.Series, p_low: float = 0.10, p_high: float = 0.90) -> pd.Series:
    """Winsorizes a numeric series between p_low and p_high quantiles."""
    clean_s = s.dropna()
    if len(clean_s) < 5:
        return s
    q_low = clean_s.quantile(p_low)
    q_high = clean_s.quantile(p_high)
    return s.clip(lower=q_low, upper=q_high)


def min_max_scale(s: pd.Series, ascending: bool = True) -> pd.Series:
    """Scales a series to 0-100 range. If ascending=False, lower values get higher scores."""
    clean_s = s.dropna()
    if len(clean_s) == 0:
        return pd.Series(50.0, index=s.index)
    
    min_val, max_val = clean_s.min(), clean_s.max()
    if min_val == max_val:
        return pd.Series(50.0, index=s.index)
    
    if ascending:
        scaled = ((s - min_val) / (max_val - min_val)) * 100.0
    else:
        scaled = ((max_val - s) / (max_val - min_val)) * 100.0
    return scaled.fillna(50.0)


def compute_composite_quality_scores(df_universe: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a 4-pillar composite quality score (0-100):
      - 35% Profitability: ROE (15%), ROCE (10%), NPM (10%)
      - 30% Cash Quality: FCF CAGR/Growth (15%), CFO/PAT Ratio (10%), Positive FCF flag (5%)
      - 20% Growth: Revenue CAGR 5Y (10%), PAT CAGR 5Y (10%)
      - 15% Leverage: D/E (10% - lower is better), ICR (5%)
    """
    df = df_universe.copy()

    # Derived components
    # 1. ROCE proxy from operating profit & balance sheet or NPM
    if "operating_profit_margin_pct" in df.columns:
        df["roce_proxy"] = df["operating_profit_margin_pct"] * df["asset_turnover"].fillna(1.0)
    else:
        df["roce_proxy"] = df["return_on_equity_pct"]

    # 2. CFO / PAT Ratio
    cfo = pd.to_numeric(df["cash_from_operations_cr"], errors="coerce").fillna(0.0)
    pat = pd.to_numeric(df["net_profit"], errors="coerce").replace(0, np.nan)
    df["cfo_pat_ratio"] = (cfo / pat).clip(-2.0, 5.0).fillna(1.0)

    # 3. FCF positive flag
    fcf = pd.to_numeric(df["free_cash_flow_cr"], errors="coerce").fillna(0.0)
    df["fcf_pos_flag"] = (fcf > 0).astype(float) * 100.0

    # Sector-Relative Winsorized Scoring
    score_cols = {
        "roe_scaled": ("return_on_equity_pct", True),
        "roce_scaled": ("roce_proxy", True),
        "npm_scaled": ("net_profit_margin_pct", True),
        "fcf_scaled": ("free_cash_flow_cr", True),
        "cfo_pat_scaled": ("cfo_pat_ratio", True),
        "rev_cagr_scaled": ("revenue_cagr_5yr", True),
        "pat_cagr_scaled": ("pat_cagr_5yr", True),
        "de_scaled": ("debt_to_equity", False),          # Lower D/E is better
        "icr_scaled": ("interest_coverage", True)
    }

    # Normalize within broad_sector
    for new_col, (orig_col, asc) in score_cols.items():
        if orig_col not in df.columns:
            df[new_col] = 50.0
            continue
            
        numeric_series = pd.to_numeric(df[orig_col], errors="coerce")
        df[new_col] = df.groupby("broad_sector", group_keys=False)[orig_col].apply(
            lambda s: min_max_scale(winsorize_series(pd.to_numeric(s, errors="coerce")), ascending=asc)
        ).fillna(50.0)

    # Calculate Weighted Composite Score
    profitability_pillar = (0.15 * df["roe_scaled"]) + (0.10 * df["roce_scaled"]) + (0.10 * df["npm_scaled"])
    cash_quality_pillar = (0.15 * df["fcf_scaled"]) + (0.10 * df["cfo_pat_scaled"]) + (0.05 * df["fcf_pos_flag"])
    growth_pillar = (0.10 * df["rev_cagr_scaled"]) + (0.10 * df["pat_cagr_scaled"])
    leverage_pillar = (0.10 * df["de_scaled"]) + (0.05 * df["icr_scaled"])

    df["composite_quality_score"] = (
        profitability_pillar + cash_quality_pillar + growth_pillar + leverage_pillar
    ).round(2)

    # Clean intermediate calculation columns
    drop_temp = list(score_cols.keys()) + ["roce_proxy", "cfo_pat_ratio", "fcf_pos_flag"]
    df = df.drop(columns=[c for c in drop_temp if c in df.columns])

    return df.sort_values("composite_quality_score", ascending=False).reset_index(drop=True)
