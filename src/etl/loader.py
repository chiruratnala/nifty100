import os
import sqlite3
import re
import pandas as pd
import numpy as np

DB_PATH = "data/nifty100.db"

def normalize_ticker(val):
    if val is None or pd.isna(val):
        return None
    return str(val).strip().upper()

def normalize_year(value):
    if value is None or pd.isna(value):
        return "PARSE_ERROR"
    val = str(value).strip()
    if not val:
        return "PARSE_ERROR"
    if re.fullmatch(r"\d{4}-\d{2}", val):
        return val
    match = re.fullmatch(r"FY(\d{2}|\d{4})", val, re.IGNORECASE)
    if match:
        yr = match.group(1)
        return f"20{yr}-03" if len(yr) == 2 else f"{yr}-03"
    if re.fullmatch(r"\d{4}", val):
        return f"{val}-03"
    match = re.fullmatch(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:[a-z]*)?[-\s]?(\d{2}|\d{4})",
        val,
        re.IGNORECASE
    )
    if match:
        m_map = {
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "may": "05", "jun": "06", "jul": "07", "aug": "08",
            "sep": "09", "oct": "10", "nov": "11", "dec": "12"
        }
        m_num = m_map[match.group(1).lower()]
        yr = match.group(2)
        return f"20{yr}-{m_num}" if len(yr) == 2 else f"{yr}-{m_num}"
    return "PARSE_ERROR"

def load_excel(file_path: str, header: int = 1) -> pd.DataFrame:
    """Load an Excel file and apply basic ETL normalization."""
    resolved_path = file_path
    if not os.path.exists(resolved_path):
        for candidate in [f"data/raw/{file_path}", f"data/supporting/{file_path}", f"data/{file_path}"]:
            if os.path.exists(candidate):
                resolved_path = candidate
                break

    df = pd.read_excel(resolved_path, header=header)
    df.columns = df.columns.astype(str).str.strip()

    if "id" in df.columns and "companies" in file_path:
        df["id"] = df["id"].apply(normalize_ticker)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)
        df["company_id"] = df["company_id"].replace({"AGTL": "ATGL"})

    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
    elif "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

    return df

def load_core_files() -> dict:
    """Load all 7 core Excel files into a dictionary of DataFrames."""
    core_files = [
        "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx",
        "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx"
    ]
    return {f: load_excel(f, header=1) for f in core_files}

def prepare_and_load_db(db_path: str = DB_PATH):
    """Initializes SQLite schema and loads all 10 cleaned datasets."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_file = "src/etl/schema.sql"
    if os.path.exists(schema_file):
        with open(schema_file, "r") as f:
            conn.executescript(f.read())

    def get_table_cols(tbl):
        cur = conn.execute(f"PRAGMA table_info({tbl});")
        return [row[1] for row in cur.fetchall() if row[1] != "id" or tbl in ["companies", "profitandloss", "balancesheet", "cashflow", "analysis", "documents"]]

    def resolve_file(file_name):
        candidates = [file_name, f"data/{file_name}", f"data/raw/{file_name}", f"data/supporting/{file_name}"]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    # 1. Master Companies Table
    comp_path = resolve_file("companies.xlsx")
    df_comp = pd.read_excel(comp_path, header=1)
    df_comp.columns = df_comp.columns.astype(str).str.strip()
    df_comp["id"] = df_comp["id"].apply(normalize_ticker)
    df_comp = df_comp.dropna(subset=["id"]).drop_duplicates(subset=["id"], keep="last")
    if "face_value" in df_comp.columns:
        df_comp["face_value"] = pd.to_numeric(df_comp["face_value"], errors="coerce").fillna(1.0)

    comp_cols = [c for c in get_table_cols("companies") if c in df_comp.columns]
    df_comp[comp_cols].to_sql("companies", conn, if_exists="append", index=False)
    valid_tickers = set(df_comp["id"])
    print(f"[✓] companies     : {len(df_comp)} records loaded.")

    # 2. Child Table Cleaner (drops parse errors before deduplication)
    def clean_child(df, key_cols, yr_col="year"):
        df.columns = df.columns.astype(str).str.strip().str.replace(" ", "_")
        if "company_id" not in df.columns:
            if "id" in df.columns:
                df["company_id"] = df["id"]
            elif "ticker" in df.columns:
                df["company_id"] = df["ticker"]

        df["company_id"] = df["company_id"].apply(normalize_ticker)
        df["company_id"] = df["company_id"].replace({"AGTL": "ATGL"})

        # Normalize year and filter errors FIRST
        if yr_col in df.columns and yr_col == "year":
            df["year"] = df["year"].apply(normalize_year)
            df = df[df["year"] != "PARSE_ERROR"]
        elif yr_col in df.columns and yr_col == "Year":
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

        df = df[df["company_id"].isin(valid_tickers)]
        if key_cols:
            df = df.drop_duplicates(subset=key_cols, keep="last")
        return df

    # Core Datasets
    core_configs = [
        ("profitandloss.xlsx", "profitandloss", ["company_id", "year"], "year"),
        ("balancesheet.xlsx", "balancesheet", ["company_id", "year"], "year"),
        ("cashflow.xlsx", "cashflow", ["company_id", "year"], "year"),
        ("analysis.xlsx", "analysis", ["company_id"], None),
        ("documents.xlsx", "documents", ["company_id", "Year"], "Year"),
        ("prosandcons.xlsx", "prosandcons", None, None),
    ]

    for file, table, keys, yr_col in core_configs:
        file_path = resolve_file(file)
        if file_path:
            df = pd.read_excel(file_path, header=1)
            df = clean_child(df, keys, yr_col)
            target_cols = [c for c in get_table_cols(table) if c in df.columns]
            df[target_cols].to_sql(table, conn, if_exists="append", index=False)
            print(f"[✓] {table:<14}: {len(df)} records loaded.")

    # Supplementary Datasets
    supp_configs = [
        ("sectors.xlsx", "sectors", ["company_id"]),
        ("stock_prices.xlsx", "stock_prices", ["company_id", "date"]),
        ("market_cap.xlsx", "market_cap", ["company_id", "year"]),
    ]

    for file, table, keys in supp_configs:
        file_path = resolve_file(file)
        if file_path:
            df = pd.read_excel(file_path, header=0)
            df = clean_child(df, keys, None)
            target_cols = [c for c in get_table_cols(table) if c in df.columns]
            df[target_cols].to_sql(table, conn, if_exists="append", index=False)
            print(f"[✓] {table:<14}: {len(df)} records loaded.")

    conn.close()
    print("\nDatabase build complete: data/nifty100.db")

if __name__ == "__main__":
    prepare_and_load_db()
