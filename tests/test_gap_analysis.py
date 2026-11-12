import json
import sqlite3

from pathlib import Path

import pytest

from selbee.mathematics.gap_analysis import (
    analyze_gaps,
    calculate_theoretical_gap_distribution,
    test_gap_distribution_monte_carlo as run_gap_monte_carlo,
)

@pytest.fixture
def sample_database(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_selbee.db"

    combinations = [
        [1, 2, 3, 4, 5, 6],
        [1, 3, 6, 10, 15, 21],
    ]

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE historical_combinations (
                draw_date TEXT PRIMARY KEY,
                main_numbers TEXT NOT NULL
            )
            """
        )

        for index, numbers in enumerate(combinations):
            connection.execute(
                """
                INSERT INTO historical_combinations
                (draw_date, main_numbers)
                VALUES (?, ?)
                """,
                (
                    f"2026-01-0{index + 1}",
                    json.dumps(numbers),
                ),
            )

    return db_path


def test_analyze_gaps(sample_database):
    result = analyze_gaps(sample_database)

    assert result["total_draws"] == 2
    assert result["total_gaps"] == 10
    assert result["observed_mean_gap"] == pytest.approx(2.5)

    assert result["gap_distribution"] == {
        1: 5,
        2: 1,
        3: 1,
        4: 1,
        5: 1,
        6: 1,
    }

    assert result["small_gap_counts"] == {
        1: 5,
        2: 1,
        3: 1,
    }


def test_theoretical_gap_distribution():
    result = calculate_theoretical_gap_distribution()

    assert result["total_combinations"] == 13_983_816
    assert result["total_gap_occurrences"] == 69_919_080

    assert sum(result["distribution"].values()) == (
        69_919_080
    )

    assert sum(result["probabilities"].values()) == pytest.approx(1.0)

    assert result["mean"] == pytest.approx(50 / 7)


def test_gap_monte_carlo(sample_database):
    result = run_gap_monte_carlo(
        db_path=sample_database,
        simulations=20,
        seed=42,
    )

    assert result["total_draws"] == 2
    assert result["total_gaps"] == 10
    assert result["simulations"] == 20

    assert 0 <= result["empirical_p_value"] <= 1


def test_gap_analysis_empty_database(tmp_path):
    db_path = tmp_path / "empty.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE historical_combinations (
                draw_date TEXT PRIMARY KEY,
                main_numbers TEXT NOT NULL
            )
            """
        )

    with pytest.raises(ValueError, match="No historical combinations"):
        analyze_gaps(db_path)
