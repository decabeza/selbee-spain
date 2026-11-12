
import pytest

from selbee.games.bonoloto import (
    calculate_category_probabilities,
    reintegro_probability,
    probability_of_any_prize,
    expected_fixed_prize_per_line,
    fixed_prize_ev_per_line,
    minimum_ticket_cost,
)


def test_category_probabilities_sum_to_one():
    probabilities = calculate_category_probabilities()

    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_first_category_probability():
    probabilities = calculate_category_probabilities()

    assert probabilities["first"] == pytest.approx(
        1 / 13_983_816
    )


def test_second_category_probability():
    probabilities = calculate_category_probabilities()

    assert probabilities["second"] == pytest.approx(
        1 / 2_330_636
    )


def test_third_category_probability():
    probabilities = calculate_category_probabilities()

    assert probabilities["third"] == pytest.approx(
        252 / 13_983_816
    )


def test_reintegro_probability():
    assert reintegro_probability() == pytest.approx(0.10)


def test_any_prize_probability():
    probability = probability_of_any_prize()

    assert 0 < probability < 1


def test_fixed_prize_expected_value():
    expected = expected_fixed_prize_per_line()

    assert expected > 0


def test_fixed_prize_ev_is_negative():
    ev = fixed_prize_ev_per_line()

    assert ev < 0


def test_minimum_ticket_cost():
    assert minimum_ticket_cost() == pytest.approx(1.00)
