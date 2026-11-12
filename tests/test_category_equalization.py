import pytest

from selbee.mathematics.category_equalization import (
    equalize_category_prizes,
)


def make_winners(first=1, second=1, third=1, fourth=1, fifth=1):
    return {
        "first": first,
        "second": second,
        "third": third,
        "fourth": fourth,
        "fifth": fifth,
    }


def test_no_equalization_needed():
    pools = {
        "first": 100_000,
        "second": 20_000,
        "third": 5_000,
        "fourth": 1_000,
        "fifth": 4,
    }

    result = equalize_category_prizes(pools, make_winners())

    assert result["payouts"]["first"] == pytest.approx(100_000)
    assert result["payouts"]["second"] == pytest.approx(20_000)
    assert result["merged_groups"] == [
        ["first"], ["second"], ["third"], ["fourth"], ["fifth"]
    ]


def test_fourth_category_exceeds_third():
    pools = {
        "first": 100_000,
        "second": 20_000,
        "third": 500,
        "fourth": 1_000,
        "fifth": 4,
    }

    result = equalize_category_prizes(pools, make_winners())

    assert result["payouts"]["third"] == pytest.approx(750)
    assert result["payouts"]["fourth"] == pytest.approx(750)


def test_equalization_cascades():
    pools = {
        "first": 100,
        "second": 200,
        "third": 300,
        "fourth": 400,
        "fifth": 500,
    }

    result = equalize_category_prizes(pools, make_winners())

    for category in ("first", "second", "third", "fourth", "fifth"):
        assert result["payouts"][category] == pytest.approx(300)

    assert result["merged_groups"] == [
        ["first", "second", "third", "fourth", "fifth"]
    ]


def test_multiple_winners_are_considered():
    pools = {
        "first": 100_000,
        "second": 20_000,
        "third": 10_000,
        "fourth": 100,
        "fifth": 4,
    }

    winners = make_winners(second=1, third=100)

    result = equalize_category_prizes(pools, winners)

    assert result["payouts"]["second"] == pytest.approx(20_000)
    assert result["payouts"]["third"] == pytest.approx(100)
    assert result["payouts"]["fourth"] == pytest.approx(100)


def test_zero_winners_with_remaining_pool_is_invalid():
    pools = {
        "first": 100_000,
        "second": 20_000,
        "third": 5_000,
        "fourth": 1_000,
        "fifth": 4,
    }

    winners = make_winners(second=0)

    with pytest.raises(ValueError):
        equalize_category_prizes(pools, winners)


def test_zero_winners_with_zero_pool_is_allowed():
    pools = {
        "first": 100_000,
        "second": 0,
        "third": 5_000,
        "fourth": 1_000,
        "fifth": 4,
    }

    winners = make_winners(second=0)

    result = equalize_category_prizes(pools, winners)

    assert "second" not in result["payouts"]


def test_negative_pool_is_invalid():
    pools = {
        "first": 100_000,
        "second": -1,
        "third": 5_000,
        "fourth": 1_000,
        "fifth": 4,
    }

    with pytest.raises(ValueError):
        equalize_category_prizes(pools, make_winners())


def test_negative_winners_are_invalid():
    pools = {
        "first": 100_000,
        "second": 20_000,
        "third": 5_000,
        "fourth": 1_000,
        "fifth": 4,
    }

    with pytest.raises(ValueError):
        equalize_category_prizes(
            pools,
            make_winners(second=-1),
        )
