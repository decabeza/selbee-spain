"""
SELBEE SPAIN - Prize Sharing Engine

Estimates the expected fraction of a shared prize pool
received by one winning entry.
"""

import math


def expected_share_fraction(
    win_probability: float,
    other_entries: int,
) -> float:
    """
    Calculate the expected share of a prize pool,
    conditional on our entry winning.

    Assumptions:
    - Other entries are independent.
    - All entries have the same win probability.
    - The prize pool is shared equally among winners.
    """

    if not 0 < win_probability <= 1:
        raise ValueError("Win probability must be greater than 0 and at most 1")

    if not isinstance(other_entries, int) or isinstance(other_entries, bool):
        raise TypeError("Other entries must be an integer")

    if other_entries < 0:
        raise ValueError("Other entries cannot be negative")

    if win_probability == 1:
        return 1.0 / (other_entries + 1)

    total_entries = other_entries + 1

    numerator = -math.expm1(
        total_entries * math.log1p(-win_probability)
    )

    return numerator / (total_entries * win_probability)


def expected_shared_prize(
    prize_pool: float,
    win_probability: float,
    other_entries: int,
) -> float:
    """
    Calculate expected gross payout conditional on winning.
    """

    if not math.isfinite(prize_pool) or prize_pool < 0:
        raise ValueError("Prize pool must be finite and non-negative")

    share = expected_share_fraction(
        win_probability=win_probability,
        other_entries=other_entries,
    )

    return prize_pool * share
