import os
import sqlite3
import re
import pandas as pd
import numpy as np
from src.etl.normaliser import normalize_ticker, normalize_year

DB_PATH = "data/nifty100.db"
CORE_FILES = [
    "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx",
    "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx"
]

def load_excel(file_path: str, header: int = 1) -> pd.DataFrame:
    """Load an Excel file and apply basic ETL normalization."""
    # Resolve file path across standard locations
    resolved_path = file_path
    if not os.path.exists(resolved_path):
        for candidate in [f"data/raw/{file_path}", f"data/supporting/{file_path}", f"data/{file_path}"]:
            if os.path.exists(candidate):
                resolved_path = candidate
                break

    df = pd.read_excel(resolved_path, header=header)
    df.columns = df.columns.astype(str).str.strip()

    # Normalize primary and foreign keys
    if "id" in df.columns and "companies" in file_path:
        df["id"] = df["id"].apply(normalize_ticker)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)
        df["company_id"] = df["company_id"].replace({"AGTL": "ATGL"})

    # Normalize year labels
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
    elif "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

    return df

def load_core_files() -> dict:
    """Load all 7 core Excel files into a dictionary of DataFrames."""
    data = {}
    for file_name in CORE_FILES:
        data[file_name] = load_excel(file_name, header=1)
    return data

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

    # 1. Companies Master Table
    comp_file = "data/raw/companies.xlsx" if os.path.exists("data/raw/companies.xlsx") else "companies.xlsx"
    df_comp = load_excel(comp_file, header=1)
    df_comp["id"] = df_comp["id"].apply(normalize_ticker)
    df_comp = df_comp.dropna(subset=["id"]).drop_duplicates(subset=["id"], keep="last")
    if "face_value" in df_comp.columns:
        df_comp["face_value"] = pd.to_numeric(df_comp["face_value"], errors="coerce").fillna(1.0)

    comp_cols = [c for c in get_table_cols("companies") if c in df_comp.columns]
    df_comp[comp_cols].to_sql("companies", conn, if_exists="append", index=False)
    valid_tickers = set(df_comp["id"])
    print(f"companies      : Loaded {len(df_comp)} records.")

    def clean_child(df, key_cols, yr_col="year"):
        df.columns = df.columns.astype(str).str.strip().str.replace(" ", "_")
        if "company_id" not in df.columns:
            if "id" in df.columns:
                df["company_id"] = df["id"]
            elif "ticker" in df.columns:
                df["company_id"] = df["ticker"]

        df["company_id"] = df["company_id"].apply(normalize_ticker)
        df["company_id"] = df["company_id"].replace({"AGTL": "ATGL"})

        if yr_col in df.columns and yr_col == "year":
            df["year"] = df["year"].apply(normalize_year)
            df = df[df["year"] != "PARSE_ERROR"]
        elif yr_col in df.columns and yr_col == "Year":
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

        df = df[df["company_id"].isin(valid_tickers)]
        if key_cols:
            df = df.drop_duplicates(subset=key_cols, keep="last")
        return df

    # 2. Core Child Datasets
    core_configs = [
        ("profitandloss.xlsx", "profitandloss", ["company_id", "year"], "year"),
        ("balancesheet.xlsx", "balancesheet", ["company_id", "year"], "year"),
        ("cashflow.xlsx", "cashflow", ["company_id", "year"], "year"),
        ("analysis.xlsx", "analysis", ["company_id"], None),
        ("documents.xlsx", "documents", ["company_id", "Year"], "Year"),
        ("prosandcons.xlsx", "prosandcons", None, None),
    ]

    for file, table, keys, yr_col in core_configs:
        file_path = f"data/raw/{file}" if os.path.exists(f"data/raw/{file}") else file
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, header=1)
            df = clean_child(df, keys, yr_col)
            target_cols = [c for c in get_table_cols(table) if c in df.columns]
            df[target_cols].to_sql(table, conn, if_exists="append", index=False)
            print(f"{table:15}: Loaded {len(df)} records.")

    # 3. Supplementary Datasets
    supp_configs = [
        ("sectors.xlsx", "sectors", ["company_id"]),
        ("stock_prices.xlsx", "stock_prices", ["company_id", "date"]),
        ("market_cap.xlsx", "market_cap", ["company_id", "year"]),
    ]

    for file, table, keys in supp_configs:
        file_path = f"data/supporting/{file}" if os.path.exists(f"data/supporting/{file}") else (f"data/{file}" if os.path.exists(f"data/{file}") else file)
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, header=0)
            df = clean_child(df, keys, None)
            target_cols = [c for c in get_table_cols(table) if c in df.columns]
            df[target_cols].to_sql(table, conn, if_exists="append", index=False)
            print(f"{table:15}: Loaded {len(df)} records.")

    conn.close()
    print("\nDatabase build complete: data/nifty100.db")

if __name__ == "__main__":
    prepare_and_load_db()