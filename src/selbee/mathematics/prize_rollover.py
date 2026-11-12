"""
SELBEE SPAIN - Prize Rollover Engine

Applies Bonoloto prize-pool rollovers when a category
has no winners.
"""

from math import isfinite


CATEGORIES = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
)


def apply_category_rollovers(
    pools: dict[str, float],
    winners: dict[str, int],
) -> dict:
    """
    Apply category rollovers according to the Bonoloto
    prize allocation sequence.

    Rules implemented:
    - First category: rolls over to the next draw.
    - Second category: rolls into third category.
    - Third category: rolls into fourth category.
    - Fourth category: rolls into first category of the next draw.
    - Fifth category: fixed prize; does not roll over.

    The input pools must already include any applicable
    current-draw allocations and previous carryovers.

    Returns:
        pools: Prize pools after current-draw rollovers.
        first_prize_rollover: Amount carried into the next draw.
    """

    if set(pools) != set(CATEGORIES):
        raise ValueError("Pools must contain exactly the five categories")

    if set(winners) != set(CATEGORIES):
        raise ValueError("Winners must contain exactly the five categories")

    updated_pools = {}

    for category in CATEGORIES:
        pool = pools[category]
        count = winners[category]

        if not isinstance(pool, (int, float)) or isinstance(pool, bool):
            raise TypeError("Prize pools must be numeric")

        if not isfinite(pool) or pool < 0:
            raise ValueError("Prize pools must be finite and non-negative")

        if not isinstance(count, int) or isinstance(count, bool):
            raise TypeError("Winner counts must be integers")

        if count < 0:
            raise ValueError("Winner counts cannot be negative")

        updated_pools[category] = float(pool)

    first_prize_rollover = 0.0

    # First category: carry over to the next draw.
    if winners["first"] == 0:
        first_prize_rollover += updated_pools["first"]
        updated_pools["first"] = 0.0

    # Second category rolls into third.
    if winners["second"] == 0:
        updated_pools["third"] += updated_pools["second"]
        updated_pools["second"] = 0.0

    # Third category rolls into fourth.
    if winners["third"] == 0:
        updated_pools["fourth"] += updated_pools["third"]
        updated_pools["third"] = 0.0

    # Fourth category rolls into first category of the next draw.
    if winners["fourth"] == 0:
        first_prize_rollover += updated_pools["fourth"]
        updated_pools["fourth"] = 0.0

    return {
        "pools": updated_pools,
        "first_prize_rollover": first_prize_rollover,
    }
