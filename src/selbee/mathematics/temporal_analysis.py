"""
SELBEE SPAIN - Temporal Statistical Analysis
"""

import json
import sqlite3

import pandas as pd

from pathlib import Path

from selbee.mathematics.historical_analysis import (
    analyze_number_frequencies,
)


DATABASE_PATH = Path("data/processed/selbee.db")


def analyze_temporal_frequencies(
    db_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Analyze main-number frequencies by historical period."""

    with sqlite3.connect(db_path) as connection:
        draws = pd.read_sql_query(
            """
            SELECT draw_date, main_numbers
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if draws.empty:
        raise ValueError("No historical combinations found")

    draws["draw_date"] = pd.to_datetime(draws["draw_date"])
    draws["decade"] = (
        draws["draw_date"].dt.year // 10
    ) * 10

    results = []

    for decade, period in draws.groupby("decade"):

        combinations = [
            json.loads(value)
            for value in period["main_numbers"]
        ]

        analysis = analyze_number_frequencies(combinations)

        results.append({
            "period": (
                f"{decade}-{min(decade + 9, 2026)}"
            ),
            "draws": analysis["total_draws"],
            "expected_frequency": analysis["expected_frequency"],
            "pearson_statistic": analysis["pearson_statistic"],
            "corrected_statistic": analysis["corrected_statistic"],
            "p_value": analysis["p_value"],
            "significant_at_5_percent": (
                analysis["significant_at_5_percent"]
            ),
        })

    return pd.DataFrame(results)
