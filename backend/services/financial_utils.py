"""
Financial utility functions shared across services.
"""
from datetime import date


def calculate_proportional_period_amount(
    amount: float,
    period_start: date,
    period_end: date,
    range_start: date,
    range_end: date,
) -> float:
    """
    Calculate proportional amount for a transaction that spans a period,
    within a given date range.

    For example, if a transaction covers 30 days and only 10 of them fall
    within the range, return amount * (10/30).
    """
    total_days = (period_end - period_start).days + 1
    if total_days <= 0:
        return 0.0

    overlap_start = max(period_start, range_start)
    overlap_end = min(period_end, range_end)
    overlap_days = (overlap_end - overlap_start).days + 1

    if overlap_days <= 0:
        return 0.0

    return amount * (overlap_days / total_days)


def determine_profit_status_color(profit: float, budget: float = 0.0) -> str:
    """
    Return a color string based on profit status.
    green = profitable, yellow = breakeven, red = loss.
    """
    if profit > 0:
        return "green"
    elif profit == 0:
        return "yellow"
    else:
        return "red"
