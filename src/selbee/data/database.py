"""
SELBEE SPAIN - Database Engine

SQLite storage for normalized Bonoloto draw data.
"""

import json
import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("data/processed/selbee.db")


def initialize_database(
    db_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Create the database and its tables if they do not exist."""

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draws (
                draw_id TEXT PRIMARY KEY,
                draw_date TEXT NOT NULL,
                game_id TEXT NOT NULL,
                main_numbers TEXT NOT NULL,
                complementary INTEGER NOT NULL,
                reintegro INTEGER NOT NULL,
                entries INTEGER NOT NULL,
                revenue_eur REAL NOT NULL,
                prize_fund_eur REAL NOT NULL,
                jackpot_rollover_eur REAL NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS prize_categories (
                draw_id TEXT NOT NULL,
                category INTEGER NOT NULL,
                description TEXT NOT NULL,
                prize_per_winner REAL NOT NULL,
                winners INTEGER NOT NULL,
                PRIMARY KEY (draw_id, category),
                FOREIGN KEY (draw_id)
                    REFERENCES draws(draw_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_draws_date
            ON draws(draw_date)
            """
        )


def save_draw(
    draw: dict,
    db_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """
    Save one normalized draw and its prize categories.

    Existing records are updated using the official draw ID.
    """

    initialize_database(db_path)

    combination = draw["combination"]

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            INSERT INTO draws (
                draw_id,
                draw_date,
                game_id,
                main_numbers,
                complementary,
                reintegro,
                entries,
                revenue_eur,
                prize_fund_eur,
                jackpot_rollover_eur
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(draw_id) DO UPDATE SET
                draw_date = excluded.draw_date,
                game_id = excluded.game_id,
                main_numbers = excluded.main_numbers,
                complementary = excluded.complementary,
                reintegro = excluded.reintegro,
                entries = excluded.entries,
                revenue_eur = excluded.revenue_eur,
                prize_fund_eur = excluded.prize_fund_eur,
                jackpot_rollover_eur = excluded.jackpot_rollover_eur
            """,
            (
                draw["draw_id"],
                draw["date"].isoformat(),
                draw["game_id"],
                json.dumps(combination["numbers"]),
                combination["complementary"],
                combination["reintegro"],
                draw["entries"],
                draw["revenue_eur"],
                draw["prize_fund_eur"],
                draw["jackpot_rollover_eur"],
            ),
        )

        connection.execute(
            "DELETE FROM prize_categories WHERE draw_id = ?",
            (draw["draw_id"],),
        )

        connection.executemany(
            """
            INSERT INTO prize_categories (
                draw_id,
                category,
                description,
                prize_per_winner,
                winners
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    draw["draw_id"],
                    category,
                    result["description"],
                    result["prize_per_winner"],
                    result["winners"],
                )
                for category, result in draw["categories"].items()
            ],
        )


def count_draws(
    db_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Return the number of stored draws."""

    if not Path(db_path).exists():
        return 0

    with sqlite3.connect(db_path) as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM draws"
        ).fetchone()

    return result[0]
