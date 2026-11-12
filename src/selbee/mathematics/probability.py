"""
SELBEE SPAIN - Probability Engine

Core mathematical functions for lottery and betting analysis.
"""

from math import comb, isclose
from typing import Sequence


def combinations(n: int, k: int) -> int:
    """
    Calculate the number of combinations of k elements from n elements.

    Order does not matter and elements cannot be repeated.
    """
    if n < 0 or k < 0 or k > n:
        raise ValueError("Require n >= 0 and 0 <= k <= n")

    return comb(n, k)


def exact_match_probability(
    population: int,
    picks: int,
    draw_size: int,
    matches: int,
) -> float:
    """
    Calculate the probability of matching exactly `matches` numbers.

    Uses the hypergeometric distribution, assuming:
    - Numbers are drawn without replacement.
    - Every combination is equally likely.
    """
    if population <= 0:
        raise ValueError("Population must be positive")

    if not 0 <= picks <= population:
        raise ValueError("Picks must be between 0 and population")

    if not 0 <= draw_size <= population:
        raise ValueError("Draw size must be between 0 and population")

    if not 0 <= matches <= min(picks, draw_size):
        raise ValueError("Invalid number of matches")

    if picks - matches > population - draw_size:
        return 0.0

    favorable = (
        combinations(draw_size, matches)
        * combinations(population - draw_size, picks - matches)
    )

    total = combinations(population, picks)

    return favorable / total


def expected_value(
    probabilities: Sequence[float],
    payouts: Sequence[float],
    stake: float = 0.0,
) -> float:
    """
    Calculate expected net profit per bet.

    Payouts represent gross money received, including any returned stake.
    Probabilities must describe mutually exclusive, exhaustive outcomes.
    """
    if len(probabilities) != len(payouts) or not probabilities:
        raise ValueError("Probabilities and payouts must have equal non-zero length")

    if stake < 0:
        raise ValueError("Stake cannot be negative")

    if any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("Probabilities must be between 0 and 1")

    if any(payout < 0 for payout in payouts):
        raise ValueError("Payouts cannot be negative")

    if not isclose(sum(probabilities), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Probabilities must sum to 1")

    gross_expected_payout = sum(
        probability * payout
        for probability, payout in zip(probabilities, payouts)
    )

    return gross_expected_payout - stake


def expected_roi(ev: float, stake: float) -> float:
    """
    Calculate expected return on investment as a percentage.

    EV must represent net expected profit.
    """
    if stake <= 0:
        raise ValueError("Stake must be greater than zero")

    return (ev / stake) * 100
