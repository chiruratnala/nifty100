
import re
import pandas as pd


def normalize_ticker(value):
    """
    Normalize an NSE ticker by stripping whitespace
    and converting it to uppercase.
    """
    if value is None:
        return None

    return str(value).strip().upper()


def normalize_year(value):
    """
    Normalize financial year labels to YYYY-MM.
    """

    if value is None or pd.isna(value):
        return "PARSE_ERROR"

    value = str(value).strip()

    if not value:
        return "PARSE_ERROR"

    # Already normalized: YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", value):
        return value

    # FY23 / FY2023
    match = re.fullmatch(r"FY(\d{2}|\d{4})", value, re.IGNORECASE)

    if match:
        year = match.group(1)

        if len(year) == 2:
            year = "20" + year

        return f"{year}-03"

    # Plain year: 2023 → March FY
    if re.fullmatch(r"\d{4}", value):
        return f"{value}-03"

    # Month + year
    match = re.fullmatch(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"(?:[a-z]*)?"
        r"[-\s]?"
        r"(\d{2}|\d{4})",
        value,
        re.IGNORECASE
    )

    if match:
        month_text = match.group(1).lower()
        year = match.group(2)

        month_map = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "may": "05",
            "jun": "06",
            "jul": "07",
            "aug": "08",
            "sep": "09",
            "oct": "10",
            "nov": "11",
            "dec": "12",
        }

        month = month_map[month_text]

        if len(year) == 2:
            year = "20" + year

        return f"{year}-{month}"

    return "PARSE_ERROR"
