"""
SELBEE SPAIN - Combination Structure Analysis
"""

import json
import sqlite3

from pathlib import Path

import pandas as pd

from scipy.stats import hypergeom, chisquare


DATABASE_PATH = Path("data/processed/selbee.db")


def analyze_parity_distribution(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Analyze even/odd distribution against its theoretical model."""

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if draws.empty:
        raise ValueError("No historical combinations found")

    distribution = {even: 0 for even in range(7)}

    for value in draws["main_numbers"]:
        numbers = json.loads(value)

        if (
            len(numbers) != 6
            or len(set(numbers)) != 6
            or any(number < 1 or number > 49 for number in numbers)
        ):
            raise ValueError("Invalid historical combination")

        even_count = sum(number % 2 == 0 for number in numbers)
        distribution[even_count] += 1

    total_draws = len(draws)

    observed = [
        distribution[even]
        for even in range(7)
    ]

    expected_probabilities = hypergeom.pmf(
        range(7),
        M=49,
        n=24,
        N=6,
    )

    expected = expected_probabilities * total_draws

    # Combine categories with low expected counts.
    observed_grouped = [
        observed[0] + observed[1],
        observed[2],
        observed[3],
        observed[4],
        observed[5] + observed[6],
    ]

    expected_grouped = [
        expected[0] + expected[1],
        expected[2],
        expected[3],
        expected[4],
        expected[5] + expected[6],
    ]

    chi_statistic, p_value = chisquare(
        observed_grouped,
        expected_grouped,
    )

    return {
        "total_draws": total_draws,
        "observed_distribution": distribution,
        "expected_distribution": {
            even: float(expected_probabilities[even])
            for even in range(7)
        },
        "chi_square_statistic": float(chi_statistic),
        "degrees_of_freedom": 4,
        "p_value": float(p_value),
        "significant_at_5_percent": bool(p_value < 0.05),
    }

def analyze_sum_distribution(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Analyze the sum distribution of historical combinations."""

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if draws.empty:
        raise ValueError("No historical combinations found")

    sums = []

    for value in draws["main_numbers"]:
        numbers = json.loads(value)

        if (
            len(numbers) != 6
            or len(set(numbers)) != 6
            or any(number < 1 or number > 49 for number in numbers)
        ):
            raise ValueError("Invalid historical combination")

        sums.append(sum(numbers))

    return {
        "total_draws": len(sums),
        "observed_mean": float(pd.Series(sums).mean()),
        "observed_std": float(pd.Series(sums).std(ddof=0)),
        "minimum_sum": min(sums),
        "maximum_sum": max(sums),
        "sum_values": sums,
    }

def calculate_theoretical_sum_distribution() -> dict:
    """
    Calculate the exact distribution of sums for 6 numbers
    selected without replacement from 1 to 49.
    """

    import math

    picks = 6
    population = 49

    # dp[k][s] = number of ways to select k numbers
    # with a total sum of s.
    dp = [
        [0] * (population * picks + 1)
        for _ in range(picks + 1)
    ]

    dp[0][0] = 1

    for number in range(1, population + 1):
        for count in range(picks, 0, -1):
            for total in range(
                population * picks,
                number - 1,
                -1,
            ):
                dp[count][total] += dp[count - 1][total - number]

    total_combinations = math.comb(population, picks)

    distribution = {
        total: dp[picks][total]
        for total in range(21, 280)
        if dp[picks][total] > 0
    }

    probabilities = {
        total: count / total_combinations
        for total, count in distribution.items()
    }

    return {
        "total_combinations": total_combinations,
        "distribution": distribution,
        "probabilities": probabilities,
        "mean": sum(
            total * probability
            for total, probability in probabilities.items()
        ),
    }

def test_historical_sum_distribution(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Compare historical sums with the exact theoretical distribution."""

    from scipy.stats import chisquare

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if draws.empty:
        raise ValueError("No historical combinations found")

    historical_sums = [
        sum(json.loads(value))
        for value in draws["main_numbers"]
    ]

    theoretical = calculate_theoretical_sum_distribution()

    total_draws = len(historical_sums)

    # Group sums into 10-point intervals.
    bins = list(range(20, 291, 10))

    observed_counts = pd.cut(
        historical_sums,
        bins=bins,
        right=False,
        include_lowest=True,
        labels=False,
    )

    observed = (
        pd.Series(observed_counts)
        .value_counts()
        .reindex(range(len(bins) - 1), fill_value=0)
        .sort_index()
    )

    theoretical_grouped = {}

    for index in range(len(bins) - 1):
        lower = bins[index]
        upper = bins[index + 1]

        theoretical_grouped[index] = sum(
            probability
            for total, probability in theoretical["probabilities"].items()
            if lower <= total < upper
        ) * total_draws

    observed_grouped = {
        index: int(observed.get(index, 0))
        for index in theoretical_grouped
    }

    # Merge adjacent intervals until expected counts are sufficient.
    grouped_observed = []
    grouped_expected = []

    current_observed = 0
    current_expected = 0.0

    for index in theoretical_grouped:
        current_observed += observed_grouped[index]
        current_expected += theoretical_grouped[index]

        if current_expected >= 5:
            grouped_observed.append(current_observed)
            grouped_expected.append(current_expected)
            current_observed = 0
            current_expected = 0.0

    if current_expected > 0:
        grouped_observed[-1] += current_observed
        grouped_expected[-1] += current_expected

    statistic, p_value = chisquare(
        grouped_observed,
        grouped_expected,
    )

    return {
        "total_draws": total_draws,
        "observed_mean": float(pd.Series(historical_sums).mean()),
        "theoretical_mean": theoretical["mean"],
        "observed_std": float(pd.Series(historical_sums).std(ddof=0)),
        "observed_min": min(historical_sums),
        "observed_max": max(historical_sums),
        "chi_square_statistic": float(statistic),
        "degrees_of_freedom": len(grouped_observed) - 1,
        "p_value": float(p_value),
        "observed_grouped": grouped_observed,
        "expected_grouped": grouped_expected,
        "significant_at_5_percent": bool(p_value < 0.05),
    }

def analyze_consecutive_numbers(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Analyze consecutive-number pairs in historical combinations."""

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if draws.empty:
        raise ValueError("No historical combinations found")

    distribution = {}

    total_pairs = 0

    for value in draws["main_numbers"]:
        numbers = sorted(json.loads(value))

        if (
            len(numbers) != 6
            or len(set(numbers)) != 6
            or any(number < 1 or number > 49 for number in numbers)
        ):
            raise ValueError("Invalid historical combination")

        consecutive_pairs = sum(
            numbers[index + 1] - numbers[index] == 1
            for index in range(5)
        )

        distribution[consecutive_pairs] = (
            distribution.get(consecutive_pairs, 0) + 1
        )

        total_pairs += consecutive_pairs

    total_draws = len(draws)

    return {
        "total_draws": total_draws,
        "observed_distribution": distribution,
        "mean_consecutive_pairs": total_pairs / total_draws,
        "expected_consecutive_pairs": 30 / 49,
    }

def calculate_theoretical_consecutive_distribution() -> dict:
    """
    Calculate the exact distribution of adjacent pairs
    in combinations of 6 numbers selected from 1 to 49.
    """

    import math

    population = 49
    picks = 6

    total_combinations = math.comb(population, picks)

    distribution = {}

    for consecutive_pairs in range(picks):

        # Number of consecutive blocks.
        blocks = picks - consecutive_pairs

        # Select the positions of the blocks and distribute
        # the remaining non-selected numbers around them.
        count = (
            math.comb(picks - 1, blocks - 1)
            * math.comb(population - picks + 1, blocks)
        )

        distribution[consecutive_pairs] = count

    probabilities = {
        pairs: count / total_combinations
        for pairs, count in distribution.items()
    }

    expected_mean = sum(
        pairs * probability
        for pairs, probability in probabilities.items()
    )

    return {
        "total_combinations": total_combinations,
        "distribution": distribution,
        "probabilities": probabilities,
        "mean": expected_mean,
    }

def test_consecutive_distribution(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Compare historical consecutive pairs with the exact distribution."""

    from scipy.stats import chisquare

    historical = analyze_consecutive_numbers(db_path)
    theoretical = calculate_theoretical_consecutive_distribution()

    total_draws = historical["total_draws"]
    observed_distribution = historical["observed_distribution"]

    # Categories 0, 1, 2 and 3 or more.
    observed = [
        observed_distribution.get(0, 0),
        observed_distribution.get(1, 0),
        observed_distribution.get(2, 0),
        sum(
            observed_distribution.get(pairs, 0)
            for pairs in range(3, 6)
        ),
    ]

    expected = [
        theoretical["probabilities"][0] * total_draws,
        theoretical["probabilities"][1] * total_draws,
        theoretical["probabilities"][2] * total_draws,
        sum(
            theoretical["probabilities"][pairs]
            for pairs in range(3, 6)
        ) * total_draws,
    ]

    statistic, p_value = chisquare(observed, expected)

    return {
        "total_draws": total_draws,
        "observed": observed,
        "expected": expected,
        "theoretical_mean": theoretical["mean"],
        "observed_mean": historical["mean_consecutive_pairs"],
        "chi_square_statistic": float(statistic),
        "degrees_of_freedom": 3,
        "p_value": float(p_value),
        "significant_at_5_percent": bool(p_value < 0.05),
    }
