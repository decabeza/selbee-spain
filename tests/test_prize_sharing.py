
import pytest

from selbee.mathematics.prize_sharing import (
    expected_share_fraction,
    expected_shared_prize,
)


def test_no_other_entries():
    assert expected_share_fraction(0.10, 0) == pytest.approx(1.0)


def test_all_other_entries_also_win():
    assert expected_share_fraction(1.0, 9) == pytest.approx(0.10)


def test_one_other_entry():
    assert expected_share_fraction(0.50, 1) == pytest.approx(0.75)


def test_shared_prize_example():
    prize = expected_shared_prize(
        prize_pool=100_000,
        win_probability=0.10,
        other_entries=9,
    )

    assert prize == pytest.approx(65_132.15599, rel=1e-8)


def test_zero_probability_is_invalid():
    with pytest.raises(ValueError):
        expected_share_fraction(0, 10)


def test_negative_entries_are_invalid():
    with pytest.raises(ValueError):
        expected_share_fraction(0.10, -1)


def test_invalid_prize_pool():
    with pytest.raises(ValueError):
        expected_shared_prize(
            prize_pool=-100,
            win_probability=0.10,
            other_entries=10,
        )


def test_fraction_is_between_zero_and_one():
    fraction = expected_share_fraction(0.01, 1000)

    assert 0 < fraction <= 1
