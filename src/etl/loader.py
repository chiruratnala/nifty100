import pandas as pd
from src.etl.normaliser import normalize_ticker, normalize_year
CORE_FILES = ["companies.xlsx","profitandloss.xlsx","balancesheet.xlsx","cashflow.xlsx","analysis.xlsx", "documents.xlsx","prosandcons.xlsx",]
def load_excel(file_path, header=1):
    """
    Load an Excel file and apply basic ETL normalization.
    Core Bluestock Excel files use header=1.
    """
    df = pd.read_excel(file_path, header=header)
    # Clean column names
    df.columns = df.columns.astype(str).str.strip()
    # Normalize company_id when present
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)
   # Normalize year when present
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
    return df
def load_core_files():
    """
    Load all 7 core Excel files.

    Returns:
        dict: filename -> DataFrame
    """
    data = {}
    for file_name in CORE_FILES:
        data[file_name] = load_excel(file_name, header=1)
    return data
