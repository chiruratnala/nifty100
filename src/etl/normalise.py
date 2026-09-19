"""
Year Normalization Utility
Module: src/etl/normalise.py
"""

import re


def normalize_year(val: str | float | None) -> str | None:
    """
    Normalizes diverse financial year inputs into canonical 'YYYY' or 'YYYY-MM' format.
    Handles: '2023', 2023, 'FY23', 'FY2023', 'Mar 23', 'March 2023', '2023-03', '31-03-2023', etc.
    Returns None for invalid, NaN, or non-parseable inputs.
    """
    if val is None:
        return None

    # Handle floats / NaNs
    if isinstance(val, float):
        if str(val) == "nan":
            return None
        val = int(val)

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "-", ""):
        return None

    # Pattern: Full date YYYY-MM or YYYY-MM-DD
    m_iso = re.match(r"^(\d{4})[-/](0[1-9]|1[0-2])", s)
    if m_iso:
        return f"{m_iso.group(1)}-{m_iso.group(2)}"

    # Pattern: DD-MM-YYYY or DD/MM/YYYY
    m_dmy = re.match(r"^\d{1,2}[-/](\d{1,2})[-/](\d{4})$", s)
    if m_dmy:
        year = m_dmy.group(2)
        month = m_dmy.group(1).zfill(2)
        return f"{year}-{month}"

    # Pattern: FY2023 or FY23 or FY 2023 or FY-24
    m_fy = re.search(r"fy\s*[-_]?\s*(\d{2,4})", s, re.IGNORECASE)
    if m_fy:
        digits = m_fy.group(1)
        if len(digits) == 2:
            return f"20{digits}"
        return digits

    # Pattern: 'Mar 2023' or 'March 2023' or 'Mar-23' or 'Mar-2023'
    m_month_yr = re.search(
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-/\s]+(\d{2,4})", s, re.IGNORECASE
    )
    if m_month_yr:
        digits = m_month_yr.group(1)
        if len(digits) == 2:
            return f"20{digits}"
        return digits

    # Pattern: Plain 4-digit year (19xx or 20xx)
    m_4d = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if m_4d:
        return m_4d.group(1)

    # Pattern: '23 or '24 with apostrophe
    m_apos = re.match(r"^'(\d{2})$", s)
    if m_apos:
        return f"20{m_apos.group(1)}"

    return None
