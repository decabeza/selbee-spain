"""
SELBEE SPAIN - Historical Statistical Analysis
"""

import numpy as np
from scipy.stats import chi2

from numpy.random import default_rng

def analyze_number_frequencies(
    combinations: list[list[int]],
) -> dict:
    """Test uniformity of Bonoloto main-number frequencies."""

    if not combinations:
        raise ValueError("At least one combination is required")

    observed = np.zeros(49, dtype=int)

    for combination in combinations:
        if len(combination) != 6:
            raise ValueError("Each combination must contain 6 numbers")

        if len(set(combination)) != 6:
            raise ValueError("Numbers within a combination must be unique")

        if any(number < 1 or number > 49 for number in combination):
            raise ValueError("Numbers must be between 1 and 49")

        for number in combination:
            observed[number - 1] += 1

    total_draws = len(combinations)
    expected_frequency = total_draws * 6 / 49
    expected = np.full(49, expected_frequency)

    pearson_statistic = float(
        np.sum((observed - expected) ** 2 / expected)
    )

    degrees_of_freedom = 48

    corrected_statistic = pearson_statistic * 48 / 43

    p_value = float(
        chi2.sf(corrected_statistic, degrees_of_freedom)
    )

    return {
        "total_draws": total_draws,
        "expected_frequency": expected_frequency,
        "observed_frequencies": observed.tolist(),
        "pearson_statistic": pearson_statistic,
        "corrected_statistic": corrected_statistic,
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": p_value,
        "significant_at_5_percent": p_value < 0.05,
    }

def monte_carlo_uniformity_test(
    combinations: list[list[int]],
    simulations: int = 2000,
    seed: int = 42,
) -> dict:
    """
    Validate the uniformity test using Monte Carlo simulations.

    Each simulated draw selects 6 distinct numbers from 1 to 49.
    """

    if simulations < 1:
        raise ValueError("At least one simulation is required")

    # Validate and calculate the real historical statistic.
    historical = analyze_number_frequencies(combinations)

    observed_statistic = historical["corrected_statistic"]
    total_draws = historical["total_draws"]

    rng = default_rng(seed)

    simulated_statistics = np.empty(simulations)

    expected_frequency = total_draws * 6 / 49

    for simulation in range(simulations):

        simulated_draws = np.array([
            rng.choice(49, size=6, replace=False)
            for _ in range(total_draws)
        ])

        frequencies = np.bincount(
            simulated_draws.flatten(),
            minlength=49,
        )

        pearson_statistic = np.sum(
            (frequencies - expected_frequency) ** 2
            / expected_frequency
        )

        simulated_statistics[simulation] = (
            pearson_statistic * 48 / 43
        )

    exceedances = np.sum(
        simulated_statistics >= observed_statistic
    )

    empirical_p_value = (
        (exceedances + 1) / (simulations + 1)
    )

    return {
        "simulations": simulations,
        "seed": seed,
        "observed_statistic": float(observed_statistic),
        "simulated_mean": float(np.mean(simulated_statistics)),
        "simulated_std": float(np.std(simulated_statistics)),
        "simulated_percentile_95": float(
            np.percentile(simulated_statistics, 95)
        ),
        "exceedances": int(exceedances),
        "empirical_p_value": float(empirical_p_value),
        "significant_at_5_percent": empirical_p_value < 0.05,
    }
