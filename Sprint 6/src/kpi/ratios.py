"""
KPI & Financial Ratio Formulas
Module: src/kpi/ratios.py
"""


def compute_roe(net_income: float, shareholders_equity: float) -> float | None:
    """
    Computes Return on Equity (ROE %).
    Guardrail: If shareholders' equity <= 0, standard ROE is economically distorted/meaningless -> return None.
    """
    if shareholders_equity is None or net_income is None:
        return None
    if shareholders_equity <= 0:
        return None
    return round((net_income / shareholders_equity) * 100.0, 2)


def compute_debt_to_equity(total_debt: float, shareholders_equity: float) -> float | None:
    """
    Computes Debt-to-Equity.
    Debt-free company (total_debt == 0) returns 0.0.
    Negative equity returns None.
    """
    if total_debt is None or shareholders_equity is None:
        return None
    if total_debt == 0.0:
        return 0.0
    if shareholders_equity <= 0:
        return None
    return round(total_debt / shareholders_equity, 2)


def compute_interest_coverage(ebit: float, interest_expense: float) -> float | None:
    """
    Computes ICR = EBIT / Interest.
    Guardrail: When interest expense == 0 (zero debt/interest), return None.
    """
    if ebit is None or interest_expense is None:
        return None
    if interest_expense == 0.0:
        return None
    return round(ebit / interest_expense, 2)


def check_leverage_flag(debt_to_equity: float | None, broad_sector: str) -> bool:
    """
    Flags companies with D/E > 5 for non-financial companies.
    Financials/Banks/NBFCs legitimately operate at 6x-12x and are exempt.
    """
    if debt_to_equity is None:
        return False
    is_financial = any(k in broad_sector.lower() for k in ["financial", "bank", "nbfc", "lending"])
    return bool(not is_financial and debt_to_equity > 5.0)


def compute_cagr(start_val: float, end_val: float, periods: int) -> tuple[float | None, str | None]:
    """
    Computes Compound Annual Growth Rate (CAGR %) with cycle turnaround flags.
    - Normal positive growth: (end/start)**(1/n) - 1
    - Turnaround: start < 0 and end > 0 -> returns None, flag="TURNAROUND"
    - Decline-to-loss: start > 0 and end < 0 -> returns None, flag="DECLINE_TO_LOSS"
    - Persistent loss: start < 0 and end < 0 -> returns None, flag="CHRONIC_LOSS"
    """
    if start_val is None or end_val is None or periods <= 0:
        return None, "INVALID_INPUT"

    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"
    if start_val <= 0 and end_val <= 0:
        return None, "CHRONIC_LOSS"
    if start_val == 0:
        return None, "ZERO_BASE"

    cagr = ((end_val / start_val) ** (1.0 / periods) - 1.0) * 100.0
    return round(cagr, 2), "NORMAL"


def check_opm_crosscheck(opm_pct: float, sales: float, operating_profit: float, tolerance: float = 1.0) -> bool:
    """
    Cross-checks whether reported OPM diverges from operating_profit / sales by > tolerance %.
    Returns True if divergence flag raised.
    """
    if sales <= 0:
        return False
    calc_opm = (operating_profit / sales) * 100.0
    diff = abs(opm_pct - calc_opm)
    return diff > tolerance


def compute_cfo_quality_score(cfo: float, operating_profit: float, net_profit: float) -> float:
    """
    Calculates CFO Quality Score (0 to 100):
    Evaluates cash conversion against operating and net income.
    Score components:
    - CFO / PAT > 1.0 (50 pts)
    - CFO / EBITDA > 0.7 (50 pts)
    """
    score = 0.0
    if net_profit > 0 and cfo > 0:
        cfo_to_pat = cfo / net_profit
        if cfo_to_pat >= 1.0:
            score += 50.0
        elif cfo_to_pat > 0:
            score += round(cfo_to_pat * 50.0, 2)

    if operating_profit > 0 and cfo > 0:
        cfo_to_ebitda = cfo / operating_profit
        if cfo_to_ebitda >= 0.7:
            score += 50.0
        elif cfo_to_ebitda > 0:
            score += round((cfo_to_ebitda / 0.7) * 50.0, 2)

    return min(100.0, round(score, 2))
