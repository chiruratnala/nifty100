from src.etl.loader import load_excel
def test_companies_loader():
    df = load_excel("data/companies.xlsx")
    assert len(df) == 92
    assert len(df.columns) == 12
    assert df["id"].nunique() == 92
    assert df["id"].isna().sum() == 0
def test_profitandloss_loader():
    df = load_excel("data/profitandloss.xlsx")
    assert len(df) == 1276
    assert len(df.columns) == 15
    assert df["company_id"].isna().sum() == 0
def test_balancesheet_loader():
    df = load_excel("data/balancesheet.xlsx")
    assert len(df) == 1312
    assert len(df.columns) == 13
    assert df["company_id"].isna().sum() == 0
def test_cashflow_loader():
    df = load_excel("data/cashflow.xlsx")
    assert len(df) == 1187
    assert len(df.columns) == 7
    assert df["company_id"].isna().sum() == 0
def test_analysis_loader():
    df = load_excel("data/analysis.xlsx")
    assert len(df) == 20
    assert len(df.columns) == 6
def test_documents_loader():
    df = load_excel("data/documents.xlsx")
    assert len(df) == 1585
    assert len(df.columns) == 4
def test_prosandcons_loader():
    df = load_excel("data/prosandcons.xlsx")
    assert len(df) == 16
    assert len(df.columns) == 4
