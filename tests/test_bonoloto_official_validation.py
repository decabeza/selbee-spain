import pytest

from selbee.games.bonoloto_ev import calculate_prize_pools


def test_official_bonoloto_draw_2026_11_03():
    """
    Validate prize allocation against SELAE's official
    Bonoloto draw published on 3 November 2026.
    """

    pools = calculate_prize_pools(
        revenue_eur=2_621_100.50,
        expected_fifth_winners=92_320,
        first_prize_pool_eur=1_800_000,
    )

    # Second category: 20% of the remaining fund.
    assert pools["second"] == pytest.approx(
        162_043.045
    )

    # Third category: 10% of the remaining fund.
    assert pools["third"] / 97 == pytest.approx(
        835.27, abs=0.01
    )

    # Fourth category: 15% of the remaining fund.
    assert pools["fourth"] / 5_076 == pytest.approx(
        23.94, abs=0.01
    )

    # Fifth category: fixed prize of 4 EUR.
    assert pools["fifth_fixed_payout"] == pytest.approx(
        369_280
    )

    # Current first-category allocation.
    assert pools["current_first_allocation"] == pytest.approx(
        445_618.37375
    )
