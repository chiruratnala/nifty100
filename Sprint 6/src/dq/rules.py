"""
Institutional Data Quality (DQ) Rule Definitions
Module: src/dq/rules.py
"""

from typing import Any

import pandas as pd

DQ_REGISTRY = [
    {"rule_id": "DQ001", "name": "Missing Company ID", "severity": "CRITICAL"},
    {"rule_id": "DQ002", "name": "Negative Sales Revenue", "severity": "CRITICAL"},
    {"rule_id": "DQ003", "name": "Balance Sheet Imbalance (Assets != Liabilities)", "severity": "CRITICAL"},
    {"rule_id": "DQ004", "name": "OPM Greater Than 100%", "severity": "HIGH"},
    {"rule_id": "DQ005", "name": "NPM Exceeds OPM (Operating Anomaly)", "severity": "HIGH"},
    {"rule_id": "DQ006", "name": "Extreme D/E Ratio (> 25x)", "severity": "HIGH"},
    {"rule_id": "DQ007", "name": "Unnormalized Fiscal Year String", "severity": "MEDIUM"},
    {"rule_id": "DQ008", "name": "Negative Net Worth / Equity Flag", "severity": "HIGH"},
    {"rule_id": "DQ009", "name": "CFO Positive While Sales Negative", "severity": "HIGH"},
    {"rule_id": "DQ010", "name": "Dividend Payout Ratio > 150%", "severity": "MEDIUM"},
    {"rule_id": "DQ011", "name": "Negative Cash Balance", "severity": "CRITICAL"},
    {"rule_id": "DQ012", "name": "Unassigned Sector Taxonomy", "severity": "MEDIUM"},
    {"rule_id": "DQ013", "name": "P/E Negative With Positive Earnings", "severity": "HIGH"},
    {"rule_id": "DQ014", "name": "Duplicate Constituent Period Entry", "severity": "CRITICAL"},
]


def evaluate_dq_rule(rule_id: str, df: pd.DataFrame) -> list[dict[str, Any]]:
    """Execute Evaluate dq rule routine."""
    violations = []

    if rule_id == "DQ001":
        # Missing or empty company_id
        if "company_id" in df.columns:
            bad = df[df["company_id"].isna() | (df["company_id"].astype(str).str.strip() == "")]
            if not bad.empty:
                violations.append({"rule_id": "DQ001", "severity": "CRITICAL", "count": len(bad)})

    elif rule_id == "DQ002":
        # Negative Sales
        if "sales" in df.columns:
            bad = df[pd.to_numeric(df["sales"], errors="coerce") < 0]
            if not bad.empty:
                violations.append({"rule_id": "DQ002", "severity": "CRITICAL", "count": len(bad)})

    elif rule_id == "DQ003":
        # Balance Sheet Imbalance
        if "total_assets" in df.columns and "total_liabilities" in df.columns:
            diff = (
                pd.to_numeric(df["total_assets"], errors="coerce")
                - pd.to_numeric(df["total_liabilities"], errors="coerce")
            ).abs()
            bad = df[diff > 1.0]
            if not bad.empty:
                violations.append({"rule_id": "DQ003", "severity": "CRITICAL", "count": len(bad)})

    elif rule_id == "DQ004":
        # OPM > 100%
        if "opm_pct" in df.columns:
            bad = df[pd.to_numeric(df["opm_pct"], errors="coerce") > 100.0]
            if not bad.empty:
                violations.append({"rule_id": "DQ004", "severity": "HIGH", "count": len(bad)})

    elif rule_id == "DQ005":
        # NPM > OPM
        if "npm_pct" in df.columns and "opm_pct" in df.columns:
            bad = df[pd.to_numeric(df["npm_pct"], errors="coerce") > pd.to_numeric(df["opm_pct"], errors="coerce")]
            if not bad.empty:
                violations.append({"rule_id": "DQ005", "severity": "HIGH", "count": len(bad)})

    elif rule_id == "DQ006":
        # Extreme D/E > 25
        if "debt_to_equity" in df.columns:
            bad = df[pd.to_numeric(df["debt_to_equity"], errors="coerce") > 25.0]
            if not bad.empty:
                violations.append({"rule_id": "DQ006", "severity": "HIGH", "count": len(bad)})

    elif rule_id == "DQ007":
        # Unnormalized Year String
        if "year" in df.columns:
            bad = df[~df["year"].astype(str).str.match(r"^\d{4}(-\d{2})?$")]
            if not bad.empty:
                violations.append({"rule_id": "DQ007", "severity": "MEDIUM", "count": len(bad)})

    elif rule_id == "DQ008":
        # Negative Equity
        if "shareholders_equity" in df.columns:
            bad = df[pd.to_numeric(df["shareholders_equity"], errors="coerce") < 0]
            if not bad.empty:
                violations.append({"rule_id": "DQ008", "severity": "HIGH", "count": len(bad)})

    elif rule_id == "DQ009":
        # CFO > 0 while Sales <= 0
        if "cfo" in df.columns and "sales" in df.columns:
            bad = df[
                (pd.to_numeric(df["cfo"], errors="coerce") > 0) & (pd.to_numeric(df["sales"], errors="coerce") <= 0)
            ]
            if not bad.empty:
                violations.append({"rule_id": "DQ009", "severity": "HIGH", "count": len(bad)})

    elif rule_id == "DQ010":
        # Payout ratio > 150%
        if "dividend_payout_pct" in df.columns:
            bad = df[pd.to_numeric(df["dividend_payout_pct"], errors="coerce") > 150.0]
            if not bad.empty:
                violations.append({"rule_id": "DQ010", "severity": "MEDIUM", "count": len(bad)})

    elif rule_id == "DQ011":
        # Negative Cash
        if "cash_balance" in df.columns:
            bad = df[pd.to_numeric(df["cash_balance"], errors="coerce") < 0]
            if not bad.empty:
                violations.append({"rule_id": "DQ011", "severity": "CRITICAL", "count": len(bad)})

    elif rule_id == "DQ012":
        # Unassigned Sector
        if "sector" in df.columns:
            bad = df[
                df["sector"].isna() | (df["sector"].astype(str).str.lower().isin(["unknown", "unassigned", "", "none"]))
            ]
            if not bad.empty:
                violations.append({"rule_id": "DQ012", "severity": "MEDIUM", "count": len(bad)})

    elif rule_id == "DQ013":
        # Negative P/E with positive EPS
        if "pe_ratio" in df.columns and "eps" in df.columns:
            bad = df[
                (pd.to_numeric(df["pe_ratio"], errors="coerce") < 0) & (pd.to_numeric(df["eps"], errors="coerce") > 0)
            ]
            if not bad.empty:
                violations.append({"rule_id": "DQ013", "severity": "HIGH", "count": len(bad)})

    elif (
        rule_id == "DQ014"
        and "company_id" in df.columns
        and "year" in df.columns
        and not (bad := df[df.duplicated(subset=["company_id", "year"], keep=False)]).empty
    ):
        # Duplicate constituent-period key
        violations.append({"rule_id": "DQ014", "severity": "HIGH", "count": len(bad)})

    return violations
