"""
Health Diagnostic Router
Module: src/api/routers/health.py
"""

import os
import sqlite3
import time
from typing import Any

from fastapi import APIRouter, Depends

router = APIRouter()
START_TIME = time.time()
API_VERSION = "1.0.0"


def get_db():
    """Execute Get db routine."""
    candidates = ["/content/nifty100.db", "data/nifty100.db", "nifty100.db"]
    db_path = None
    for c in candidates:
        if os.path.exists(c):
            db_path = c
            break
    if not db_path:
        for root, _, files in os.walk("."):
            if "nifty100.db" in files:
                db_path = os.path.join(root, "nifty100.db")
                break

    conn = sqlite3.connect(db_path if db_path else "nifty100.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@router.get("", response_model=dict[str, Any], tags=["System Health"])
@router.get("/", include_in_schema=False)
def get_health(conn: sqlite3.Connection = Depends(get_db)):
    """
    Returns system status, active version, uptime, and row counts across all database tables.
    """
    uptime_sec = round(time.time() - START_TIME, 2)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    db_counts = {}
    for tbl in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            db_counts[tbl] = cursor.fetchone()[0]
        except Exception:
            db_counts[tbl] = 0

    return {
        "status": "ok",
        "version": API_VERSION,
        "uptime_seconds": uptime_sec,
        "table_count": len(tables),
        "db_row_counts": db_counts,
    }
