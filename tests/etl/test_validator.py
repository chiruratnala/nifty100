
import pandas as pd

from src.etl.validator import Validator


def test_dq01_company_pk():
    data = {
        "companies.xlsx": pd.DataFrame({
            "id": ["TCS", "TCS", "INFY"]
        })
    }

    validator = Validator(data)

    validator.validate_dq01_company_pk()

    assert len(validator.failures) == 2
    assert all(
        f["rule_id"] == "DQ-01"
        for f in validator.failures
    )


def test_dq02_annual_pk():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "TCS", "INFY"],
            "year": ["2024-03", "2024-03", "2024-03"]
        }),
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        }),
        "cashflow.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        })
    }

    validator = Validator(data)

    validator.validate_dq02_annual_pk()

    assert len(validator.failures) == 2
    assert all(
        f["rule_id"] == "DQ-02"
        for f in validator.failures
    )


def test_dq04_balance_sheet():
    data = {
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "total_assets": [1000, 1000],
            "total_liabilities": [1000, 1100]
        })
    }

    validator = Validator(data)

    validator.validate_dq04_balance_sheet()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-04"


def test_dq05_opm():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "sales": [1000, 1000],
            "operating_profit": [200, 500],
            "opm_percentage": [20, 20]
        })
    }

    validator = Validator(data)

    validator.validate_dq05_opm()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-05"


def test_dq06_positive_sales():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "sales": [1000, 0]
        })
    }

    validator = Validator(data)

    validator.validate_dq06_positive_sales()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-06"


def test_dq07_year_format():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "PARSE_ERROR"]
        }),
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        }),
        "cashflow.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        })
    }

    validator = Validator(data)

    validator.validate_dq07_year_format()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-07"


def test_dq08_ticker_format():
    data = {
        "companies.xlsx": pd.DataFrame({
            "id": ["TCS", "invalid ticker!"]
        }),
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        }),
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        }),
        "cashflow.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        }),
        "analysis.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        }),
        "documents.xlsx": pd.DataFrame({
            "company_id": [],
            "Year": []
        }),
        "prosandcons.xlsx": pd.DataFrame({
            "company_id": [],
            "year": []
        })
    }

    validator = Validator(data)

    validator.validate_dq08_ticker_format()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-08"


def test_dq09_cashflow():
    data = {
        "cashflow.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "operating_activity": [100, 100],
            "investing_activity": [-50, -50],
            "financing_activity": [-20, -20],
            "net_cash_flow": [30, 50]
        })
    }

    validator = Validator(data)

    validator.validate_dq09_cashflow()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-09"


def test_dq10_fixed_assets():
    data = {
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "fixed_assets": [1000, -100]
        })
    }

    validator = Validator(data)

    validator.validate_dq10_fixed_assets()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-10"


def test_dq11_tax_rate():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "tax_percentage": [25, 75]
        })
    }

    validator = Validator(data)

    validator.validate_dq11_tax_rate()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-11"


def test_dq12_dividend_payout():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "dividend_payout": [50, 250]
        })
    }

    validator = Validator(data)

    validator.validate_dq12_dividend_payout()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-12"


def test_dq13_urls():
    data = {
        "documents.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "Year": [2024, 2024],
            "Annual_Report": [
                "https://example.com/report.pdf",
                "not-a-url"
            ]
        })
    }

    validator = Validator(data)

    validator.validate_dq13_urls()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-13"


def test_dq14_eps_sign():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "net_profit": [100, -100],
            "eps": [10, 10]
        })
    }

    validator = Validator(data)

    validator.validate_dq14_eps_sign()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-14"


def test_dq15_balance():
    data = {
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS", "INFY"],
            "year": ["2024-03", "2024-03"],
            "total_assets": [1000, 1000],
            "total_liabilities": [1000, 999]
        })
    }

    validator = Validator(data)

    validator.validate_dq15_balance()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-15"


def test_dq16_coverage():
    data = {
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "TCS", "TCS"],
            "year": ["2022-03", "2023-03", "2024-03"]
        }),
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        }),
        "cashflow.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        })
    }

    validator = Validator(data)

    validator.validate_dq16_coverage()

    assert len(validator.failures) == 3
    assert all(
        f["rule_id"] == "DQ-16"
        for f in validator.failures
    )



def test_dq03_fk_integrity():
    data = {
        "companies.xlsx": pd.DataFrame({
            "id": ["TCS", "INFY"]
        }),
        "profitandloss.xlsx": pd.DataFrame({
            "company_id": ["TCS", "UNKNOWN"],
            "year": ["2024-03", "2024-03"]
        }),
        "balancesheet.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        }),
        "cashflow.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024-03"]
        }),
        "analysis.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024"]
        }),
        "documents.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "Year": [2024]
        }),
        "prosandcons.xlsx": pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2024"]
        })
    }

    validator = Validator(data)

    validator.validate_dq03_fk_integrity()

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-03"
    assert validator.failures[0]["company_id"] == "UNKNOWN"
