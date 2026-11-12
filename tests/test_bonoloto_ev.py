
import pytest

from selbee.games.bonoloto_ev import (
    calculate_prize_pools,
    estimate_ev_per_line,
)


def test_prize_pool_allocation():
    pools = calculate_prize_pools(
        revenue_eur=10_000,
        expected_fifth_winners=1_000,
        first_prize_pool_eur=5_000,
    )

    assert pools["first"] == pytest.approx(5_000)
    assert pools["second"] == pytest.approx(100)
    assert pools["third"] == pytest.approx(50)
    assert pools["fourth"] == pytest.approx(75)


def test_fifth_category_fixed_payout():
    pools = calculate_prize_pools(
        revenue_eur=10_000,
        expected_fifth_winners=1_000,
        first_prize_pool_eur=5_000,
    )

    assert pools["fifth_fixed_payout"] == pytest.approx(4_000)


def test_reintegro_fund():
    pools = calculate_prize_pools(
        revenue_eur=10_000,
        expected_fifth_winners=1_000,
        first_prize_pool_eur=5_000,
    )

    assert pools["reintegro_fund"] == pytest.approx(1_000)


def test_negative_revenue_is_invalid():
    with pytest.raises(ValueError):
        calculate_prize_pools(-100, 10, 1_000)


def test_excessive_fifth_category_payout_is_invalid():
    with pytest.raises(ValueError):
        calculate_prize_pools(
            revenue_eur=100,
            expected_fifth_winners=100,
            first_prize_pool_eur=1_000,
        )


def test_ev_result_contains_required_fields():
    result = estimate_ev_per_line(
        revenue_eur=100_000,
        first_prize_pool_eur=500_000,
        other_entries=199_999,
    )

    assert "ev_per_line" in result
    assert "roi_percent" in result
    assert "expected_gross_payout" in result
    assert "expected_category_payouts" in result


def test_ev_calculation_is_consistent():
    result = estimate_ev_per_line(
        revenue_eur=100_000,
        first_prize_pool_eur=500_000,
        other_entries=199_999,
    )

    assert result["ev_per_line"] == pytest.approx(
        result["expected_gross_payout"] - result["stake_eur"]
    )

    assert result["roi_percent"] == pytest.approx(
        result["ev_per_line"] / result["stake_eur"] * 100
    )


def test_reintegro_expected_payout():
    result = estimate_ev_per_line(
        revenue_eur=100_000,
        first_prize_pool_eur=500_000,
        other_entries=199_999,
    )

    assert result["expected_reintegro_payout"] == pytest.approx(0.05)


def test_negative_other_entries_are_invalid():
    with pytest.raises(ValueError):
        estimate_ev_per_line(
            revenue_eur=100_000,
            first_prize_pool_eur=500_000,
            other_entries=-1,
        )


def test_zero_revenue_is_invalid():
    with pytest.raises(ValueError):
        estimate_ev_per_line(
            revenue_eur=0,
            first_prize_pool_eur=500_000,
            other_entries=100,
        )
