
import json
import sqlite3

from pathlib import Path

import numpy as np
import pandas as pd

from selbee.mathematics.combination_structure import DATABASE_PATH


def analyze_gaps(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """
    Analyze distances between consecutive numbers
    in historical Bonoloto combinations.
    """

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

    all_gaps = []
    minimum_gaps = []
    maximum_gaps = []
    mean_gaps = []

    gap_distribution = {}

    small_gap_counts = {
        1: 0,
        2: 0,
        3: 0,
    }

    for value in draws["main_numbers"]:
        numbers = sorted(json.loads(value))

        if (
            len(numbers) != 6
            or len(set(numbers)) != 6
            or any(number < 1 or number > 49 for number in numbers)
        ):
            raise ValueError("Invalid historical combination")

        gaps = [
            numbers[index + 1] - numbers[index]
            for index in range(5)
        ]

        all_gaps.extend(gaps)

        minimum_gaps.append(min(gaps))
        maximum_gaps.append(max(gaps))
        mean_gaps.append(float(np.mean(gaps)))

        for gap in gaps:
            gap_distribution[gap] = (
                gap_distribution.get(gap, 0) + 1
            )

            if gap <= 3:
                small_gap_counts[gap] += 1

    total_draws = len(draws)
    total_gaps = len(all_gaps)

    return {
        "total_draws": total_draws,
        "total_gaps": total_gaps,
        "observed_mean_gap": float(np.mean(all_gaps)),
        "observed_std_gap": float(np.std(all_gaps)),
        "observed_minimum_gap_mean": float(np.mean(minimum_gaps)),
        "observed_maximum_gap_mean": float(np.mean(maximum_gaps)),
        "observed_mean_of_draw_means": float(np.mean(mean_gaps)),
        "gap_distribution": dict(sorted(gap_distribution.items())),
        "small_gap_counts": small_gap_counts,
    }


import math


def calculate_theoretical_gap_distribution() -> dict:
    """
    Calculate the exact pooled distribution of the five
    internal gaps in combinations of 6 numbers from 1 to 49.
    """

    population = 49
    picks = 6

    total_combinations = math.comb(population, picks)
    total_gaps = picks - 1

    distribution = {}

    for gap in range(1, population - picks + 2):
        count = (
            (population - gap)
            * math.comb(population - gap - 1, picks - 2)
        )

        distribution[gap] = count

    total_gap_occurrences = total_combinations * total_gaps

    probabilities = {
        gap: count / total_gap_occurrences
        for gap, count in distribution.items()
    }

    expected_mean = sum(
        gap * probability
        for gap, probability in probabilities.items()
    )

    return {
        "total_combinations": total_combinations,
        "total_gap_occurrences": total_gap_occurrences,
        "distribution": distribution,
        "probabilities": probabilities,
        "mean": expected_mean,
    }


def test_gap_distribution_monte_carlo(
    db_path: Path = DATABASE_PATH,
    simulations: int = 2000,
    seed: int = 42,
) -> dict:
    """
    Compare historical gap frequencies with the theoretical model
    using Monte Carlo simulations at draw level.

    The complete six-number draw is simulated as a unit, preserving
    the dependence between its five internal gaps.
    """

    if simulations < 1:
        raise ValueError("Simulations must be greater than zero")

    historical = analyze_gaps(db_path)
    theoretical = calculate_theoretical_gap_distribution()

    total_draws = historical["total_draws"]
    observed_distribution = historical["gap_distribution"]

    # Build groups with at least five expected occurrences.
    groups = []
    current_start = 1
    current_expected = 0.0

    for gap, probability in theoretical["probabilities"].items():
        current_expected += probability * total_draws * 5

        if current_expected >= 5:
            groups.append((current_start, gap))
            current_start = gap + 1
            current_expected = 0.0

    # Merge any remaining tail into the last group.
    if current_expected > 0:
        if groups:
            groups[-1] = (groups[-1][0], 44)
        else:
            groups.append((current_start, 44))

    expected = np.array([
        sum(
            theoretical["probabilities"][gap]
            for gap in range(start, end + 1)
        ) * total_draws * 5
        for start, end in groups
    ])

    observed = np.array([
        sum(
            observed_distribution.get(gap, 0)
            for gap in range(start, end + 1)
        )
        for start, end in groups
    ])

    observed_statistic = float(
        np.sum((observed - expected) ** 2 / expected)
    )

    rng = np.random.default_rng(seed)
    simulated_statistics = np.empty(simulations)

    for simulation in range(simulations):
        # Generate uniform random six-number combinations.
        random_values = rng.random((total_draws, 49))

        selected = np.argpartition(
            random_values,
            kth=5,
            axis=1,
        )[:, :6]

        selected.sort(axis=1)

        gaps = np.diff(selected, axis=1)
        gap_counts = np.bincount(
            gaps.ravel() + 0,
            minlength=50,
        )

        simulated_observed = np.array([
            sum(
                gap_counts[gap]
                for gap in range(start, end + 1)
            )
            for start, end in groups
        ])

        simulated_statistics[simulation] = np.sum(
            (simulated_observed - expected) ** 2 / expected
        )

    exceedances = int(
        np.sum(simulated_statistics >= observed_statistic)
    )

    empirical_p_value = (
        exceedances + 1
    ) / (
        simulations + 1
    )

    return {
        "total_draws": total_draws,
        "total_gaps": total_draws * 5,
        "simulations": simulations,
        "seed": seed,
        "groups": groups,
        "observed_grouped": observed.tolist(),
        "expected_grouped": expected.tolist(),
        "observed_statistic": observed_statistic,
        "simulated_statistic_mean": float(
            np.mean(simulated_statistics)
        ),
        "simulated_statistic_std": float(
            np.std(simulated_statistics)
        ),
        "exceedances": exceedances,
        "empirical_p_value": float(empirical_p_value),
        "significant_at_5_percent": bool(
            empirical_p_value < 0.05
        ),
    }
