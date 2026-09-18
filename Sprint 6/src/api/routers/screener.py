"""
Screener Router
Module: src/api/routers/screener.py
"""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_db, load_canonical_universe

router = APIRouter()


@router.get("", response_model=list[dict[str, Any]], tags=["Screener"])
@router.get("/", include_in_schema=False)
def screen_companies(
    min_roe: float | None = Query(None, description="Minimum ROE (%)"),
    max_de: float | None = Query(None, description="Maximum Debt-to-Equity ratio"),
    min_fcf: float | None = Query(None, description="Minimum 5Y FCF CAGR (%)"),
    sector: str | None = Query(None, description="Sector filter"),
    min_rev_cagr_5yr: float | None = Query(None, description="Minimum 5Y Revenue CAGR (%)"),
    min_pat_cagr_5yr: float | None = Query(None, description="Minimum 5Y PAT CAGR (%)"),
    max_pe: float | None = Query(None, description="Maximum P/E multiple"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute Screen companies routine with multi-factor criteria."""
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative.")
    if max_pe is not None and max_pe <= 0:
        raise HTTPException(status_code=400, detail="max_pe must be strictly positive.")
    if min_roe is not None and min_roe < -100:
        raise HTTPException(status_code=400, detail="min_roe cannot be less than -100%.")

    df = load_canonical_universe(conn)

    if sector:
        df = df[df["sector"].str.lower() == sector.strip().lower()]
    if min_roe is not None:
        df = df[df["return_on_equity_pct"] >= min_roe]
    if max_de is not None:
        df = df[df["debt_to_equity"] <= max_de]
    if min_fcf is not None:
        df = df[df["fcf_cagr_5yr"] >= min_fcf]
    if min_rev_cagr_5yr is not None:
        df = df[df["revenue_cagr_5yr"] >= min_rev_cagr_5yr]
    if min_pat_cagr_5yr is not None:
        df = df[df["net_profit_cagr_5yr"] >= min_pat_cagr_5yr]
    if max_pe is not None:
        df = df[df["price_to_earnings"] <= max_pe]

    if df.empty:
        return []

    df = df.copy()
    df["score"] = df["return_on_equity_pct"] / (df["debt_to_equity"].clip(lower=0) + 0.1)
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    result_cols = [
        "rank",
        "company_id",
        "company_name",
        "sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "fcf_cagr_5yr",
        "revenue_cagr_5yr",
        "net_profit_cagr_5yr",
        "price_to_earnings",
    ]
    return df[result_cols].round(2).to_dict(orient="records")
