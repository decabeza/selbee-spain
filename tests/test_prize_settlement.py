"""
SELBEE SPAIN - Prize Settlement Integration Tests

Tests the interaction between category rollovers
and category prize equalization.
"""

import pytest

from selbee.mathematics.category_equalization import equalize_category_prizes
from selbee.mathematics.prize_rollover import apply_category_rollovers


def make_pools():
    return {
        "first": 100_000.0,
        "second": 20_000.0,
        "third": 10_000.0,
        "fourth": 5_000.0,
        "fifth": 4.0,
    }


def test_rollover_is_applied_before_category_equalization():
    pools = make_pools()

    winners = {
        "first": 1,
        "second": 0,
        "third": 100,
        "fourth": 1,
        "fifth": 1,
    }

    rollover_result = apply_category_rollovers(
        pools=pools,
        winners=winners,
    )

    assert rollover_result["pools"]["second"] == 0
    assert rollover_result["pools"]["third"] == 30_000.0
    assert rollover_result["first_prize_rollover"] == 0

    equalization_result = equalize_category_prizes(
        pools=rollover_result["pools"],
        winners=winners,
    )

    expected_shared_prize = 35_000.0 / 101

    assert equalization_result["payouts"]["third"] == pytest.approx(
        expected_shared_prize
    )
    assert equalization_result["payouts"]["fourth"] == pytest.approx(
        expected_shared_prize
    )


def test_first_category_rollover_is_separated_from_current_draw():
    pools = make_pools()

    winners = {
        "first": 0,
        "second": 1,
        "third": 1,
        "fourth": 1,
        "fifth": 1,
    }

    rollover_result = apply_category_rollovers(
        pools=pools,
        winners=winners,
    )

    assert rollover_result["first_prize_rollover"] == 100_000.0
    assert rollover_result["pools"]["first"] == 0

    equalization_result = equalize_category_prizes(
        pools=rollover_result["pools"],
        winners=winners,
    )

    assert "first" not in equalization_result["payouts"]
    assert "second" in equalization_result["payouts"]
