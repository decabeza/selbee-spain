"""
SELBEE SPAIN - Bonoloto Game Model

Official game mechanics and exact mathematical probabilities.
"""

from selbee.mathematics.probability import exact_match_probability


# Official game configuration
POPULATION = 49
PICKS = 6
DRAW_SIZE = 6
COMPLEMENTARY_POOL_SIZE = POPULATION - DRAW_SIZE

REINTEGRO_OUTCOMES = 10

STAKE_PER_LINE = 0.50
MIN_LINES_PER_DRAW = 2

THIRD_CATEGORY_FIXED_PRIZE = 4.00


def calculate_category_probabilities() -> dict[str, float]:
    """
    Calculate the exact probability of each Bonoloto prize category.

    The complementary number is drawn from the 43 numbers
    not included in the six main winning numbers.

    Reintegro is calculated separately because it is an
    independent additional prize.
    """

    p_six = exact_match_probability(
        POPULATION, PICKS, DRAW_SIZE, 6
    )

    p_five_total = exact_match_probability(
        POPULATION, PICKS, DRAW_SIZE, 5
    )

    # Exactly five main numbers, with the sixth selected
    # number matching the complementary number.
    p_five_plus_complementary = (
        p_five_total / COMPLEMENTARY_POOL_SIZE
    )

    p_five = p_five_total - p_five_plus_complementary

    p_four = exact_match_probability(
        POPULATION, PICKS, DRAW_SIZE, 4
    )

    p_three = exact_match_probability(
        POPULATION, PICKS, DRAW_SIZE, 3
    )

    p_no_number_prize = 1.0 - (
        p_six
        + p_five_plus_complementary
        + p_five
        + p_four
        + p_three
    )

    return {
        "first": p_six,
        "second": p_five_plus_complementary,
        "third": p_five,
        "fourth": p_four,
        "fifth": p_three,
        "no_number_prize": p_no_number_prize,
    }


def reintegro_probability() -> float:
    """Probability of matching the randomly assigned reintegro."""
    return 1.0 / REINTEGRO_OUTCOMES


def probability_of_any_prize() -> float:
    """
    Probability of receiving at least one prize.

    Includes number-based prizes and the independent reintegro.
    """
    probabilities = calculate_category_probabilities()

    p_no_number_prize = probabilities["no_number_prize"]
    p_no_reintegro = 1.0 - reintegro_probability()

    return 1.0 - (p_no_number_prize * p_no_reintegro)


def expected_fixed_prize_per_line() -> float:
    """
    Calculate gross expected payout from known fixed prizes only.

    Includes:
    - Fifth category: 4 EUR for exactly 3 matches.
    - Reintegro: returns the 0.50 EUR line stake.

    Excludes variable prize categories.
    """
    probabilities = calculate_category_probabilities()

    fifth_category_return = (
        probabilities["fifth"] * THIRD_CATEGORY_FIXED_PRIZE
    )

    reintegro_return = (
        reintegro_probability() * STAKE_PER_LINE
    )

    return fifth_category_return + reintegro_return


def fixed_prize_ev_per_line() -> float:
    """
    Calculate partial net EV from known fixed prize components.

    Variable prize categories are deliberately excluded.
    """
    return expected_fixed_prize_per_line() - STAKE_PER_LINE


def minimum_ticket_cost() -> float:
    """Calculate the minimum cost for one draw."""
    return STAKE_PER_LINE * MIN_LINES_PER_DRAW
