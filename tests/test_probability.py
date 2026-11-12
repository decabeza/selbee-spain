import pytest

from selbee.mathematics.probability import (
    combinations,
    exact_match_probability,
    expected_value,
    expected_roi,
)


def test_bonoloto_total_combinations():
    """Bonoloto has 13,983,816 possible combinations."""
    assert combinations(49, 6) == 13_983_816


def test_invalid_combinations():
    with pytest.raises(ValueError):
        combinations(5, 6)


def test_bonoloto_jackpot_probability():
    """Probability of matching all 6 numbers."""
    probability = exact_match_probability(
        population=49,
        picks=6,
        draw_size=6,
        matches=6,
    )

    assert probability == pytest.approx(1 / 13_983_816)


def test_match_probabilities_sum_to_one():
    """All possible match outcomes must sum to 100%."""
    probabilities = [
        exact_match_probability(49, 6, 6, matches)
        for matches in range(7)
    ]

    assert sum(probabilities) == pytest.approx(1.0)


def test_expected_value():
    """A 10% chance of receiving 10 euros for a 1 euro stake."""
    ev = expected_value(
        probabilities=[0.10, 0.90],
        payouts=[10.0, 0.0],
        stake=1.0,
    )

    assert ev == pytest.approx(0.0)


def test_positive_expected_value():
    ev = expected_value(
        probabilities=[0.20, 0.80],
        payouts=[10.0, 0.0],
        stake=1.0,
    )

    assert ev == pytest.approx(1.0)


def test_expected_roi():
    assert expected_roi(ev=1.0, stake=10.0) == pytest.approx(10.0)


def test_invalid_probability_distribution():
    with pytest.raises(ValueError):
        expected_value(
            probabilities=[0.20, 0.50],
            payouts=[10.0, 0.0],
            stake=1.0,
        )
