"""
SELBEE SPAIN - Bonoloto Expected Value Analyzer

Baseline EV model using official prize allocation rules
and an independent, uniformly distributed opponent model.

Important:
- This is a scenario estimator, not an exact draw settlement model.
- Lower-category roll-downs are not included yet.
- All monetary results are pre-tax.
"""

from math import isfinite

from selbee.games.bonoloto import (
    STAKE_PER_LINE,
    THIRD_CATEGORY_FIXED_PRIZE,
    calculate_category_probabilities,
    reintegro_probability,
)

from selbee.mathematics.prize_sharing import expected_shared_prize


PRIZE_FUND_RATE = 0.45
REINTEGRO_FUND_RATE = 0.10

CATEGORY_ALLOCATION = {
    "first": 0.55,
    "second": 0.20,
    "third": 0.10,
    "fourth": 0.15,
}


def calculate_prize_pools(
    revenue_eur: float,
    expected_fifth_winners: float,
    first_prize_pool_eur: float,
) -> dict[str, float]:
    """
    Estimate the available prize pools.

    first_prize_pool_eur must represent the total first-category
    pool for the draw, including current allocation and carryover.

    The other category pools are calculated from the current draw's
    45% category fund, after deducting expected fixed fifth-category
    payouts.
    """

    values = (
        revenue_eur,
        expected_fifth_winners,
        first_prize_pool_eur,
    )

    if not all(isfinite(value) for value in values):
        raise ValueError("All monetary inputs must be finite")

    if revenue_eur < 0:
        raise ValueError("Revenue cannot be negative")

    if expected_fifth_winners < 0:
        raise ValueError("Expected winners cannot be negative")

    if first_prize_pool_eur < 0:
        raise ValueError("First prize pool cannot be negative")

    category_fund = revenue_eur * PRIZE_FUND_RATE

    fifth_fixed_payout = (
        expected_fifth_winners * THIRD_CATEGORY_FIXED_PRIZE
    )

    remaining_fund = category_fund - fifth_fixed_payout

    if remaining_fund < -1e-9:
        raise ValueError(
            "Expected fifth-category payouts exceed the category fund"
        )

    remaining_fund = max(0.0, remaining_fund)

    return {
        "first": first_prize_pool_eur,
        "second": remaining_fund * CATEGORY_ALLOCATION["second"],
        "third": remaining_fund * CATEGORY_ALLOCATION["third"],
        "fourth": remaining_fund * CATEGORY_ALLOCATION["fourth"],
        "fifth_fixed_payout": fifth_fixed_payout,
        "reintegro_fund": revenue_eur * REINTEGRO_FUND_RATE,
        "current_first_allocation": (
            remaining_fund * CATEGORY_ALLOCATION["first"]
        ),
    }


def estimate_ev_per_line(
    revenue_eur: float,
    first_prize_pool_eur: float,
    other_entries: int,
) -> dict:
    """
    Estimate expected gross and net return per Bonoloto line.

    other_entries represents all other lines participating in
    the same draw, excluding the line being evaluated.

    Assumptions:
    - Other lines are independent and uniformly distributed.
    - Shared category pools are divided equally.
    - Lower-category roll-downs are excluded.
    - Tax is excluded.
    """

    if not isinstance(other_entries, int) or isinstance(other_entries, bool):
        raise TypeError("other_entries must be an integer")

    if other_entries < 0:
        raise ValueError("other_entries cannot be negative")

    if not isfinite(revenue_eur) or revenue_eur <= 0:
        raise ValueError("Revenue must be finite and greater than zero")

    if not isfinite(first_prize_pool_eur) or first_prize_pool_eur < 0:
        raise ValueError("First prize pool must be finite and non-negative")

    probabilities = calculate_category_probabilities()

    # Our line cannot win the fifth category if it wins categories 1-4.
    # Therefore, expected fifth-category winners are calculated
    # using the other participating lines only.
    expected_fifth_winners = (
        other_entries * probabilities["fifth"]
    )

    pools = calculate_prize_pools(
        revenue_eur=revenue_eur,
        expected_fifth_winners=expected_fifth_winners,
        first_prize_pool_eur=first_prize_pool_eur,
    )

    expected_category_payouts = {}

    for category in ("first", "second", "third", "fourth"):
        probability = probabilities[category]

        expected_category_payouts[category] = (
            probability
            * expected_shared_prize(
                prize_pool=pools[category],
                win_probability=probability,
                other_entries=other_entries,
            )
        )

    # Fifth category: fixed gross payout of 4 EUR.
    expected_fifth_payout = (
        probabilities["fifth"] * THIRD_CATEGORY_FIXED_PRIZE
    )

    # Reintegro: 10% probability of recovering the 0.50 EUR line stake.
    expected_reintegro_payout = (
        reintegro_probability() * STAKE_PER_LINE
    )

    expected_variable_payout = sum(
        expected_category_payouts.values()
    )

    expected_gross_payout = (
        expected_variable_payout
        + expected_fifth_payout
        + expected_reintegro_payout
    )

    ev = expected_gross_payout - STAKE_PER_LINE

    roi = (ev / STAKE_PER_LINE) * 100

    return {
        "revenue_eur": revenue_eur,
        "first_prize_pool_eur": first_prize_pool_eur,
        "other_entries": other_entries,
        "prize_pools": pools,
        "expected_category_payouts": expected_category_payouts,
        "expected_fifth_payout": expected_fifth_payout,
        "expected_reintegro_payout": expected_reintegro_payout,
        "expected_gross_payout": expected_gross_payout,
        "stake_eur": STAKE_PER_LINE,
        "ev_per_line": ev,
        "roi_percent": roi,
    }
