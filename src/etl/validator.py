
import re
from urllib.parse import urlparse

import pandas as pd


class Validator:

    def __init__(self, data):
        self.data = data
        self.failures = []

    def add_failure(
        self,
        rule_id,
        severity,
        file_name,
        company_id=None,
        year=None,
        message=""
    ):
        self.failures.append({
            "rule_id": rule_id,
            "severity": severity,
            "file_name": file_name,
            "company_id": company_id,
            "year": year,
            "message": message
        })


    # --------------------------------------------------
    # DQ-01 — Company PK Uniqueness
    # --------------------------------------------------

    def validate_dq01_company_pk(self):

        df = self.data["companies.xlsx"]

        duplicates = df[df["id"].duplicated(keep=False)]

        for _, row in duplicates.iterrows():

            self.add_failure(
                rule_id="DQ-01",
                severity="CRITICAL",
                file_name="companies.xlsx",
                company_id=row["id"],
                message="Duplicate company ID"
            )


    # --------------------------------------------------
    # DQ-02 — Annual PK Uniqueness
    # --------------------------------------------------

    def validate_dq02_annual_pk(self):

        for file_name in [
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx"
        ]:

            df = self.data[file_name]

            duplicates = df[
                df.duplicated(
                    subset=["company_id", "year"],
                    keep=False
                )
            ]

            for _, row in duplicates.iterrows():

                self.add_failure(
                    rule_id="DQ-02",
                    severity="CRITICAL",
                    file_name=file_name,
                    company_id=row["company_id"],
                    year=row["year"],
                    message="Duplicate company-year record"
                )


    # --------------------------------------------------
    # DQ-03 — Foreign Key Integrity
    # --------------------------------------------------

    def validate_dq03_fk_integrity(self):

        companies = self.data["companies.xlsx"]

        valid_ids = set(
            companies["id"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
        )

        child_files = [
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx",
            "analysis.xlsx",
            "documents.xlsx",
            "prosandcons.xlsx"
        ]

        for file_name in child_files:

            df = self.data[file_name]

            for _, row in df.iterrows():

                company_id = (
                    str(row["company_id"])
                    .strip()
                    .upper()
                )

                if company_id not in valid_ids:

                    self.add_failure(
                        rule_id="DQ-03",
                        severity="CRITICAL",
                        file_name=file_name,
                        company_id=company_id,
                        year=row.get(
                            "year",
                            row.get("Year")
                        ),
                        message=(
                            "Company ID not found "
                            "in companies table"
                        )
                    )


    # --------------------------------------------------
    # DQ-04 — Balance Sheet Balance
    # --------------------------------------------------

    def validate_dq04_balance_sheet(self):

        df = self.data["balancesheet.xlsx"].copy()

        denominator = df["total_assets"].replace(
            0,
            pd.NA
        )

        difference = (
            abs(
                df["total_assets"]
                - df["total_liabilities"]
            )
            / denominator
        )

        violations = df[
            difference >= 0.01
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                rule_id="DQ-04",
                severity="WARNING",
                file_name="balancesheet.xlsx",
                company_id=row["company_id"],
                year=row["year"],
                message=(
                    "Balance sheet difference "
                    "is >= 1%"
                )
            )


    # ==================================================
    # DQ-05 — OPM Cross-Check
    # ==================================================

    def validate_dq05_opm(self):

        df = self.data["profitandloss.xlsx"].copy()

        valid_sales = df["sales"] != 0

        computed_opm = (
            df["operating_profit"]
            / df["sales"]
            * 100
        )

        difference = abs(
            df["opm_percentage"]
            - computed_opm
        )

        violations = df[
            valid_sales & (difference >= 1.0)
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                "DQ-05",
                "WARNING",
                "profitandloss.xlsx",
                row["company_id"],
                row["year"],
                "OPM differs from computed OPM by >= 1 percentage point"
            )


    # ==================================================
    # DQ-06 — Positive Sales
    # ==================================================

    def validate_dq06_positive_sales(self):

        df = self.data["profitandloss.xlsx"]

        bank_tickers = {
            "AXISBANK",
            "BAJAJHLDNG",
            "BAJFINANCE",
            "BANKBARODA",
            "CANBK",
            "CHOLAFIN",
            "HDFCBANK",
            "ICICIBANK",
            "INDUSINDBK",
            "KOTAKBANK",
            "PNB",
            "SBIN",
            "SHRIRAMFIN",
            "UNIONBANK"
        }

        for _, row in df.iterrows():

            company_id = (
                str(row["company_id"])
                .strip()
                .upper()
            )

            if (
                company_id not in bank_tickers
                and row["sales"] <= 0
            ):

                self.add_failure(
                    "DQ-06",
                    "WARNING",
                    "profitandloss.xlsx",
                    company_id,
                    row["year"],
                    "Non-bank company has sales <= 0"
                )


    # ==================================================
    # DQ-07 — Year Format
    # ==================================================

    def validate_dq07_year_format(self):

        pattern = re.compile(
            r"^\d{4}-(0[1-9]|1[0-2])$"
        )

        for file_name in [
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx"
        ]:

            df = self.data[file_name]

            for _, row in df.iterrows():

                year = str(row["year"])

                if not pattern.fullmatch(year):

                    self.add_failure(
                        "DQ-07",
                        "CRITICAL",
                        file_name,
                        row["company_id"],
                        year,
                        "Invalid year format"
                    )


    # ==================================================
    # DQ-08 — Ticker Format
    # ==================================================

    def validate_dq08_ticker_format(self):

        pattern = re.compile(
            r"^[A-Z0-9&-]{2,12}$"
        )

        for file_name in [
            "companies.xlsx",
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx",
            "analysis.xlsx",
            "documents.xlsx",
            "prosandcons.xlsx"
        ]:

            df = self.data[file_name]

            column = (
                "id"
                if file_name == "companies.xlsx"
                else "company_id"
            )

            for _, row in df.iterrows():

                ticker = (
                    str(row[column])
                    .strip()
                    .upper()
                )

                if not pattern.fullmatch(ticker):

                    self.add_failure(
                        "DQ-08",
                        "CRITICAL",
                        file_name,
                        ticker,
                        row.get("year", row.get("Year")),
                        "Invalid ticker format"
                    )


    # ==================================================
    # DQ-09 — Net Cash Flow
    # ==================================================

    def validate_dq09_cashflow(self):

        df = self.data["cashflow.xlsx"]

        computed = (
            df["operating_activity"]
            + df["investing_activity"]
            + df["financing_activity"]
        )

        difference = abs(
            df["net_cash_flow"] - computed
        )

        violations = df[
            difference > 10
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                "DQ-09",
                "WARNING",
                "cashflow.xlsx",
                row["company_id"],
                row["year"],
                "Net cash flow differs from components by > 10"
            )


    # ==================================================
    # DQ-10 — Fixed Assets
    # ==================================================

    def validate_dq10_fixed_assets(self):

        df = self.data["balancesheet.xlsx"]

        violations = df[
            df["fixed_assets"] < 0
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                "DQ-10",
                "WARNING",
                "balancesheet.xlsx",
                row["company_id"],
                row["year"],
                "Negative fixed assets"
            )


    # ==================================================
    # DQ-11 — Tax Rate
    # ==================================================

    def validate_dq11_tax_rate(self):

        df = self.data["profitandloss.xlsx"]

        violations = df[
            (df["tax_percentage"] < 0)
            | (df["tax_percentage"] > 60)
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                "DQ-11",
                "WARNING",
                "profitandloss.xlsx",
                row["company_id"],
                row["year"],
                "Tax percentage outside 0-60% range"
            )


    # ==================================================
    # DQ-12 — Dividend Payout
    # ==================================================

    def validate_dq12_dividend_payout(self):

        df = self.data["profitandloss.xlsx"]

        violations = df[
            df["dividend_payout"] > 200
        ]

        for _, row in violations.iterrows():

            self.add_failure(
                "DQ-12",
                "WARNING",
                "profitandloss.xlsx",
                row["company_id"],
                row["year"],
                "Dividend payout exceeds 200%"
            )


    # ==================================================
    # DQ-13 — Annual Report URL
    # ==================================================

    def validate_dq13_urls(self):

        df = self.data["documents.xlsx"]

        for _, row in df.iterrows():

            value = row["Annual_Report"]

            if pd.isna(value):
                continue

            value = str(value).strip()

            # Treat source missing markers as missing,
            # not malformed URLs.
            if value.lower() in {
                "null",
                "none",
                "nan",
                ""
            }:
                continue

            try:

                parsed = urlparse(value)

                valid = (
                    parsed.scheme in {"http", "https"}
                    and bool(parsed.netloc)
                )

            except Exception:

                valid = False

            if not valid:

                self.add_failure(
                    "DQ-13",
                    "WARNING",
                    "documents.xlsx",
                    row["company_id"],
                    row["Year"],
                    "Malformed annual report URL"
                )


    # ==================================================
    # DQ-14 — EPS Sign Consistency
    # ==================================================

    def validate_dq14_eps_sign(self):

        df = self.data["profitandloss.xlsx"]

        for _, row in df.iterrows():

            net_profit = row["net_profit"]
            eps = row["eps"]

            if (
                pd.notna(net_profit)
                and pd.notna(eps)
                and net_profit != 0
                and eps != 0
            ):

                mismatch = (
                    (net_profit > 0 and eps < 0)
                    or
                    (net_profit < 0 and eps > 0)
                )

                if mismatch:

                    self.add_failure(
                        "DQ-14",
                        "WARNING",
                        "profitandloss.xlsx",
                        row["company_id"],
                        row["year"],
                        "EPS sign inconsistent with net profit"
                    )


    # ==================================================
    # DQ-15 — Strict Balance Check
    # ==================================================

    def validate_dq15_balance(self):

        df = self.data["balancesheet.xlsx"]

        mismatches = df[
            df["total_liabilities"]
            != df["total_assets"]
        ]

        for _, row in mismatches.iterrows():

            self.add_failure(
                "DQ-15",
                "INFO",
                "balancesheet.xlsx",
                row["company_id"],
                row["year"],
                "Total liabilities does not strictly equal total assets"
            )


    # ==================================================
    # DQ-16 — Minimum Coverage
    # ==================================================

    def validate_dq16_coverage(self):

        for file_name in [
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx"
        ]:

            df = self.data[file_name]

            coverage = (
                df.groupby("company_id")["year"]
                .nunique()
            )

            violations = coverage[
                coverage < 5
            ]

            for company_id, years in violations.items():

                self.add_failure(
                    "DQ-16",
                    "WARNING",
                    file_name,
                    company_id,
                    None,
                    f"Only {years} years of coverage"
                )


    # ==================================================
    # RUN ALL DQ RULES
    # ==================================================

    def run_all(self):

        self.validate_dq01_company_pk()
        self.validate_dq02_annual_pk()
        self.validate_dq03_fk_integrity()
        self.validate_dq04_balance_sheet()
        self.validate_dq05_opm()
        self.validate_dq06_positive_sales()
        self.validate_dq07_year_format()
        self.validate_dq08_ticker_format()
        self.validate_dq09_cashflow()
        self.validate_dq10_fixed_assets()
        self.validate_dq11_tax_rate()
        self.validate_dq12_dividend_payout()
        self.validate_dq13_urls()
        self.validate_dq14_eps_sign()
        self.validate_dq15_balance()
        self.validate_dq16_coverage()

        return pd.DataFrame(self.failures)
