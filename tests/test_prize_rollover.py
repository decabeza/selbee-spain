
import pytest

from selbee.mathematics.prize_rollover import apply_category_rollovers


def make_pools(**overrides):
    pools = {
        "first": 100_000.0,
        "second": 20_000.0,
        "third": 10_000.0,
        "fourth": 5_000.0,
        "fifth": 4.0,
    }
    pools.update(overrides)
    return pools


def make_winners(**overrides):
    winners = {
        "first": 1,
        "second": 1,
        "third": 1,
        "fourth": 1,
        "fifth": 1,
    }
    winners.update(overrides)
    return winners


def test_first_category_rolls_over_when_there_are_no_winners():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(first=0),
    )

    assert result["pools"]["first"] == 0
    assert result["first_prize_rollover"] == 100_000.0


def test_second_category_rolls_into_third():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(second=0),
    )

    assert result["pools"]["second"] == 0
    assert result["pools"]["third"] == 30_000.0


def test_third_category_rolls_into_fourth():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(third=0),
    )

    assert result["pools"]["third"] == 0
    assert result["pools"]["fourth"] == 15_000.0


def test_second_and_third_roll_into_fourth():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(second=0, third=0),
    )

    assert result["pools"]["second"] == 0
    assert result["pools"]["third"] == 0
    assert result["pools"]["fourth"] == 35_000.0


def test_second_third_and_fourth_roll_into_next_first():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(first=0, second=0, third=0, fourth=0),
    )

    assert result["pools"]["first"] == 0
    assert result["pools"]["second"] == 0
    assert result["pools"]["third"] == 0
    assert result["pools"]["fourth"] == 0
    assert result["first_prize_rollover"] == 135_000.0


def test_fifth_category_does_not_roll_over():
    result = apply_category_rollovers(
        make_pools(),
        make_winners(fifth=0),
    )

    assert result["pools"]["fifth"] == 4.0


def test_invalid_negative_winner_count_raises_error():
    with pytest.raises(ValueError):
        apply_category_rollovers(
            make_pools(),
            make_winners(second=-1),
        )
