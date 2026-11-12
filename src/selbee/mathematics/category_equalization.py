"""
SELBEE SPAIN - Category Equalization Engine

Implements the category prize equalization mechanism
described in Bonoloto rule 8.4.

Input pools must already reflect any applicable
rollovers under rule 8.3.
"""

from math import isfinite


CATEGORIES = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
)


def equalize_category_prizes(
    pools: dict[str, float],
    winners: dict[str, int],
) -> dict:
    """
    Equalize adjacent category prizes when a lower category
    would otherwise pay more per winner than the preceding one.

    Categories are ordered from highest to lowest.

    Returns:
        payouts: Gross prize per winner in each category.
        merged_groups: Categories sharing the same prize.
    """

    if set(pools) != set(CATEGORIES):
        raise ValueError("Pools must contain exactly the five categories")

    if set(winners) != set(CATEGORIES):
        raise ValueError("Winners must contain exactly the five categories")

    groups = []

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

        if count == 0:
            if pool > 0:
                raise ValueError(
                    f"Category {category} has an undistributed pool. "
                    "Resolve rollovers before equalization."
                )
            continue

        groups.append({
            "categories": [category],
            "pool": float(pool),
            "winners": count,
        })

        # Merge adjacent categories while a lower category
        # would pay more per winner than the preceding category.
        while len(groups) >= 2:
            previous = groups[-2]
            current = groups[-1]

            previous_prize = previous["pool"] / previous["winners"]
            current_prize = current["pool"] / current["winners"]

            if current_prize <= previous_prize:
                break

            merged = {
                "categories": (
                    previous["categories"] + current["categories"]
                ),
                "pool": previous["pool"] + current["pool"],
                "winners": previous["winners"] + current["winners"],
            }

            groups[-2:] = [merged]

    payouts = {}
    merged_groups = []

    for group in groups:
        prize_per_winner = group["pool"] / group["winners"]

        for category in group["categories"]:
            payouts[category] = prize_per_winner

        merged_groups.append(group["categories"])

    return {
        "payouts": payouts,
        "merged_groups": merged_groups,
    }
