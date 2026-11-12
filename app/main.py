
"""
SELBEE SPAIN - Bonoloto Research Dashboard

Historical draw database and experimental EV analysis.
"""
import json
from collections import Counter

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from selbee.games.bonoloto import (
    calculate_category_probabilities,
    probability_of_any_prize,
)
from selbee.games.bonoloto_ev import estimate_ev_per_line


DATABASE_PATH = Path("data/processed/selbee.db")


st.set_page_config(
    page_title="SELBEE SPAIN",
    page_icon="📊",
    layout="wide",
)

st.title("SELBEE SPAIN")
st.caption("Quantitative research into Spanish lottery games")


# ---------------------------------------------------------
# Historical database
# ---------------------------------------------------------

st.header("Historical database")

if DATABASE_PATH.exists():

    with sqlite3.connect(DATABASE_PATH) as connection:

        draws = pd.read_sql_query(
            """
            SELECT
                draw_id,
                draw_date,
                main_numbers,
                complementary,
                reintegro,
                entries,
                revenue_eur,
                prize_fund_eur,
                jackpot_rollover_eur
            FROM draws
            ORDER BY draw_date DESC
            """,
            connection,
        )

    if not draws.empty:

        total_draws = len(draws)
        total_revenue = draws["revenue_eur"].sum()
        average_revenue = draws["revenue_eur"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("Stored draws", f"{total_draws:,}")
        col2.metric("Total historical revenue", f"{total_revenue:,.2f} €")
        col3.metric("Average revenue per draw", f"{average_revenue:,.2f} €")

        st.subheader("Draw history")

        st.dataframe(
            draws,
            use_container_width=True,
            hide_index=True,
        )

        selected_draw_id = st.selectbox(
            "Select a draw to inspect its prize categories",
            draws["draw_id"].tolist(),
        )

        with sqlite3.connect(DATABASE_PATH) as connection:

            categories = pd.read_sql_query(
                """
                SELECT
                    category,
                    description,
                    winners,
                    prize_per_winner
                FROM prize_categories
                WHERE draw_id = ?
                ORDER BY category
                """,
                connection,
                params=(selected_draw_id,),
            )

        st.subheader(f"Prize categories — Draw {selected_draw_id}")

        st.dataframe(
            categories,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info("The database exists but contains no draws.")

else:
    st.info("No historical database found. Import Bonoloto JSON files first.")


st.divider()

# ---------------------------------------------------------
# Historical combination analysis
# ---------------------------------------------------------

st.divider()

st.header("Historical combination analysis")

if DATABASE_PATH.exists():

    with sqlite3.connect(DATABASE_PATH) as connection:
        historical = pd.read_sql_query(
            """
            SELECT
                draw_date,
                main_numbers,
                complementary,
                reintegro,
                source
            FROM historical_combinations
            ORDER BY draw_date
            """,
            connection,
        )

    if not historical.empty:

        total_combinations = len(historical)
        missing_reintegro = historical["reintegro"].isna().sum()
        available_reintegro = total_combinations - missing_reintegro

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Historical combinations",
            f"{total_combinations:,}",
        )

        col2.metric(
            "First recorded draw",
            historical["draw_date"].min(),
        )

        col3.metric(
            "Last recorded draw",
            historical["draw_date"].max(),
        )

        col4.metric(
            "Available reintegros",
            f"{available_reintegro:,} / {total_combinations:,}",
        )

        st.caption(
            f"{missing_reintegro:,} historical records have no "
            "reintegro information."
        )

        # Main number frequencies

        st.subheader("Main number frequency")

        main_numbers = Counter()

        for combination in historical["main_numbers"]:
            main_numbers.update(json.loads(combination))

        main_frequency = pd.DataFrame({
            "Number": range(1, 50),
            "Occurrences": [
                main_numbers[number] for number in range(1, 50)
            ],
        }).set_index("Number")

        st.bar_chart(main_frequency)

        st.dataframe(
            main_frequency.sort_values(
                "Occurrences",
                ascending=False,
            ),
            use_container_width=True,
        )

        # Complementary number frequencies

        st.subheader("Complementary number frequency")

        complementary_frequency = (
            historical["complementary"]
            .value_counts()
            .reindex(range(1, 50), fill_value=0)
            .sort_index()
        )

        st.bar_chart(
            complementary_frequency.rename("Occurrences")
        )

        # Reintegro frequencies

        st.subheader("Reintegro frequency")

        reintegro_frequency = (
            historical["reintegro"]
            .dropna()
            .astype(int)
            .value_counts()
            .reindex(range(10), fill_value=0)
            .sort_index()
        )

        st.bar_chart(
            reintegro_frequency.rename("Occurrences")
        )

        st.caption(
            "Historical frequencies are descriptive statistics. "
            "They do not predict future lottery outcomes."
        )

    else:
        st.info("No historical combinations available.")

else:
    st.info("Historical database not found.")


# ---------------------------------------------------------
# Experimental EV scenario analyzer
# ---------------------------------------------------------

st.header("Bonoloto — Scenario analysis")

st.warning(
    "Experimental model: category rollovers and prize equalization "
    "are not yet incorporated into this EV calculation. "
    "Results are indicative and pre-tax."
)

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
