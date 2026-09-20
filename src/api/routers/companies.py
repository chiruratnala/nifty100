"""
Companies Router
Module: src/api/routers/companies.py
"""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from fastapi import HTTPException
from src.api.deps import fetch_company_row, find_col, get_db
from src.api.routers.peers import calculate_radar_dict
from src.reports.tearsheet import build_tearsheet
router = APIRouter()


def query_financial_table(
    conn: sqlite3.Connection,
    table_name: str,
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
    single_year: str | None = None,
) -> list[dict[str, Any]]:
    """Execute Query financial table routine for historical statements."""
    fetch_company_row(conn, ticker)

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    cols = [r["name"] for r in cursor.fetchall()]
    cid_col = find_col(cols, ["company_id", "id", "ticker"]) or "company_id"
    yr_col = find_col(cols, ["year", "fiscal_year", "period"])

    conditions = [f"UPPER(TRIM({cid_col})) = UPPER(TRIM(?))"]
    params = [ticker]

    if yr_col:
        if single_year:
            conditions.append(f"{yr_col} = ?")
            params.append(single_year)
        if from_year:
            conditions.append(f"{yr_col} >= ?")
            params.append(from_year)
        if to_year:
            conditions.append(f"{yr_col} <= ?")
            params.append(to_year)

    query_str = f"SELECT * FROM {table_name} WHERE {' AND '.join(conditions)}"
    if yr_col:
        query_str += f" ORDER BY {yr_col} ASC;"
    else:
        query_str += ";"

    cursor.execute(query_str, params)
    return [dict(row) for row in cursor.fetchall()]


@router.get("", response_model=list[dict[str, Any]], tags=["Companies"])
@router.get("/", include_in_schema=False)
def list_companies(
    sector: str | None = Query(None, description="Filter by broad_sector or sector"),
    market_cap: str | None = Query(None, description="Filter by market cap category"),
    search: str | None = Query(None, description="Search term matching id or company_name"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute List companies routine across the universe."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(companies);")
    cols = [r["name"] for r in cursor.fetchall()]

    sec_c = find_col(cols, ["broad_sector", "sector"])
    mc_c = find_col(cols, ["market_cap_category", "cap_category"])
    cid_c = find_col(cols, ["id", "company_id", "ticker"]) or "id"
    name_c = find_col(cols, ["company_name", "name"]) or cid_c

    conditions = []
    params = []

    if sector and sec_c:
        conditions.append(f"LOWER({sec_c}) = LOWER(?)")
        params.append(sector.strip())
    if market_cap and mc_c:
        conditions.append(f"LOWER({mc_c}) = LOWER(?)")
        params.append(market_cap.strip())
    if search:
        conditions.append(f"(LOWER({cid_c}) LIKE LOWER(?) OR LOWER({name_c}) LIKE LOWER(?))")
        params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])

    sql = "SELECT * FROM companies"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += f" ORDER BY {cid_c} ASC;"

    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


@router.get("/{ticker}", response_model=dict[str, Any], tags=["Companies"])
def get_company(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Execute Get company profile and latest KPIs routine."""
    comp_row = fetch_company_row(conn, ticker)
    comp_dict = dict(comp_row)

    ratios = query_financial_table(conn, "financial_ratios", ticker)
    latest_ratios = ratios[-1] if ratios else {}

    return {
        "company_profile": comp_dict,
        "latest_year_kpis": latest_ratios,
        "total_historical_years": len(ratios),
    }


@router.get("/{ticker}/pl", response_model=list[dict[str, Any]], tags=["Companies"])
def get_company_profit_loss(
    ticker: str,
    from_year: str | None = Query(None, description="Start year"),
    to_year: str | None = Query(None, description="End year"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute Get company profit loss statements routine."""
    return query_financial_table(conn, "profitandloss", ticker, from_year=from_year, to_year=to_year)


@router.get("/{ticker}/bs", response_model=list[dict[str, Any]], tags=["Companies"])
def get_company_balance_sheet(
    ticker: str,
    from_year: str | None = Query(None, description="Start year"),
    to_year: str | None = Query(None, description="End year"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute Get company balance sheet statements routine."""
    return query_financial_table(conn, "balancesheet", ticker, from_year=from_year, to_year=to_year)


@router.get("/{ticker}/cashflow", response_model=list[dict[str, Any]], tags=["Companies"])
def get_company_cashflow(
    ticker: str,
    from_year: str | None = Query(None, description="Start year"),
    to_year: str | None = Query(None, description="End year"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute Get company cash flow statements routine."""
    return query_financial_table(conn, "cashflow", ticker, from_year=from_year, to_year=to_year)


@router.get("/{ticker}/ratios", response_model=list[dict[str, Any]], tags=["Companies"])
def get_company_ratios(
    ticker: str,
    year: str | None = Query(None, description="Single fiscal year"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Execute Get company ratios routine."""
    return query_financial_table(conn, "financial_ratios", ticker, single_year=year)

@router.get(
    "/{ticker}/tearsheet",
    tags=["Companies"],
    summary="Download Company Tearsheet",
)
def download_company_tearsheet(
    ticker: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Generate and return the company's institutional tearsheet PDF."""

    # Validate that the company exists
    fetch_company_row(conn, ticker)

    output_dir = "reports/tearsheets"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir,
        f"{ticker.strip().upper()}_tearsheet.pdf",
    )

    build_tearsheet(ticker.strip().upper(), output_path)

    if not os.path.exists(output_path):
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate tearsheet for '{ticker}'.",
        )

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=os.path.basename(output_path),
    )

@router.get(
    "/{ticker}/peers/compare",
    response_model=dict[str, Any],
    tags=["Companies"],
    summary="Get Company Peer Radar",
)
def get_company_peer_radar(
    ticker: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Return peer comparison radar metrics for a company."""

    return calculate_radar_dict(ticker, conn)