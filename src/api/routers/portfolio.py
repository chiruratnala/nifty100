"""
Portfolio Analytics Router
Module: src/api/routers/portfolio.py
"""

import os
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/stats", response_model=list[dict[str, Any]], tags=["Portfolio"])
def get_portfolio_stats():
    """Execute Get portfolio stats routine."""
    csv_path = "output/portfolio_stats.csv"
    if not os.path.exists(csv_path):
        from src.analytics.cluster_profiling import main as gen_stats

        gen_stats()

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=500, detail="Portfolio statistics file not found.")

    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")
