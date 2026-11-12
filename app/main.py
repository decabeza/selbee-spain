"""
SELBEE SPAIN - Bonoloto Research Dashboard

First experimental interface for Bonoloto EV analysis.
"""

import streamlit as st

from selbee.games.bonoloto import (
    calculate_category_probabilities,
    probability_of_any_prize,
)
from selbee.games.bonoloto_ev import estimate_ev_per_line


st.set_page_config(
    page_title="SELBEE SPAIN",
    page_icon="📊",
    layout="wide",
)

st.title("SELBEE SPAIN")
st.caption("Quantitative research into Spanish lottery games")

st.warning(
    "Experimental model: this version does not yet incorporate "
    "category rollovers or prize equalization into the EV calculation. "
    "Results are indicative, pre-tax estimates, not verified opportunities."
)

st.header("Bonoloto — Scenario analysis")

st.sidebar.header("Draw parameters")

revenue_eur = st.sidebar.number_input(
    "Estimated draw revenue (€)",
    min_value=1.0,
    value=1_000_000.0,
    step=50_000.0,
)

first_prize_pool_eur = st.sidebar.number_input(
    "First category prize pool (€)",
    min_value=0.0,
    value=500_000.0,
    step=25_000.0,
)

other_entries = st.sidebar.number_input(
    "Other participating lines",
    min_value=0,
    value=2_000_000,
    step=100_000,
)

st.subheader("Mathematical probabilities")

probabilities = calculate_category_probabilities()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Jackpot probability",
    f"1 in {1 / probabilities['first']:,.0f}",
)

col2.metric(
    "Any number-based prize",
    f"{(1 - probabilities['no_number_prize']) * 100:.4f}%",
)

col3.metric(
    "Any prize including reintegro",
    f"{probability_of_any_prize() * 100:.4f}%",
)

st.divider()

st.subheader("Expected value analysis")

try:
    result = estimate_ev_per_line(
        revenue_eur=revenue_eur,
        first_prize_pool_eur=first_prize_pool_eur,
        other_entries=other_entries,
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Expected value per line",
        f"{result['ev_per_line']:+.4f} €",
    )

    metric2.metric(
        "Expected ROI",
        f"{result['roi_percent']:+.2f}%",
    )

    metric3.metric(
        "Expected gross payout",
        f"{result['expected_gross_payout']:.4f} €",
    )

    st.subheader("Expected payout by category")

    category_labels = {
        "first": "First category — 6 matches",
        "second": "Second category — 5 + complementary",
        "third": "Third category — 5 matches",
        "fourth": "Fourth category — 4 matches",
    }

    for category, label in category_labels.items():
        payout = result["expected_category_payouts"][category]
        st.write(f"**{label}:** {payout:.6f} €")

    st.write(
        f"**Fifth category — 3 matches:** "
        f"{result['expected_fifth_payout']:.6f} €"
    )

    st.write(
        f"**Reintegro (modelled per line):** "
        f"{result['expected_reintegro_payout']:.6f} €"
    )

    st.divider()

    st.subheader("Scenario inputs")
    st.write(f"Draw revenue: {revenue_eur:,.2f} €")
    st.write(f"First category pool: {first_prize_pool_eur:,.2f} €")
    st.write(f"Other participating lines: {other_entries:,}")
    st.write(f"Cost per line: {result['stake_eur']:.2f} €")

except (ValueError, TypeError) as error:
    st.error(f"Unable to calculate this scenario: {error}")

st.divider()

st.caption(
    "SELBEE SPAIN | Research prototype | "
    "All monetary estimates are pre-tax."
)
