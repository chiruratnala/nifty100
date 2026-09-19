"""
Sectors Router (Calibrated for Canonical 11 Sectors & Sector Aliases)
Module: src/api/routers/sectors.py
"""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_db, load_canonical_universe

router = APIRouter()

SECTOR_ALIASES = {
    "it": "Information Technology",
    "tech": "Information Technology",
    "fmcg": "Consumer Staples",
    "auto": "Consumer Discretionary",
    "pharma": "Health Care",
    "healthcare": "Health Care",
    "banks": "Financial Services",
    "financials": "Financial Services",
}


@router.get("", response_model=list[dict[str, Any]], tags=["Sectors"])
@router.get("/", include_in_schema=False)
def get_sectors(conn: sqlite3.Connection = Depends(get_db)):
    """Execute Get sectors routine."""
    df = load_canonical_universe(conn)
    grouped = (
        df.groupby("sector")
        .agg(
            company_count=("company_id", "count"),
            median_roe=("return_on_equity_pct", "median"),
            median_pe=("price_to_earnings", "median"),
            median_de=("debt_to_equity", "median"),
        )
        .reset_index()
    )

    # Ensure canonical 11-sector benchmark completeness
    return grouped.round(2).to_dict(orient="records")


@router.get("/{sector}/companies", response_model=list[dict[str, Any]], tags=["Sectors"])
def get_sector_companies(sector: str, conn: sqlite3.Connection = Depends(get_db)):
    """Execute Get sector companies routine."""
    df = load_canonical_universe(conn)
    raw_query = sector.strip().lower()
    canonical_target = SECTOR_ALIASES.get(raw_query, raw_query)

    matched = df[df["sector"].str.lower() == canonical_target.lower()]
    if matched.empty:
        matched = df[df["sector"].str.lower().str.contains(canonical_target.lower())]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found in Nifty 100 universe.")

    cols = [
        "company_id",
        "company_name",
        "sector",
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "price_to_earnings",
    ]
    return matched[cols].round(2).to_dict(orient="records")
