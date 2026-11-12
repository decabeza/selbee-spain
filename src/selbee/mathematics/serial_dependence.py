"""
SELBEE SPAIN - Serial Dependence Analysis
"""

import json
import sqlite3

from pathlib import Path

import numpy as np
import pandas as pd

from scipy.stats import chisquare, hypergeom


DATABASE_PATH = Path("data/processed/selbee.db")


def analyze_consecutive_draws(
    db_path: Path = DATABASE_PATH,
) -> dict:
    """Analyze repeated main numbers between consecutive draws."""

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT draw_date, main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if len(draws) < 2:
        raise ValueError("At least two draws are required")

    dates = pd.to_datetime(draws["draw_date"])

    combinations = [
        set(json.loads(value))
        for value in draws["main_numbers"]
    ]

    overlaps = [
        len(combinations[index] & combinations[index - 1])
        for index in range(1, len(combinations))
    ]

    observed = np.bincount(overlaps, minlength=7)

    total_transitions = len(overlaps)

    probabilities = hypergeom.pmf(
        np.arange(7),
        M=49,
        n=6,
        N=6,
    )

    expected = probabilities * total_transitions

    # Categories 0 to 6 are mutually exclusive.
    # Combine the last categories if expected counts are too small.
    observed_grouped = np.array([
        observed[0],
        observed[1],
        observed[2],
        observed[3],
        observed[4] + observed[5] + observed[6],
    ])

    expected_grouped = np.array([
        expected[0],
        expected[1],
        expected[2],
        expected[3],
        expected[4] + expected[5] + expected[6],
    ])

    chi_statistic, p_value = chisquare(
        observed_grouped,
        expected_grouped,
    )

    return {
        "total_transitions": total_transitions,
        "mean_repeated_numbers": float(np.mean(overlaps)),
        "expected_repeated_numbers": 36 / 49,
        "observed_distribution": observed.tolist(),
        "expected_distribution": probabilities.tolist(),
        "chi_square_statistic": float(chi_statistic),
        "degrees_of_freedom": 4,
        "p_value": float(p_value),
        "significant_at_5_percent": bool(p_value < 0.05),
        "first_date": dates.iloc[0].date().isoformat(),
        "last_date": dates.iloc[-1].date().isoformat(),
    }
